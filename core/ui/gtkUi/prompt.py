'''
prompt.py

Copyright 2007 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
'''

import pygtk
pygtk.require('2.0')
import gtk, gobject

class PromptView(gtk.TextView):
    '''Creates a prompt for user interaction.

    The user input is passed to the registered function, the result
    of this is shown under the prompt.
    
    @param procfunc: the function to process the user input

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, promptText, procfunc):
        self.promptText = promptText
        self.procfunc = procfunc
        super(PromptView,self).__init__()

        # keys
        self.keys = {
            gtk.gdk.keyval_from_name("Return"): self._key_enter,
            gtk.gdk.keyval_from_name("Up"): self._key_up,
            gtk.gdk.keyval_from_name("Down"): self._key_down,
            gtk.gdk.keyval_from_name("BackSpace"): self._key_backspace,
        }

        self.textbuffer = self.get_buffer()
        self.user_started = None
        self.all_lines = []
        self.cursorPosInitLine = 0

        self.connect("key-press-event", self._key)
        self.show()
        gobject.idle_add(self._prompt)

        # FIXME: que el mouse no pueda dejar el cursor en cualquier lado
        # FIXME: poner un toolbar, un boton save ahi, y que grabe a disco
        # FIXME: que haga wrap cuando escribimos mucho

    def _key_up(self):
        print "boo"
        # FIXME implementar esto!

    def _key_down(self):
        print "boo"
        # FIXME implementar esto!

    def _key_backspace(self):
        cursor_pos = self.textbuffer.get_property("cursor-position")
        if cursor_pos <= self.cursorLimit:
            return True
        return False

    def _key_enter(self):
        '''The user pressed Return.'''
        cursor_pos = self.textbuffer.get_property("cursor-position")
        iter_end = self.textbuffer.get_end_iter()
        if cursor_pos != iter_end.get_offset():
            return

        self.textbuffer.insert(iter_end, "\n")
        iter_start = self.textbuffer.get_iter_at_mark(self.user_started)
        text = self.textbuffer.get_text(iter_start, iter_end)
        self.user_started = None
        text = text.strip()
        if text:
            self._proc(text)
        else:
            self._prompt()
        return True

    def _proc(self, text):
        '''Process the user input.'''
        result = self.procfunc(text)
        if result != None:
            iter = self.textbuffer.get_end_iter()
            self.textbuffer.insert(iter, result+"\n")
        self._prompt()
        # FIXME: que ajuste el scrollbar para abajo de todo
        
    def _prompt(self):
        '''Show the prompt.'''
        iter = self.textbuffer.get_end_iter()
        self.textbuffer.insert(iter, self.promptText + "> ")
        iter = self.textbuffer.get_end_iter()
        self.textbuffer.place_cursor(iter)
        self.cursorLimit = self.textbuffer.get_property("cursor-position")
        self.user_started = self.textbuffer.create_mark("user-input", iter, True)

    def _key(self, widg, event):
        '''Separates the special keys from the other.'''
        if event.keyval in self.keys:
            func = self.keys[event.keyval]
            return func()
        print gtk.gdk.keyval_name(event.keyval)
        return False

class PromptDialog(gtk.Dialog):
    '''Puts the Prompt widget inside a Dialog.
    
    @param title: the title of the window.
    @param procfunc: the function to process the user input

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, title, promptText, procfunc):
        super(PromptDialog,self).__init__(title, None, gtk.DIALOG_MODAL, ())

        # A vertical box that contains the prompt...
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.show()
        
        # the prompt itself
        prompt = PromptView(promptText, procfunc)
        prompt.show()
        
        sw.add(prompt)
        self.vbox.pack_start(sw)

        self.resize(600,300)
        self.show()


if __name__ == "__main__":

    def procFunc(x):
        return x[::-1]

    class Test(object):
        def __init__(self):
            # create a new window
            self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
            self.window.connect("destroy", gtk.main_quit)
            self.window.resize(100,50)

            # button
            button = gtk.Button("Prompt")
            button.connect("clicked", self.prompt)
            button.show()
            self.window.add(button)
    
            self.window.show()
            gtk.main()

        def prompt(self, widg):
            prompt = PromptDialog("Just a test", "test", procFunc)

    Test()
