'''
scanrun.py

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

import urllib2, time
import re
from . import helpers, kbtree, messages, httpLogTab, reqResViewer, craftedRequests
import core.data.kb.knowledgeBase as kb
import webbrowser

# To show request and responses
from core.data.db.reqResDBHandler import reqResDBHandler

class FullKBTree(kbtree.KBTree):
    '''A tree showing all the info.
    
    This also gives a long description of the element when clicked.

    @param kbbrowser: The KB Browser
    @param filter: The filter to show which elements

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af, kbbrowser, filter):
        super(FullKBTree,self).__init__(w3af, filter, 'Knowledge Base', strict=False)
        self._dbHandler = reqResDBHandler()
        self.kbbrowser = kbbrowser
        self.connect('cursor-changed', self._showDesc)
        self.show()

    def _showDesc(self, tv):
        '''Shows the description at the right

        @param tv: the treeview.
        '''
        (path, column) = tv.get_cursor()
        if path is None:
            return

        instance = self.getInstance(path)
        if hasattr(instance, "getDesc"):
            longdesc = str(instance.getDesc())
        else:
            longdesc = ""
        self.kbbrowser.explanation.set_text(longdesc)
        
        success = False
        if hasattr(instance, "getId" ):
            if instance.getId() != None:
                # The request and response that generated the vulnerability
                search_result = self._dbHandler.searchById( instance.getId() )
                if len(search_result) == 1:
                    request, response = search_result[0]
                    self.kbbrowser.rrV.request.showObject( request )
                    self.kbbrowser.rrV.response.showObject( response )
                    success = True
                else:
                    om.out.error('Failed to find request/response with id: ' + str(instance.getId()) + ' in the database.' )
        
        if success:
            self.kbbrowser.rrV.set_sensitive(True)
        else:
            self.kbbrowser.rrV.request.clearPanes()
            self.kbbrowser.rrV.response.clearPanes()
            self.kbbrowser.rrV.set_sensitive(False)
            
            
