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

import gtk, gobject

import urllib2
import sys
import re, Queue, threading
from . import helpers, kbtree, httpLogTab, reqResViewer, craftedRequests, entries
import webbrowser
import core.controllers.outputManager as om
from extlib.xdot import xdot

# To show request and responses
from core.data.db.history import HistoryItem
import core.data.kb.knowledgeBase as kb

RECURSION_LIMIT = sys.getrecursionlimit() - 5
RECURSION_MSG = "Recursion limit: can't go deeper"

class FullKBTree(kbtree.KBTree):
    '''A tree showing all the info.

    This also gives a long description of the element when clicked.

    @param kbbrowser: The KB Browser
    @param filter: The filter to show which elements

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af, kbbrowser, ifilter):
        super(FullKBTree,self).__init__(w3af, ifilter, 'Knowledge Base', strict=False)
        self._historyItem = HistoryItem()
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
            if instance.getId() is not None:
                #
                # We have two different cases:
                #
                # 1) The object is related to ONLY ONE request / response
                # 2) The object is related to MORE THAN ONE request / response
                #
                # For 1), we show the classic view, and for 2) we show the classic
                # view with a "page control"
                #
                # Work:
                #
                if len( instance.getId() ) == 1:
                    # There is ONLY ONE id related to the object
                    # This is 1)
                    self.kbbrowser.pagesControl.deactivate()
                    self.kbbrowser._pageChange(0)
                    self.kbbrowser.pagesControl.hide()
                    self.kbbrowser.title0.hide()

                    # This handles a special case, where the plugin writer made a mistake and
                    # failed to set an id to the info / vuln object:
                    if instance.getId()[0] is None:
                        raise Exception('Exception - The id should not be None! "' + str(instance._desc) + '".')
                        success = False
                    else:
                        # ok, we don't have None in the id:
                        historyItem = self._historyItem.read(instance.getId()[0])
                        if historyItem:
                            self.kbbrowser.rrV.request.showObject(historyItem.request)
                            self.kbbrowser.rrV.response.showObject(historyItem.response)
                            
                            # Don't forget to highlight if neccesary
                            severity = instance.getSeverity()
                            for s in instance.getToHighlight():
                                self.kbbrowser.rrV.response.highlight( s, severity )
                            
                            success = True
                        else:
                            om.out.error(_('Failed to find request/response with id: ') + str(instance.getId()) + _(' in the database.') )
                else:
                    # There are MORE THAN ONE ids related to the object
                    # This is 2)
                    self.kbbrowser.pagesControl.show()
                    self.kbbrowser.title0.show()

                    self.kbbrowser.req_res_ids = instance.getId()
                    self.kbbrowser.pagesControl.activate(len(instance.getId()))
                    self.kbbrowser._pageChange(0)
                    success = True

        if success:
            self.kbbrowser.rrV.set_sensitive(True)
        else:
            self.kbbrowser.rrV.request.clearPanes()
            self.kbbrowser.rrV.response.clearPanes()
            self.kbbrowser.rrV.set_sensitive(False)


class KBBrowser(entries.RememberingHPaned):
    '''Show the Knowledge Base, with the filter and the tree.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        super(KBBrowser,self).__init__(w3af, "pane-kbbrowser", 250)

        # Internal variables:
        #
        # Here I save the request and response ids to be used in the page control
        self.req_res_ids = []
        # This is to search the DB and print the different request and responses as they are
        # requested from the page control, "_pageChange" method.
        self._historyItem = HistoryItem()

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

        # all in the first pane
        scrollwin21 = gtk.ScrolledWindow()
        scrollwin21.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrollwin21.add(self.kbtree)
        scrollwin21.show()

        # the filter and tree box
        treebox = gtk.VBox()
        treebox.pack_start(filterbox, expand=False, fill=False)
        treebox.pack_start(scrollwin21)
        treebox.show()

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
        self.rrV = reqResViewer.reqResViewer(w3af, withAudit=False)
        self.rrV.set_sensitive(False)

        # Create the title label to show the request id
        self.title0 = gtk.Label()
        self.title0.show()

        # Create page changer to handle info/vuln objects that have MORE THAN ONE
        # related request/response
        self.pagesControl = entries.PagesControl(w3af, self._pageChange, 0)
        self.pagesControl.deactivate()
        self._pageChange(0)
        centerbox = gtk.HBox()
        centerbox.pack_start(self.pagesControl, True, False)

        # Add everything to a vbox
        vbox_rrv_centerbox = gtk.VBox()
        vbox_rrv_centerbox.pack_start(self.title0, False, True)
        vbox_rrv_centerbox.pack_start(self.rrV,  True,  True)
        vbox_rrv_centerbox.pack_start(centerbox,  False,  False)

        # and show
        vbox_rrv_centerbox.show()
        self.pagesControl.show()
        centerbox.show()

        # And now put everything inside the vpaned
        vpanedExplainAndView = entries.RememberingVPaned(w3af, "pane-kbbexplainview", 100)
        vpanedExplainAndView.pack1( scrollwin22 )
        vpanedExplainAndView.pack2( vbox_rrv_centerbox )
        vpanedExplainAndView.show()

        # pack & show
        self.pack1(treebox)
        self.pack2(vpanedExplainAndView)
        self.show()

    def typeFilter(self, button, ptype):
        '''Changes the filter of the KB in the tree.'''
        self.filters[ptype] = button.get_active()
        self.kbtree.setFilter(self.filters)

    def _pageChange(self, page):
        '''
        Handle the page change in the page control.
        '''
        # Only do something if I have a list of request and responses
        if self.req_res_ids:
            request_id = self.req_res_ids[page]
            try:
                historyItem = self._historyItem.read(request_id)
            except:
                # the request brought problems
                self.rrV.request.clearPanes()
                self.rrV.response.clearPanes()
                self.rrV.set_sensitive(False)
                self.title0.set_markup( "<b>Error</b>")
            else:
                self.title0.set_markup( "<b>Id: %d</b>" % request_id )
                self.rrV.request.showObject( historyItem.request )
                self.rrV.response.showObject( historyItem.response )
                self.rrV.set_sensitive(True)


