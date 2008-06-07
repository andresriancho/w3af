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

import pygtk, gtk, gobject

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
        self.set_wrap_mode(gtk.WRAP_CHAR)

        # keys
        self.keys = {
            gtk.gdk.keyval_from_name("Return"): self._key_enter,
            gtk.gdk.keyval_from_name("KP_Enter"): self._key_enter,
            gtk.gdk.keyval_from_name("Up"): self._key_up,
            gtk.gdk.keyval_from_name("Down"): self._key_down,
            gtk.gdk.keyval_from_name("BackSpace"): self._key_backspace,
            gtk.gdk.keyval_from_name("Control_L"): lambda:False,
            gtk.gdk.keyval_from_name("Control_R"): lambda:False,
        }

        self.textbuffer = self.get_buffer()
        self.user_started = None
        self.all_lines = []
        self.cursorPosition = None
        self.historyCount = 0

        self.connect("key-press-event", self._key)
        self.connect("button-press-event", self._button_press)
        self.connect("button-release-event", self._button_release)
        self.show()
        gobject.idle_add(self._prompt)
        gobject.idle_add(self.grab_focus)

    def getText(self):
        iterini = self.textbuffer.get_start_iter()
        iterend = self.textbuffer.get_end_iter()
        text = self.textbuffer.get_text(iterini, iterend)
        return text

    def _button_press(self, widg, event):
        if self.cursorPosition is None:
            self.cursorPosition = self.textbuffer.get_property("cursor-position")
        return False

    def _button_release(self, widg, event):
        return False

    def _key_up(self):
        self.historyCount -= 1
        if self.historyCount < 0:
            self.historyCount = 0
        line = self.all_lines[self.historyCount]
        self._showHistory(line)
        return True

    def _key_down(self):
        self.historyCount += 1
        if self.historyCount >= len(self.all_lines):
            self.historyCount = len(self.all_lines) - 1
        line = self.all_lines[self.historyCount]
        self._showHistory(line)
        return True

    def _showHistory(self, text):
        # delete all the line content
        iterini = self.textbuffer.get_iter_at_offset(self.cursorLimit)
        iterend = self.textbuffer.get_end_iter()
        self.textbuffer.delete(iterini, iterend)

        # insert the text
        iter = self.textbuffer.get_end_iter()
        self.textbuffer.insert(iter, text)
        self.scroll_to_mark(self.textbuffer.get_insert(), 0)

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
            return True

        self.textbuffer.insert(iter_end, "\n")
        iter_start = self.textbuffer.get_iter_at_mark(self.user_started)
        text = self.textbuffer.get_text(iter_start, iter_end)
        self.user_started = None
        text = text.strip()
        if text:
            self.all_lines.append(text)
            self._proc(text)
        else:
            self._prompt()
        self.historyCount = len(self.all_lines)
        return True

    def _proc(self, text):
        '''Process the user input.'''
        result = self.procfunc(text)
        if result != None:
            iter = self.textbuffer.get_end_iter()
            self.textbuffer.insert(iter, result+"\n")
            self.scroll_to_mark(self.textbuffer.get_insert(), 0)
        self._prompt()
        
    def _prompt(self):
        '''Show the prompt.'''
        iter = self.textbuffer.get_end_iter()
        self.textbuffer.insert(iter, self.promptText + "> ")
        self.scroll_to_mark(self.textbuffer.get_insert(), 0)
        iter = self.textbuffer.get_end_iter()
        self.textbuffer.place_cursor(iter)
        self.cursorLimit = self.textbuffer.get_property("cursor-position")
        self.user_started = self.textbuffer.create_mark("user-input", iter, True)

    def _key(self, widg, event):
        '''Separates the special keys from the other.'''
        # analyze which key was pressed
        if event.keyval in self.keys:
            func = self.keys[event.keyval]
            return func()

        # reset the cursor after moving it with the mouse
        if self.cursorPosition is not None:
            # special: don't reset for ctrl-C, as we want to copy the selected stuff
            if event.state & gtk.gdk.CONTROL_MASK and event.keyval == gtk.gdk.keyval_from_name("c"):
                return False
            iter = self.textbuffer.get_iter_at_offset(self.cursorPosition)
            self.textbuffer.place_cursor(iter)
            self.cursorPosition = None

#        print gtk.gdk.keyval_name(event.keyval)
        return False


class PromptDialog(gtk.Dialog):
    '''Puts the Prompt widget inside a Dialog.
    
    @param title: the title of the window.
    @param procfunc: the function to process the user input

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, title, promptText, procfunc):
        super(PromptDialog,self).__init__(title, None, gtk.DIALOG_MODAL, ())

        # the toolbar
        box = gtk.HBox()
        but = gtk.Button(stock=gtk.STOCK_SAVE)
        but.set_property("image-position", gtk.POS_TOP)
        but.connect("clicked", self._save)
        box.pack_start(but, False, False)
        self.vbox.pack_start(box, False, False)
        self.vbox.pack_start(gtk.HSeparator(), False, False, padding=5)
        # FIXME: poner un HELP aca

        # the prompt in an scrolled window
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.prompt = PromptView(promptText, procfunc)
        sw.add(self.prompt)
        self.vbox.pack_start(sw)

        self.resize(600,300)
        self.show_all()

    def _save(self, widg):
        text = self.prompt.getText()
        dlg = gtk.FileChooserDialog(title="Choose a file...", action=gtk.FILE_CHOOSER_ACTION_OPEN,
                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        resp = dlg.run()
        fname = dlg.get_filename()
        dlg.destroy()
        if resp == gtk.RESPONSE_OK and fname is not None:
            fh = open(fname, "w")
            fh.write(text)
            fh.close()
        return

if __name__ == "__main__":

    def procFunc(x):
        x = x.decode("utf8")
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
