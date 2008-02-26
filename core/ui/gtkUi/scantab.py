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
import core.ui.gtkUi.messages as messages
import core.ui.gtkUi.scanrun as scanrun
from core.controllers.w3afException import w3afException
from core.controllers.misc import parseOptions
import sys

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

        # save the URL, the rest of the options are saved in the "Advanced" dialog
        options = parseOptions.parseXML(self.w3af.target.getOptionsXML())
        url = self.pcbody.target.get_text()
        options['target'].update(default=url)
        try:
            helpers.coreWrap(self.w3af.target.setOptions, options)
        except w3afException:
            return

        # Verify that everything is ready to run
        try:
            helpers.coreWrap(self.w3af.initPlugins)
            helpers.coreWrap(self.w3af.verifyEnvironment)
        except w3afException, w3:
            return

        def startScanWrap():
            try:
                self.w3af.start()
            except KeyboardInterrupt:
#                print 'Ctrl+C found, exiting!'
                pass
        
        # start real work in background, and start supervising if it ends                
        threading.Thread(target=startScanWrap).start()
        gobject.timeout_add(500, self._stoppingScan)

        # create new panel
        scnew = scanrun.ScanRunBody(self.w3af)

        # replace previous panel for new one
        self.remove(self.gobox)
        self.remove(self.pcbody)
        self.pack_start(scnew, padding=5)
        self.pack_start(self.gobox, expand=False, fill=False)
        scnew.show()
        self.pcbody = scnew

        # change the button to a "stop" one
        self.gobtn.disconnect(self.gobtnconn)
        self.gobtnconn = self.gobtn.connect("clicked", self._stopScan)
        self.gobtn.changeInternals("Stop scan", gtk.STOCK_MEDIA_STOP)
        self.mainwin.throbber.start()

        # activate exploit tab
        self.mainwin.setSensitiveExploit(True)

    def _stopScan(self, widg):
        '''Stops the scanning.

        @param widg: the widget that generated the signal.
        '''
        # stop and wait until really stopped
        self.w3af.stop()
        self.gobtn.set_sensitive(False)
        self.gobtn.changeInternals("Stopping", gtk.STOCK_MEDIA_STOP)

    def _stoppingScan(self):
        '''Handles the waiting until core actually stopped.

        @return: True if needs to be called again, False if core stopped.
        '''
        if self.w3af.isRunning():
            return True

        # change the button to go back
        self.gobtn.disconnect(self.gobtnconn)
        self.gobtnconn = self.gobtn.connect("clicked", self._resumeScan)
        self.gobtn.changeInternals("Back to config", gtk.STOCK_GO_BACK)
        self.gobtn.set_sensitive(True)
        self.mainwin.throbber.stop()
        return False

    def _resumeScan(self, widg):
        '''Goes back to the configuration pane.

        @param widg: the widget that generated the signal.
        '''
        # clean core and some widgets/infrastructure
        self.w3af.cleanup()
        messages.getQueueDiverter(reset=True)

        # change the button
        self.gobtn.disconnect(self.gobtnconn)
        self.gobtnconn = self.gobtn.connect("clicked", self._startScan)
        self.gobtn.changeInternals("Start scan", gtk.STOCK_MEDIA_PLAY)
        self.gobtn.set_sensitive(True)

        # create new panel & replace previous panel for new one
        scnew = pluginconfig.PluginConfigBody(self, self.w3af)
        self.remove(self.gobox)
        self.remove(self.pcbody)
        self.pack_start(scnew, padding=5)
        self.pack_start(self.gobox, expand=False, fill=False)
        scnew.show()
        self.pcbody = scnew

        # deactivate exploit tab
        self.mainwin.setSensitiveExploit(False)

    def togglePanels(self, panel, active):
        '''Turn on and off the panels.

        @param panel: The panel to turn on and off
        @param active: If it should be activated or deactivated
        '''
        # this pcbody must be the ScanRunBody panel... it also
        # can be the initial window, but in this case we will never 
        # be here because the View menu should be in gray
        self.pcbody.togglePanels(panel, active)