class URLsGraph(gtk.VBox):
    '''Graph the URLs that the system discovers.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        super(URLsGraph,self).__init__()
        self.w3af = w3af

        self.toolbox = gtk.HBox()
        b = entries.SemiStockButton("", gtk.STOCK_ZOOM_IN, 'Zoom In')
        b.connect("clicked", self._zoom, "in")
        self.toolbox.pack_start(b, False, False)
        b = entries.SemiStockButton("", gtk.STOCK_ZOOM_OUT, 'Zoom Out')
        b.connect("clicked", self._zoom, "out")
        self.toolbox.pack_start(b, False, False)
        b = entries.SemiStockButton("", gtk.STOCK_ZOOM_FIT, 'Zoom Fit')
        b.connect("clicked", self._zoom, "fit")
        self.toolbox.pack_start(b, False, False)
        b = entries.SemiStockButton("", gtk.STOCK_ZOOM_100, 'Zoom 100%')
        b.connect("clicked", self._zoom, "100")
        self.toolbox.pack_start(b, False, False)
        self.pack_start(self.toolbox, False, False)
        self.toolbox.set_sensitive(False)

        # no graph yet
        self.widget = gtk.Label(_("No info yet"))
        self.widget.set_sensitive(False)

        self.nodos_code = []
        self._somethingnew = False
        self.pack_start(self.widget)
        self.show_all()

        gobject.timeout_add(500, self._draw_start)

    def _zoom(self, widg, what):
        f = getattr(self.widget, "on_zoom_"+what)
        f(None)

    def _draw_start(self):
        if not self._somethingnew:
            return True

        # let's draw!
        q = Queue.Queue()
        evt = threading.Event()
        th = threading.Thread(target=self._draw_real, args=(q,evt))
        th.start()
        gobject.timeout_add(500, self._draw_end, q, evt)
        return False

    def _draw_real(self, q, evt):
        new_widget = xdot.DotWidget()
        self._somethingnew = False
        dotcode = "graph G {%s}" % "\n".join(self.nodos_code)
        new_widget.set_dotcode(dotcode)
        evt.set()
        q.put(new_widget)

    def _draw_end(self, q, evt):
        if not evt:
            return True

        new_widget = q.get()
        new_widget.zoom_to_fit()

        # put that drawing in the widget
        self.remove(self.widget)
        self.pack_start(new_widget)
        self.widget = new_widget
        new_widget.show()
        self.toolbox.set_sensitive(True)

        gobject.timeout_add(500, self._draw_start)


    def limitNode(self, parent, node, name):
        # I have to escape the quotes, because I don't want a "dot code injection"
        # This was bug #2675512
        # https://sourceforge.net/tracker/?func=detail&aid=2675512&group_id=170274&atid=853652
        node = str(node).replace('"', '\\"')
        name = str(name).replace('"', '\\"')
        
        self.nodos_code.append('"%s" [label="%s"]' % (node, name))
        if parent:
            parent = str(parent).replace('"', '\\"')
            nline = '"%s" -- "%s"' % (parent, node)
            self.nodos_code.append(nline)
        self._somethingnew = True

    def newNode(self, parent, node, name, isLeaf):
        # I have to escape the quotes, because I don't want a "dot code injection"
        # This was bug #2675512
        # https://sourceforge.net/tracker/?func=detail&aid=2675512&group_id=170274&atid=853652
        node = str(node).replace('"', '\\"')
        name = str(name).replace('"', '\\"')

        if not isLeaf:
            self.nodos_code.append('"%s" [shape=box]' % node)
        self.nodos_code.append('"%s" [label="%s"]' % (node, name))
        if parent:
            parent = str(parent).replace('"', '\\"')
            nline = '"%s" -- "%s"' % (parent, node)
            self.nodos_code.append(nline)
        self._somethingnew = True



HEAD_TO_SEND = """\
GET %s HTTP/1.0
Host: %s
User-Agent: w3af.sf.net
"""

class URLsTree(gtk.TreeView):
    '''Show the URLs that the system discovers.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af, grapher):
        self.w3af = w3af
        self.grapher = grapher

        # simple empty Tree Store
        self.treestore = gtk.TreeStore(str)
        gtk.TreeView.__init__(self, self.treestore)
        self.connect('button-release-event', self.popup_menu)
        self.connect('button-press-event', self._doubleClick)

        # the TreeView column
        tvcolumn = gtk.TreeViewColumn('URLs')
        tvcolumn.set_sort_column_id(0)
        cell = gtk.CellRendererText()
        tvcolumn.pack_start(cell, True)
        tvcolumn.add_attribute(cell, "text", 0)
        self.append_column(tvcolumn)

        # this tree structure will keep the parents where to insert nodes
        self.treeholder = {}

        # get the queue and go live
        self.urls = IteratedURLList()
        gobject.timeout_add(750, self.addUrl().next)
        self.show()

    def _doubleClick(self, widg, event):
        '''If double click, expand/collapse the row.'''
        if event.type == gtk.gdk._2BUTTON_PRESS:
            path = self.get_cursor()[0]
            # This "if path" fixed bug #2205544
            # https://sourceforge.net/tracker2/?func=detail&atid=853652&aid=2205544&group_id=170274
            if path:
                if self.row_expanded(path):
                    self.collapse_row(path)
                else:
                    self.expand_row(path, False)

    def addUrl(self):
        '''Adds periodically the new URLs to the tree.

        @return: True to keep being called by gobject, False when it's done.
        '''
        for url in self.urls.get():
            if url is None:
                yield True
                continue
            
            path = url.getPath()
            params = url.getParamsString()
            query = str(url.querystring)
            fragment = url.getFragment()
            scheme = url.getProtocol()
            netloc = url.getDomain()

            ini = "%s://%s" % (scheme, netloc)
            end = ""
            if params:
                end += ";" + params
            if query:
                end += "?" + query
            if fragment:
                end += "#" + fragment

            splittedPath = re.split('(\\\\|/)', path )
            nodes = []
            for i in splittedPath:
                if i not in ['\\','/']:
                    nodes.append(i)

            nodes.insert(0, ini)
            nodes.append(end)
            parts = [x for x in nodes if x]
            self._insertNodes(None, parts, self.treeholder, 1)
            
            # TODO: Automatically sort after each insertion
            # Order the treeview
            self.treestore.sort_column_changed()
            
        yield False

    def _insertNodes(self, parent, parts, holder, rec_cntr):
        '''Insert a new node in the tree.

        It's recursive: it walks the path of nodes, being each node a
        part of the URL, checking every time if needs to create a new
        node or just enter in it.

        @param parent: the parent to insert the node
        @param parts: the rest of the parts to walk the path
        @param holder: the dict when what is already exists is stored.
        @param rec_cntr: the recursion counter

        @return: The new or modified holder
        '''
        if not parts:
            return {}
        node = parts[0]
        rest = parts[1:]

        if rec_cntr >= RECURSION_LIMIT:
            newtreenode = self.treestore.append(parent, [RECURSION_MSG])
            self.grapher.limitNode(parent, newtreenode, RECURSION_MSG)
            return holder

        if node in holder:
            # already exists, use it if have more nodes
            (treenode, children) = holder[node]
            return self._insertNodes(treenode, rest, children, rec_cntr+1)

        # does not exist, create it
        newtreenode = self.treestore.append(parent, [node])
        self.grapher.newNode(parent, newtreenode, node, not rest)
        newholdnode = self._insertNodes(newtreenode, rest, {}, rec_cntr+1)
        holder[node] = (newtreenode, newholdnode)
        return holder

    def popup_menu( self, tv, event ):
        '''Shows a menu when you right click on a URL in the treeview.

        @param tv: the treeview.
        @parameter event: The GTK event
        '''
        if event.button != 3:
            return

        (path, column) = tv.get_cursor()
        # Is it over a URL?
        if path is None:
            return

        # Get the information about the click
        fullurl = "/".join(self.treestore[path[:i+1]][0] for i in range(len(path)))
        host = urllib2.urlparse.urlparse(fullurl)[1]
        sendtext = HEAD_TO_SEND % (fullurl, host)

        gm = gtk.Menu()

        e = gtk.ImageMenuItem(_("Open with Manual Request Editor..."))
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_INDEX,  gtk.ICON_SIZE_MENU)
        e.set_image(image)
        e.connect('activate', self._sendRequest, sendtext, craftedRequests.ManualRequests)
        gm.append( e )

        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_PROPERTIES,  gtk.ICON_SIZE_MENU)
        e = gtk.ImageMenuItem(_("Open with Fuzzy Request Editor..."))
        e.set_image(image)
        e.connect('activate', self._sendRequest, sendtext, craftedRequests.FuzzyRequests)
        gm.append( e )

        e = gtk.ImageMenuItem(_("Open with default browser..."))
        e.connect('activate', self._openBrowser, fullurl)
        gm.append( e )

        gm.show_all()
        gm.popup( None, None, None, event.button, event.time)

    def _openBrowser( self, widg, text):
        '''Opens the text with an external browser.'''
        webbrowser.open_new_tab(text)

    def _sendRequest(self, widg, text, func):
        func(self.w3af, (text,""))

