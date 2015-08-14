"""
prompt.py

Copyright 2007 Andres Riancho

This file is part of w3af, http://w3af.org/ .

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
"""
import os
import gtk
import gobject
import pango

from w3af.core.ui.gui import GUI_DATA_PATH
from w3af.core.ui.gui.output.message_consumer import MessageConsumer


class PromptView(gtk.TextView, MessageConsumer):
    """Creates a prompt for user interaction.

    The user input is passed to the registered function, the result
    of this is shown under the prompt.

    :param procfunc: the function to process the user input

    :author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    """
    def __init__(self, prompt_text, procfunc):
        gtk.TextView.__init__(self)
        MessageConsumer.__init__(self)

        self.prompt_text = prompt_text
        self.procfunc = procfunc
        
        self.set_wrap_mode(gtk.WRAP_CHAR)

        # keys
        self.keys = {
            gtk.gdk.keyval_from_name("Return"): self._key_enter,
            gtk.gdk.keyval_from_name("KP_Enter"): self._key_enter,
            gtk.gdk.keyval_from_name("Up"): self._key_up,
            gtk.gdk.keyval_from_name("Down"): self._key_down,
            gtk.gdk.keyval_from_name("BackSpace"): self._key_backspace,
            gtk.gdk.keyval_from_name("Control_L"): lambda: False,
            gtk.gdk.keyval_from_name("Control_R"): lambda: False,
        }

        # mono spaced font looks more like a terminal to me =)
        # and works better with the output of some unix commands
        # that are run remotely and displayed in the console
        pangoFont = pango.FontDescription('Courier 11')
        self.modify_font(pangoFont)

        # Buttons, buffers and stuff:
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

    def handle_message(self, msg):
        """
        This method is called from gobject.timeout_add and will add messages
        from self.message to the textbuffer.

        :return: True to keep running
        """
        super(PromptView, self).handle_message(msg)
        
        if msg.get_type() == 'console':
            # Handling new lines
            text = msg.get_msg()
            if msg.get_new_line():
                text += '\n'
    
            self.insert_into_textbuffer(text)
            yield True

    def insert_into_textbuffer(self, text):
        """
        Insert a text into the text buffer, taking care of \r, \n, self.user_started.

        :param text: The text to insert into the textbuffer
        :return: None
        """
        iterl = self.textbuffer.get_end_iter()
        # Handling carriage returns (special case for some apps)
        if text.startswith('\r'):
            # overwrite the old text:
            # 1: delete it
            # 2: write

            # Start deleting here
            iterl.backward_line()
            delete_start = iterl

            # End deleting here
            text = text[1:]
            text_length = len(text)
            iterini = self.textbuffer.get_start_iter()
            old_text = self.textbuffer.get_text(iterini, delete_start)
            old_text_length = len(old_text)
            delete_end = self.textbuffer.get_iter_at_offset(
                text_length + old_text_length)

            # Delete
            self.textbuffer.delete(iterl, delete_end)

        self.textbuffer.insert(iterl, text)
        self.scroll_to_mark(self.textbuffer.get_insert(), 0)

        # This is for the user entered command handling
        iterl = self.textbuffer.get_end_iter()
        self.textbuffer.place_cursor(iterl)
        self.cursorLimit = self.textbuffer.get_property("cursor-position")
        self.user_started = self.textbuffer.create_mark(
            "user-input", iterl, True)

    def get_text(self):
        """Returns the textbuffer content."""
        iterini = self.textbuffer.get_start_iter()
        iterend = self.textbuffer.get_end_iter()
        text = self.textbuffer.get_text(iterini, iterend)
        return text

    def _button_press(self, widg, event):
        """The mouse button is down."""
        if self.cursorPosition is None:
            self.cursorPosition = self.textbuffer.get_property(
                "cursor-position")
        return False

    def _button_release(self, widg, event):
        """The mouse button is released."""
        return False

    def _key_up(self):
        """The key UP was pressed."""
        # Do we have previous lines?
        if not self.all_lines:
            return True

        self.historyCount -= 1
        if self.historyCount < 0:
            self.historyCount = 0
        line = self.all_lines[self.historyCount]
        self._showHistory(line)
        return True

    def _key_down(self):
        """The key DOWN was pressed."""

        # Do we have previous lines?
        if not self.all_lines:
            return True

        self.historyCount += 1
        if self.historyCount >= len(self.all_lines):
            self.historyCount = len(self.all_lines) - 1
        line = self.all_lines[self.historyCount]
        self._showHistory(line)
        return True

    def _showHistory(self, text):
        """Handles the history of commands."""
        # delete all the line content
        iterini = self.textbuffer.get_iter_at_offset(self.cursorLimit)
        iterend = self.textbuffer.get_end_iter()
        self.textbuffer.delete(iterini, iterend)

        # insert the text
        iterl = self.textbuffer.get_end_iter()
        self.textbuffer.insert(iterl, text)
        self.scroll_to_mark(self.textbuffer.get_insert(), 0)

    def _key_backspace(self):
        """The key BACKSPACE was pressed."""
        cursor_pos = self.textbuffer.get_property("cursor-position")
        if cursor_pos <= self.cursorLimit:
            return True
        return False

    def _key_enter(self):
        """The user pressed Return."""
        textbuffer = self.textbuffer
        cursor_pos = textbuffer.get_property("cursor-position")
        iter_end = textbuffer.get_end_iter()
        if cursor_pos != iter_end.get_offset():
            return True

        textbuffer.insert(iter_end, "\n")

        # In some strange cases `self.user_started` can be None causing
        # a TypeError raised by get_iter_at_mark(). This hack is to prevent it.
        if not self.user_started:
            self.user_started = textbuffer.create_mark("user-input",
                                                       iter_end, True)

        iter_start = textbuffer.get_iter_at_mark(self.user_started)
        text = textbuffer.get_text(iter_start, iter_end)
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
        """Process the user input."""
        result = self.procfunc(text)
        if result is not None and isinstance(result, basestring):
            iterl = self.textbuffer.get_end_iter()
            self.textbuffer.insert(iterl, result + "\n")
            self.scroll_to_mark(self.textbuffer.get_insert(), 0)

        self._prompt()

    def _prompt(self):
        """
        Show the prompt-
        """
        iterl = self.textbuffer.get_end_iter()
        self.textbuffer.insert(iterl, self.prompt_text + "> ")
        self.scroll_to_mark(self.textbuffer.get_insert(), 0)
        
        iterl = self.textbuffer.get_end_iter()
        self.textbuffer.place_cursor(iterl)
        self.cursorLimit = self.textbuffer.get_property("cursor-position")
        self.user_started = self.textbuffer.create_mark("user-input",
                                                        iterl, True)

    def _key(self, widg, event):
        """Separates the special keys from the other."""
        # analyze which key was pressed
        if event.keyval in self.keys:
            func = self.keys[event.keyval]
            return func()

        # reset the cursor after moving it with the mouse
        if self.cursorPosition is not None:
            # special: don't reset for ctrl-C, as we want to copy the selected stuff
            if event.state & gtk.gdk.CONTROL_MASK and event.keyval == gtk.gdk.keyval_from_name("c"):
                return False
            iterl = self.textbuffer.get_iter_at_offset(self.cursorPosition)
            self.textbuffer.place_cursor(iterl)
            self.cursorPosition = None

