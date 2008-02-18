import pygtk
pygtk.require('2.0')
import gtk

import os

def InputBox(title, label, parent, text=''):
    dlg = gtk.Dialog(title, parent, gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_OK, gtk.RESPONSE_OK,
                      gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
    lbl = gtk.Label(label)
    lbl.show()
    dlg.vbox.pack_start(lbl)
    entry = gtk.Entry()
    if text: entry.set_text(text)
    entry.show()
    dlg.vbox.pack_start(entry, False)
    resp = dlg.run()
    text = entry.get_text()
    dlg.hide()
    if resp == gtk.RESPONSE_CANCEL:
        return None
    return text

def OpenFile(title, parent=None, dirname=None, fname=None):
    dlg = gtk.FileChooserDialog(title, parent,
                                buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK,
                                         gtk.STOCK_CANCEL,
                                         gtk.RESPONSE_CANCEL))
    if fname:
        dlg.set_current_folder(os.path.dirname(fname))
    elif dirname:
        dlg.set_current_folder(dirname)
    dlg.set_local_only(True)
    resp = dlg.run()
    fname = dlg.get_filename()
    dlg.hide()
    if resp == gtk.RESPONSE_CANCEL:
        return None
    return fname

def SaveFile(title, parent=None, dirname=None, fname=None):
    dlg = gtk.FileChooserDialog(title, parent,
                                gtk.FILE_CHOOSER_ACTION_SAVE,
                                buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK,
                                         gtk.STOCK_CANCEL,
                                         gtk.RESPONSE_CANCEL))
    if fname:
        dlg.set_filename(fname)
    elif dirname:
        dlg.set_current_folder(dirname)
    dlg.set_local_only(True)
    resp = dlg.run()
    fname = dlg.get_filename()
    dlg.hide()
    if resp == gtk.RESPONSE_CANCEL:
        return None
    return fname