class KBBrowser(gtk.HPaned):
    '''Show the Knowledge Base, with the filter and the tree.
    
    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        super(KBBrowser,self).__init__()

        # the filter to the tree
        filterbox = gtk.HBox()
        self.filters = {}
        def makeBut(label, signal, initial):
            but = gtk.CheckButton(label)
            but.set_active(initial)
            but.connect("clicked", self.typeFilter, signal)
            self.filters[signal] = initial
            but.show()
            filterbox.pack_start(but, expand=False, fill=False, padding=2)
        makeBut("Vuln", "vuln", True)
        makeBut("Info", "info", True)
        makeBut("Misc", "misc", False)
        filterbox.show()

        # the kb tree 
        self.kbtree = FullKBTree(w3af, self, self.filters)

        # the filter and tree box
        treebox = gtk.VBox()
        treebox.pack_start(filterbox, expand=False, fill=False)
        treebox.pack_start(self.kbtree)
        treebox.show()

        # all in the first pane
        scrollwin21 = gtk.ScrolledWindow()
        scrollwin21.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrollwin21.add_with_viewport(treebox)
        scrollwin21.show()

        # the explanation
        explan_tv = gtk.TextView()
        explan_tv.set_editable(False)
        explan_tv.set_cursor_visible(False)
        explan_tv.set_wrap_mode(gtk.WRAP_WORD)
        self.explanation = explan_tv.get_buffer()
        explan_tv.show()
        scrollwin22 = gtk.ScrolledWindow()
        scrollwin22.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrollwin22.add_with_viewport(explan_tv)
        scrollwin22.show()        
        
        # The request/response viewer
        self.rrV = reqResViewer.reqResViewer(w3af)
        vpanedExplainAndView = gtk.VPaned()
        vpanedExplainAndView.pack1( scrollwin22 )
        vpanedExplainAndView.pack2( self.rrV )
        vpanedExplainAndView.set_position(100)
        vpanedExplainAndView.show_all()
        
        # pack & show
        self.pack1(scrollwin21)
        self.pack2(vpanedExplainAndView)
        self.set_position(250)
        self.show()

    def typeFilter(self, button, type):
        '''Changes the filter of the KB in the tree.'''
        self.filters[type] = button.get_active()
        self.kbtree.setFilter(self.filters)


HEAD_TO_SEND = """\
GET %s HTTP/1.0
Host: %s
User-Agent: w3af.sf.net
"""

class URLsTree(gtk.TreeView):
    '''Show the URLs that the system discovers.
    
    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        self.w3af = w3af

        # simple empty Tree Store
        self.treestore = gtk.TreeStore(str)
        gtk.TreeView.__init__(self, self.treestore)
        self.connect('button-release-event', self.popup_menu)

        # the TreeView column
        tvcolumn = gtk.TreeViewColumn('URLs')
        cell = gtk.CellRendererText()
        tvcolumn.pack_start(cell, True)
        tvcolumn.add_attribute(cell, "text", 0)
        self.append_column(tvcolumn)

        # this tree structure will keep the parents where to insert nodes
        self.treeholder = {}

        # get the queue and go live
        queue = kb.kb.getData('urls', 'urlQueue')
        self.urls = helpers.IteratedQueue(queue)
        gobject.timeout_add(500, self.addUrl().next)
        self.show()

    def addUrl(self):
        '''Adds periodically the new URLs to the tree.

        @return: True to keep being called by gobject, False when it's done.
        '''
        for url in self.urls.get():
            if url is None:
                yield True
                continue
            (scheme, netloc, path, params, query, fragment) = urllib2.urlparse.urlparse(url)
            ini = "%s://%s" % (scheme, netloc)
            end = ""
            if params:
                end += ";" + params
            if query:
                end += "?" + query
            if fragment:
                end += "#" + fragment

            # AR:
            # This was the old way of doing it:            
            #nodes = path.split("/")[1:]
            # But it generated this bug:    http://sourceforge.net/tracker/index.php?func=detail&aid=1963947&group_id=170274&atid=853652
            # So I changed it to this:
            splittedPath = re.split('(\\\\|/)', path )
            nodes = []
            for i in splittedPath:
                if i not in ['\\','/']:
                    nodes.append(i)
            # Ok, now we continue with the code from Facundo
            nodes.insert(0, ini)
            nodes.append(end)
            parts = [x for x in nodes if x]
            self._insertNodes(None, parts, self.treeholder)
        yield False

    def _insertNodes(self, parent, parts, holder):
        '''Insert a new node in the tree.

        It's recursive: it walks the path of nodes, being each node a 
        part of the URL, checking every time if needs to create a new
        node or just enter in it.

        @param parent: the parent to insert the node
        @param parts: the rest of the parts to walk the path
        @param holder: the dict when what is already exists is stored.

        @return: The new or modified holder
        '''
        if not parts:
            return {}
        node = parts[0]
        rest = parts[1:]
        if node in holder:
            # already exists, use it if have more nodes
            (treenode, children) = holder[node]
            return self._insertNodes(treenode, rest, children)

        # does not exist, create it
        newtreenode = self.treestore.append(parent, [node])
        newholdnode = self._insertNodes(newtreenode, rest, {})
        holder[node] = (newtreenode, newholdnode)
        return holder

    def popup_menu( self, tv, event ):
        '''Shows a menu when you right click on a plugin.
        
        @param tv: the treeview.
        @parameter event: The GTK event 
        '''
        if event.button != 3:
            return

        (path, column) = tv.get_cursor()
        # Is it over a plugin name ?
        if path is None:
            return

        # Get the information about the click
        fullurl = "/".join(self.treestore[path[:i+1]][0] for i in range(len(path)))
        host = urllib2.urlparse.urlparse(fullurl)[1]
        sendtext = HEAD_TO_SEND % (fullurl, host)

        gm = gtk.Menu()

        e = gtk.MenuItem("Open with Manual Request Editor...")
        e.connect('activate', self._sendRequest, sendtext, craftedRequests.ManualRequests)
        gm.append( e )
        e = gtk.MenuItem("Open with Fuzzy Request Editor...")
        e.connect('activate', self._sendRequest, sendtext, craftedRequests.FuzzyRequests)
        gm.append( e )
        e = gtk.MenuItem("Open with default browser...")
        e.connect('activate', self._openBrowser, fullurl)
        gm.append( e )

        gm.show_all()
        gm.popup( None, None, None, event.button, event.time)

    def _openBrowser( self, widg, text):
        webbrowser.open_new_tab(text)
        
    def _sendRequest(self, widg, text, func):
        func(self.w3af, (text,""))

class ScanRunBody(gtk.Notebook):
    '''The whole body of scan run.
    
    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        super(ScanRunBody,self).__init__()
        
        # KB Browser
        # this one does not go inside a scrolled window, because that's handled
        # in each widget of itself
        kbbrowser = KBBrowser(w3af)
        l = gtk.Label("KB Browser")
        self.append_page(kbbrowser, l)
        
        # urlstree
        urlstree = URLsTree(w3af)
        scrollwin1 = gtk.ScrolledWindow()
        scrollwin1.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrollwin1.add_with_viewport(urlstree)
        scrollwin1.show()
        l = gtk.Label("URLs")
        self.append_page(scrollwin1, l)

        # Request Response navigator
        httplog = httpLogTab.httpLogTab(w3af)
        l = gtk.Label("Request/Response navigator")
        l.show()
        self.append_page(httplog, l)

        self.show()
