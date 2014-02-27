#!/usr/bin/env python

# This is a sample implementation of an editor.

import os
import pluginEditorDialogs
import gtk

from w3af import ROOT_PATH

BLOCK_SIZE = 2048
RESPONSE_FORWARD = 1


class EditWindow(gtk.Window):
    def __init__(self, quit_cb=None):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_size_request(470, 300)
        self.connect("delete_event", self.file_exit)
        self.quit_cb = quit_cb
        self.vbox = gtk.VBox()
        self.add(self.vbox)
        self.vbox.show()
        hdlbox = gtk.HandleBox()
        self.vbox.pack_start(hdlbox, expand=False)
        hdlbox.show()
        self.menubar, self.toolbar = self.create_menu()
        hdlbox.add(self.menubar)
        self.menubar.show()
        self.vbox.pack_start(self.toolbar, expand=False)
        self.scrolledwin = gtk.ScrolledWindow()
        self.scrolledwin.show()
        self.vbox.pack_start(self.scrolledwin)
        self.text = gtk.TextView()
        self.text.set_editable(True)
        self.scrolledwin.add(self.text)
        self.text.show()
        self.buffer = self.text.get_buffer()
        self.dirty = 0
        self.file_new()
        self.text.grab_focus()
        self.clipboard = gtk.Clipboard(selection='CLIPBOARD')
        self.dirname = None
        self.search_string = None
        self.last_search_iter = None
        return

    def load_file(self, fname):
        try:
            fd = open(fname)
            self.buffer.set_text('')
            buf = fd.read(BLOCK_SIZE)
            while buf != '':
                self.buffer.insert_at_cursor(buf)
                buf = fd.read(BLOCK_SIZE)
            self.text.queue_draw()
            self.set_title(os.path.basename(fname))
            self.fname = fname
            self.dirname = os.path.dirname(self.fname)
            self.buffer.set_modified(False)
            self.new = 0
        except:
            dlg = gtk.MessageDialog(self, gtk.DIALOG_DESTROY_WITH_PARENT,
                                    gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                                    _("Can't open ") + fname)
            resp = dlg.run()
            dlg.hide()
        return

    def create_menu(self):
        ui_string = """<ui>
        <menubar>
            <menu name='FileMenu' action='FileMenu'>
                <menuitem action='FileNew'/>
                <menuitem action='FileOpen'/>
                <menuitem action='FileSave'/>
                <menuitem action='FileSaveAs'/>
                <separator/>
                <menuitem action='FileExit'/>
            </menu>
            <menu name='EditMenu' action='EditMenu'>
                <menuitem action='EditCut'/>
                <menuitem action='EditCopy'/>
                <menuitem action='EditPaste'/>
                <menuitem action='EditClear'/>
                <separator/>
                <menuitem action='EditFind'/>
                <menuitem action='EditFindNext'/>
            </menu>
            <placeholder name='OtherMenus'/>
            <menu name='HelpMenu' action='HelpMenu'>
                <menuitem action='HelpAbout'/>
            </menu>
        </menubar>
        <toolbar>
          <toolitem action='FileNew'/>
          <toolitem action='FileOpen'/>
          <toolitem action='FileSave'/>
          <toolitem action='FileSaveAs'/>
                <separator/>
          <toolitem action='EditCut'/>
          <toolitem action='EditCopy'/>
          <toolitem action='EditPaste'/>
          <toolitem action='EditClear'/>
        </toolbar>
        </ui>
        """
        actions = [
            ('FileMenu', None, '_File'),
            ('FileNew', gtk.STOCK_NEW, None, None, None, self.file_new),
            ('FileOpen', gtk.STOCK_OPEN, None, None, None, self.file_open),
            ('FileSave', gtk.STOCK_SAVE, None, None, None, self.file_save),
            ('FileSaveAs', gtk.STOCK_SAVE_AS, None, None, None,
             self.file_saveas),
            ('FileExit', gtk.STOCK_QUIT, None, None, None, self.file_exit),
            ('EditMenu', None, '_Edit'),
            ('EditCut', gtk.STOCK_CUT, None, None, None, self.edit_cut),
            ('EditCopy', gtk.STOCK_COPY, None, None, None, self.edit_copy),
            ('EditPaste', gtk.STOCK_PASTE, None, None, None, self.edit_paste),
            ('EditClear', gtk.STOCK_REMOVE, _('C_lear'), None, None,
             self.edit_clear),
            ('EditFind', gtk.STOCK_FIND, None, None, None, self.edit_find),
            ('EditFindNext', None, _('Find _Next'), "F3", None,
             self.edit_find_next),
            ('HelpMenu', gtk.STOCK_HELP),
            ('HelpAbout', None, _('A_bout'), None, None, self.help_about),
        ]
        self.ag = gtk.ActionGroup('edit')
        self.ag.add_actions(actions)
        self.ui = gtk.UIManager()
        self.ui.insert_action_group(self.ag, 0)
        self.ui.add_ui_from_string(ui_string)
        self.add_accel_group(self.ui.get_accel_group())
        return (self.ui.get_widget('/menubar'), self.ui.get_widget('/toolbar'))

    def chk_save(self):
        if self.buffer.get_modified():
            dlg = gtk.Dialog('Unsaved File', self,
                             gtk.DIALOG_DESTROY_WITH_PARENT,
                             (gtk.STOCK_YES, gtk.RESPONSE_YES,
                              gtk.STOCK_NO, gtk.RESPONSE_NO,
                              gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
            lbl = gtk.Label((self.fname or _("Untitled")) +
                            _(" has not been saved\n") +
                            _("Do you want to save it?"))
            lbl.show()
            dlg.vbox.pack_start(lbl)
            ret = dlg.run()
            dlg.hide()
            if ret == gtk.RESPONSE_NO:
                return 0
            if ret == gtk.RESPONSE_YES:
                if self.file_save():
                    return 0
            return 1
        return 0

    def file_new(self, mi=None):
        if self.chk_save():
            return
        self.buffer.set_text('')
        self.buffer.set_modified(False)
        self.fname = None
        self.set_title(_("Untitled"))
        self.new = 1
        return

    def file_open(self, mi=None):
        if self.chk_save():
            return
        fname = pluginEditorDialogs.OpenFile(
            _('Open File'), self, self.dirname, self.fname)
        if not fname:
            return
        self.load_file(fname)
        return

    def file_save(self, mi=None):
        if self.new:
            return self.file_saveas()
        ret = False
        try:
            start, end = self.buffer.get_bounds()
            blockend = start.copy()
            fd = open(self.fname, "w")
            while blockend.forward_chars(BLOCK_SIZE):
                buf = self.buffer.get_text(start, blockend)
                fd.write(buf)
                start = blockend.copy()
            buf = self.buffer.get_text(start, blockend)
            fd.write(buf)
            fd.close()
            self.buffer.set_modified(False)
            ret = True
        except:
            dlg = gtk.MessageDialog(self, gtk.DIALOG_DESTROY_WITH_PARENT,
                                    gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                                    _("Error saving file ") + self.fname)
            resp = dlg.run()
            dlg.hide()
        return ret

    def file_saveas(self, mi=None):
        fname = pluginEditorDialogs.SaveFile(
            _('Save File As'), self, self.dirname,
            self.fname)
        if not fname:
            return False
        self.fname = fname
        self.dirname = os.path.dirname(self.fname)
        self.set_title(os.path.basename(fname))
        self.new = 0
        return self.file_save()

    def file_exit(self, mi=None, event=None):
        if self.chk_save():
            return True
        self.hide()
        self.destroy()
        if self.quit_cb:
            self.quit_cb(self)
        return False

    def edit_cut(self, mi):
        self.buffer.cut_clipboard(self.clipboard, True)
        return

    def edit_copy(self, mi):
        self.buffer.copy_clipboard(self.clipboard)
        return

    def edit_paste(self, mi):
        self.buffer.paste_clipboard(self.clipboard, None, True)
        return

    def edit_clear(self, mi):
        self.buffer.delete_selection(True, True)
        return

    def _search(self, search_string, iter=None):
        if iter is None:
            start = self.buffer.get_start_iter()
        else:
            start = iter
        i = 0
        if search_string:
            self.search_string = search_string
            res = start.forward_search(
                search_string, gtk.TEXT_SEARCH_TEXT_ONLY)
            if res:
                match_start, match_end = res
                self.buffer.place_cursor(match_start)
                self.buffer.select_range(match_start, match_end)
                self.text.scroll_to_iter(match_start, 0.0)
                self.last_search_iter = match_end

            else:
                self.search_string = None
                self.last_search_iter = None

    def edit_find(self, mi):
        def dialog_response_callback(dialog, response_id):
            if response_id == gtk.RESPONSE_CLOSE:
                dialog.destroy()
                return
            self._search(search_text.get_text(), self.last_search_iter)
        search_text = gtk.Entry()
        s = self.buffer.get_selection_bounds()
        if len(s) > 0:
            search_text.set_text(self.buffer.get_slice(s[0], s[1]))
        dialog = gtk.Dialog(_("Search"), self,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_FIND, RESPONSE_FORWARD,
                             gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        dialog.vbox.pack_end(search_text, True, True, 0)
        dialog.connect("response", dialog_response_callback)
        search_text.show()
        search_text.grab_focus()
        dialog.show_all()
        response_id = dialog.run()

    def edit_find_next(self, mi):
        self._search(self.search_string, self.last_search_iter)

    def help_about(self, mi):
        dlg = gtk.MessageDialog(self, gtk.DIALOG_DESTROY_WITH_PARENT,
                                gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
                                _("Text editor creators:\n\n") +
                                _("Copyright (C)\n") +
                                _("1998 James Henstridge\n") +
                                _("2004 John Finlay\n\n") +
                                _("The edit.py program is covered by the GPL>=2"))
        dlg.run()
        dlg.hide()
        return


class pluginEditor:
    def __init__(self, plugin_type, plugin_name, finishEditCallback):
        self._finishEditCallback = finishEditCallback
        self._plugin_type = plugin_type
        self._plugin_name = plugin_name

        # The filename to edit
        self._filename = os.path.join(ROOT_PATH, 'plugins', plugin_type,
                                      plugin_name + '.py')

        # Create the window
        w = EditWindow(quit_cb=self._quit_cb)
        w.load_file(self._filename)
        w.show()
        w.set_size_request(600, 400)

        gtk.main()
        return

    def _quit_cb(self, widget):
        """
        The quit callback.
        """
        gtk.main_quit()
        self._finishEditCallback(self._plugin_type, self._plugin_name)
