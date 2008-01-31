'''
scantab.py

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
import gtk, gobject, threading
import core.ui.gtkUi.entries as entries 
import core.ui.gtkUi.helpers as helpers 
import core.ui.gtkUi.pluginconfig as pluginconfig
import core.ui.gtkUi.scanrun as scanrun
from core.controllers.w3afException import w3afException
from core.controllers.misc import parseOptions

class ScanTab(gtk.VBox):
    '''Tab for all related to Scanning.

    @param w3af: the main core class.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, mainwin, w3af):
        super(ScanTab,self).__init__()
        self.w3af = w3af
        self.mainwin = mainwin

        # start scan button (we create it first because of the signal)
        self.gobox = gtk.HBox()
        self.gobtn = entries.SemiStockButton("Start scan", gtk.STOCK_MEDIA_PLAY)
        self.gobtnconn = self.gobtn.connect("clicked", self._startScan)
        self.gobox.pack_start(self.gobtn, expand=True, fill=False)

        self.scanok = helpers.PropagateBuffer(self.gobtn.set_sensitive)

        # the plugin config body
        self.pcbody = pluginconfig.PluginConfigBody(self, w3af)
        self.pack_start(self.pcbody, padding=5)

        # let's finish with the scan button
        self.gobtn.show()
        self.pack_start(self.gobox, expand=False, fill=False)
        self.gobox.show()

        self.show()

    def _startScan(self, widg):
        '''Starts the actual scanning.

        @param widg: the widget that generated the signal.
        '''
        # save the activated plugins
        for type,plugins in self.pcbody.getActivatedPlugins():
            self.w3af.setPlugins(plugins, type)

        # save the URL
        options = parseOptions.parseXML(self.w3af.target.getOptionsXML())
        url = self.pcbody.target.get_text()
        options['target'].update(default=url)
        try:
            helpers.coreWrap(self.w3af.target.setOptions, options)
        except w3afException:
            return

        # start real work in background
        try:
            helpers.coreWrap(self.w3af.initPlugins)
            helpers.coreWrap(self.w3af.verifyEnvironment)
        except w3afException:
            return
        threading.Thread(target=self.w3af.start).start()

        # create new panel
        scrun = scanrun.ScanRunBody()

        # replace previous panel for new one
        self.remove(self.gobox)
        self.remove(self.pcbody)
        self.pack_start(scrun, padding=5)
        self.pack_start(self.gobox, expand=False, fill=False)
        scrun.show()

        # change the button to a "stop" one
        self.gobtn.disconnect(self.gobtnconn)
        self.gobtnconn = self.gobtn.connect("clicked", self._stopScan)
        self.gobtn.changeInternals("Stop scan", gtk.STOCK_MEDIA_STOP)

        # activate exploit tab
        # FIXME: review this, I'm not sure *when* activate this
        self.mainwin.activateExploit()

    def _stopScan(self, widg):
        print "FIXME: Stop not implemented yet!"