#        print gtk.gdk.keyval_name(event.keyval)
        return False


class PromptDialog(gtk.Dialog):
    """Puts the Prompt widget inside a Dialog.

    :param title: the title of the window.
    :param procfunc: the function to process the user input

    :author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    """
    def __init__(self, title, prompt_text, procfunc):
        super(PromptDialog, self).__init__(title, None, gtk.DIALOG_MODAL, ())
        self.set_icon_from_file(os.path.join(GUI_DATA_PATH, 'shell.png'))

        # the toolbar
        box = gtk.HBox()
        but = gtk.Button(stock=gtk.STOCK_SAVE)
        but.set_property('image-position', gtk.POS_TOP)
        but.connect('clicked', self._save)
        box.pack_start(but, False, False)
        self.vbox.pack_start(box, False, False)
        self.vbox.pack_start(gtk.HSeparator(), False, False, padding=5)
        # FIXME: Add help here

        # the prompt in an scrolled window
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.prompt = PromptView(prompt_text, procfunc)
        sw.add(self.prompt)
        self.vbox.pack_start(sw)

        self.resize(800, 300)
        self.show_all()

    def _save(self, widg):
        """Saves the content to a file."""
        text = self.prompt.get_text()
        dlg = gtk.FileChooserDialog(title=_('Choose output file...'),
                                    action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                    buttons=(gtk.STOCK_CANCEL,
                                             gtk.RESPONSE_CANCEL,
                                             gtk.STOCK_SAVE,
                                             gtk.RESPONSE_OK))
        resp = dlg.run()
        fname = dlg.get_filename()
        dlg.destroy()
        if resp == gtk.RESPONSE_OK and fname is not None:
            fh = open(fname, 'w')
            fh.write(text)
            fh.close()
        return


if __name__ == "__main__":
    def proc_func(x):
        x = x.decode("utf8")
        return x[::-1]

    class Test(object):
        def __init__(self):
            # create a new window
            self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
            self.window.connect("destroy", gtk.main_quit)
            self.window.resize(100, 50)

            # button
            button = gtk.Button("Prompt")
            button.connect("clicked", self.prompt)
            button.show()
            self.window.add(button)

            self.window.show()
            gtk.main()

        def prompt(self, widg):
            prompt = PromptDialog("Just a test", "test", proc_func)

    Test()
