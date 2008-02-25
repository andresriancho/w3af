'''
mozillaTab.py

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

import gtk
import gtkmozembed
import core.ui.gtkUi.entries as entries

class mozillaTab(gtk.HPaned):
    '''
    A tab that contains a mozilla browser. There's a bug in the library, 
    that after a change in the Mozilla API makes crash the program, 
    unless started like this (at least in Ubuntu):

    export LD_LIBRARY_PATH=/usr/lib/firefox && export MOZILLA_FIVE_HOME=/usr/lib/firefox && ./w3af -g

    See these for more info regarding this issue:
      
        https://help.ubuntu.com/community/PythonRecipes/WebBrowser
        https://bugs.launchpad.net/ubuntu/+source/firefox/+bug/26436
        https://bugzilla.mozilla.org/show_bug.cgi?id=325884
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    @author: Facundo Batista ( facundo@taniquetil.com.ar )
    '''
    # FIXME: See how we can make that library path setup automatically...
    def __init__(self, w3af):
        super(mozillaTab,self).__init__()
        
        # Create the mozilla browser object
        self.mozilla = gtk.Label("here goes the embedded mozilla widget\n(if we can make it work)")
        self.mozilla = gtkmozembed.MozEmbed()
        self.mozilla.show()
        
#        #TODO: Create a html file, and load that file, so no connections are made
#        content = "<html><h1>Heading</h1>I'm some semi-random html...</html>"
#        #mozWidg.render_data(content, long(len(content)), "file://.", 'text/html')
        
        # Create the URL bar
        urlbarbox = gtk.HBox(spacing=5)

        # go button
        self.gobtn = entries.SemiStockButton("Go!", gtk.STOCK_MEDIA_PLAY)
        self.gobtn.connect("clicked", self.go)

        # url entry
        self.urlentry = entries.AdvisedEntry("Insert the target URL here", self._activGo)
        self.urlentry.connect("activate", self.go)

        # back button
        back = gtk.Button(stock=gtk.STOCK_GO_BACK)
        back.connect("clicked", self.go_back)

        # fwrd button
        fwrd = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        fwrd.connect("clicked", self.go_fwrd)

        # finish the url bar
        urlbarbox.pack_start(back, expand=False)
        urlbarbox.pack_start(fwrd, expand=False)
        urlbarbox.pack_start(self.urlentry, expand=True)
        urlbarbox.pack_start(self.gobtn, expand=False)
        urlbarbox.show_all()
        
        # Create the main container
        mainvbox = gtk.VBox(spacing=10)
        mainvbox.pack_start(urlbarbox, expand=False)
        mainvbox.pack_start(self.mozilla, expand=True)
        mainvbox.show()
        
        self.add(mainvbox)
        self.set_position(300)
        self.show()

    def _activGo(self, widg, change):
        self.gobtn.set_sensitive(change)

    def go(self, widg):
        url = self.urlentry.get_text()
        self.mozilla.load_url(url)

    def go_back(self, widg):
        self.mozilla.go_back()

    def go_fwrd(self, widg):
        self.mozilla.go_forward()
