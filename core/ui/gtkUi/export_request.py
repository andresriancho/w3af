'''
export_request.py

Copyright 2008 Andres Riancho

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
import gtk
from . import entries

from .encdec import SimpleTextView

from core.data.export.ajax_export import ajax_export
from core.data.export.html_export import html_export
from core.data.export.python_export import python_export
from core.data.export.ruby_export import ruby_export

from core.controllers.w3afException import w3afException

export_request_example = """\
GET http://localhost/script.php HTTP/1.0
Host: www.some_host.com
User-Agent: w3af.sf.net
Pragma: no-cache
Content-Type: application/x-www-form-urlencoded
"""

class export_request(entries.RememberingWindow):
    '''Infrastructure to export HTTP requests.

    @author: Andres Riancho < andres.riancho | gmail.com >
    '''
    def __init__(self, w3af, initialRequest=None):
        super(export_request,self).__init__(
            w3af, "exportreq", "w3af - Export Requests", "Export_Requests")
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.png')
        self.w3af = w3af

        # different ways of exporting data
        self._exporters = [
                ('HTML', html_export),
                ('Ajax', ajax_export),
                ('Python', python_export),
                ('Ruby', ruby_export)
                ]

        # splitted panes
        vpan = entries.RememberingVPaned(w3af, "pane-exportrequests")

        # upper pane that shows HTTP request
        vbox = gtk.VBox()
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.http_request = SimpleTextView()
        sw.add(self.http_request)
        vbox.pack_start(sw, True, True, padding=5)

        # middle widgets that show the export method
        table = gtk.Table(1, 6, homogeneous=True)
        cb = gtk.combo_box_new_text()
        for (lab, fnc) in self._exporters:
            cb.append_text(lab)
            b = gtk.Button(lab)
        cb.set_active(0)
        table.attach(cb, 2, 3, 0, 1)
        b = entries.SemiStockButton("Export", gtk.STOCK_GO_DOWN, _("Export the request"))
        b.connect("clicked", self._export, cb)
        table.attach(b, 3, 4, 0, 1)
        vbox.pack_start(table, False, False, padding=5)
        vpan.pack1(vbox)

        # lower pane with exported data and save button
        vbox = gtk.VBox()
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.exported_text = SimpleTextView()
        sw.add(self.exported_text)
        vbox.pack_start( sw, True, True, padding=5)
        
        b = entries.SemiStockButton("Save request as...", gtk.STOCK_SAVE_AS, _("Save request as..."))
        b.connect("clicked", self._save_as)
        vbox.pack_start( b, False, False, padding=5)
        
        vpan.pack2(vbox)
        
        # Show the data
        if initialRequest is None:
            self.http_request.setText( export_request_example )
        else:
            (request_header, request_body) = initialRequest
            self.http_request.setText(request_header + '\n\n' + request_body )
        func = self._exporters[0][1]
        self.exported_text.setText(func(self.http_request.getText()))

        self.vbox.pack_start(vpan, padding=10)
        self.show_all()
        
    def _export(self, widg, combo):
        '''Exports the upper text.'''
        opc = combo.get_active()
        func = self._exporters[opc][1]
        
        try:
            exported_request = func(self.http_request.getText())
        except w3afException, w3:
            error_msg = str(w3)
            self.exported_text.setText( error_msg )
        else:
            self.exported_text.setText( exported_request )
        
    def _save_as(self, widg):
        '''
        Save the exported data to a file using a file chooser.
        '''
        chooser = gtk.FileChooserDialog(title='Save as...',action=gtk.FILE_CHOOSER_ACTION_SAVE,
                        buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            # Save the contents of the self.exported_text to the selected file
            filename = chooser.get_filename()
            try:
                fh = file(filename, 'w')
                fh.write(self.exported_text.getText())
            except:
                msg = _("Failed to save exported data to file")
                dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, msg)
                opt = dlg.run()
                dlg.destroy()
        elif response == gtk.RESPONSE_CANCEL:
            pass
        chooser.destroy()