class ScanRunBody(gtk.Notebook):
    '''The whole body of scan run.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        super(ScanRunBody,self).__init__()
        self.w3af = w3af
        self.helpChapter = ("Browsing_the_Knowledge_Base", "Site_structure", "Requests_and_Responses")
        self.connect("switch-page", self.changedPage)

        # KB Browser
        # this one does not go inside a scrolled window, because that's handled
        # in each widget of itself
        kbbrowser = KBBrowser(w3af)
        l = gtk.Label(_("KB Browser"))
        self.append_page(kbbrowser, l)

        # urlstree, the tree
        pan = entries.RememberingHPaned(w3af, "pane-urltreegraph")
        urlsgraph = URLsGraph(w3af)
        urlstree = URLsTree(w3af, urlsgraph)
        scrollwin1 = gtk.ScrolledWindow()
        scrollwin1.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrollwin1.add_with_viewport(urlstree)
        scrollwin1.show()
        pan.pack1(scrollwin1)
        pan.pack2(urlsgraph)
        pan.show()
        l = gtk.Label("URLs")
        self.append_page(pan, l)

        # Request Response navigator
        httplog = httpLogTab.httpLogTab(w3af)
        l = gtk.Label(_("Request/Response navigator"))
        self.append_page(httplog, l)

        self.show()

    def changedPage(self, notebook, page, page_num):
        '''Changed the page in the Notebook.'''
        self.w3af.helpChapters["scanrun"] = self.helpChapter[page_num]

class IteratedURLList(object):
    '''
    Simply provide a way to access the kb.kb.getData('urls', 'url_objects')
    in an iterated manner!
     
    @author: Andres Riancho < andres.riancho @ gmail.com >
    '''
    def __init__(self):
        self._index = 0

    def get(self):
        '''Serves the elements taken from the list.'''
        while True:
            llist = kb.kb.getData('urls', 'url_objects')
            
            if self._index < len(llist):
                msg = llist[ self._index ]
                self._index += 1
                data = msg
            else:
                data = None
            
            yield data

