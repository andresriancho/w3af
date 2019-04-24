"""
scanrun.py

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
import gtk
import gobject
import urllib2
import sys
import re
import Queue
import webkit
import webbrowser

from multiprocessing.dummy import Process, Event
from markdown import markdown

from w3af.core.ui.gui import httpLogTab, entries
from w3af.core.ui.gui.reqResViewer import ReqResViewer
from w3af.core.ui.gui.kb.kbtree import KBTree
from w3af.core.ui.gui.tools.fuzzy_requests import FuzzyRequests
from w3af.core.ui.gui.tools.manual_requests import ManualRequests
from w3af.core.ui.gui.misc.xdot_wrapper import WrappedDotWidget

from w3af.core.data.db.history import HistoryItem
from w3af.core.data.kb.info import Info
from w3af.core.data.kb.kb_observer import KBObserver
from w3af.core.controllers.exceptions import DBException

import w3af.core.data.kb.knowledge_base as kb

RECURSION_LIMIT = sys.getrecursionlimit() - 5
RECURSION_MSG = "Recursion limit: can't go deeper"

DB_VULN_NOT_FOUND = markdown('The detailed description for this vulnerability'
                             ' is not available in our database, please'
                             ' contribute to the open source'
                             ' [vulndb/data project](https://github.com/vulndb/data)'
                             ' to improve w3af\'s output.')

FILE = 'file:///'


class FullKBTree(KBTree):
    def __init__(self, w3af, kbbrowser, ifilter):
        """A tree showing all the info.

        This also gives a long description of the element when clicked.

        :param kbbrowser: The KB Browser
        :param ifilter: The filter to show which elements

        :author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
        """
        super(FullKBTree, self).__init__(w3af, ifilter,
                                         'Knowledge Base', strict=False)
        self._historyItem = HistoryItem()
        self.kbbrowser = kbbrowser
        self.connect('cursor-changed', self._show_desc)
        self.show()

    def _create_reference_list(self, info):
        """
        :return: A list with references for this info instance in markdown
                 format so I can add them to the description.
        """
        if not info.get_references():
            return ''

        output = '\n\n### References\n'
        for ref in info.get_references():
            output += ' * [%s](%s)\n' % (ref.title, ref.url)

        return output

    def _show_desc(self, tv):
        """Shows the description in the right section

        :param tv: the treeview.
        """
        (path, column) = tv.get_cursor()
        if path is None:
            return

        instance = self.get_instance(path)
        if not isinstance(instance, Info):
            return
        
        summary = instance.get_desc()
        self.kbbrowser.explanation.set_text(summary)
        self.kbbrowser.vuln_notebook.set_current_page(0)

        if instance.has_db_details():
            desc_markdown = instance.get_long_description()
            desc_markdown += '\n\n### Fix guidance\n'
            desc_markdown += instance.get_fix_guidance()
            desc_markdown += self._create_reference_list(instance)
            desc = markdown(desc_markdown)

            self.kbbrowser.description.load_html_string(desc, FILE)
        else:
            self.kbbrowser.description.load_html_string(DB_VULN_NOT_FOUND, FILE)

        if not instance.get_id():
            self.clear_request_response_viewer()
            return

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
        if len(instance.get_id()) == 1:
            # There is ONLY ONE id related to the object
            # This is 1)
            self.kbbrowser.pagesControl.deactivate()
            self.kbbrowser.page_change(0)
            self.kbbrowser.pagesControl.hide()
            self.kbbrowser.title0.hide()

            search_id = instance.get_id()[0]
            try:
                history_item = self._historyItem.read(search_id)
            except DBException:
                msg = _('The HTTP data with id %s is not inside the database.')
                self._show_message(_('Error'), msg % search_id)
                self.clear_request_response_viewer()
                return

            # Error handling for .trace file problems
            # https://github.com/andresriancho/w3af/issues/1174
            try:
                # These lines will trigger the code that reads the .trace file
                # from disk and if they aren't there an exception will rise
                history_item.request
                history_item.response
            except IOError, ioe:
                self._show_message(_('Error'), str(ioe))
                return

            # Now we know that these two lines will work and we won't trigger
            # https://github.com/andresriancho/w3af/issues/1174
            self.kbbrowser.rrV.request.show_object(history_item.request)
            self.kbbrowser.rrV.response.show_object(history_item.response)

            # Don't forget to highlight if necessary
            severity = instance.get_severity()
            for s in instance.get_to_highlight():
                self.kbbrowser.rrV.response.highlight(s, severity)

        else:
            # There are MORE THAN ONE ids related to the object
            # This is 2)
            self.kbbrowser.pagesControl.show()
            self.kbbrowser.title0.show()

            self.kbbrowser.req_res_ids = instance.get_id()
            num_ids = len(instance.get_id())
            self.kbbrowser.pagesControl.activate(num_ids)
            self.kbbrowser.page_change(0)

        self.kbbrowser.rrV.set_sensitive(True)

    def clear_request_response_viewer(self):
        self.kbbrowser.rrV.request.clear_panes()
        self.kbbrowser.rrV.response.clear_panes()
        self.kbbrowser.rrV.set_sensitive(False)

    def _show_message(self, title, msg, gtkLook=gtk.MESSAGE_WARNING):
        """Show message to user as GTK dialog."""
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtkLook,
                                gtk.BUTTONS_OK, msg)
        dlg.set_title(title)
        dlg.run()
        dlg.destroy()


class KBBrowser(entries.RememberingHPaned):
    """Show the Knowledge Base, with the filter and the tree.

    :author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    """
    def __init__(self, w3af):
        super(KBBrowser, self).__init__(w3af, "pane-kbbrowser", 250)

        # Internal variables:
        # Save the request and response ids to be used in the page control
        self.req_res_ids = []
        # This is to search the DB and print the different request and responses
        # as they are requested from the page control, "page_change" method.
        self._historyItem = HistoryItem()

        # the filter to the tree
        filterbox = gtk.HBox()
        self.filters = {}

        def make_but(label, signal, initial):
            but = gtk.CheckButton(label)
            but.set_active(initial)
            but.connect('clicked', self.type_filter, signal)
            self.filters[signal] = initial
            but.show()
            filterbox.pack_start(but, expand=False, fill=False, padding=2)
        make_but('Vulnerability', 'vuln', True)
        make_but('Information', 'info', True)
        filterbox.show()

        # the kb tree
        self.kbtree = FullKBTree(w3af, self, self.filters)

        # all in the first pane
        kbtree_scrollwin = gtk.ScrolledWindow()
        kbtree_scrollwin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        kbtree_scrollwin.add(self.kbtree)
        kbtree_scrollwin.show()

        # the filter and tree box
        treebox = gtk.VBox()
        treebox.pack_start(filterbox, expand=False, fill=False)
        treebox.pack_start(kbtree_scrollwin)
        treebox.show()

        # the vulnerability information
        summary = self.get_notebook_summary(w3af)
        description = self.get_notebook_description()

        self.vuln_notebook = gtk.Notebook()
        self.vuln_notebook.append_page(summary, gtk.Label('Summary'))
        self.vuln_notebook.append_page(description, gtk.Label('Description'))
        self.vuln_notebook.set_current_page(0)
        self.vuln_notebook.show()

        # pack & show
        self.pack1(treebox)
        self.pack2(self.vuln_notebook)
        self.show()

    def get_notebook_description(self):
        # Make the HTML viewable area

        self.description = webkit.WebView()

        # Disable the plugins for the webview
        ws = self.description.get_settings()
        ws.set_property('enable-plugins', False)
        self.description.set_settings(ws)
        self.description.show()

        desc_scroll = gtk.ScrolledWindow()
        desc_scroll.add(self.description)
        desc_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        desc_scroll.show()

        return desc_scroll

    def get_notebook_summary(self, w3af):
        summary_tv = gtk.TextView()
        summary_tv.set_editable(False)
        summary_tv.set_cursor_visible(False)
        summary_tv.set_wrap_mode(gtk.WRAP_WORD)
        self.explanation = summary_tv.get_buffer()
        summary_tv.show()

        summary_scrollwin = gtk.ScrolledWindow()
        summary_scrollwin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        summary_scrollwin.add_with_viewport(summary_tv)
        summary_scrollwin.show()

        # The request/response viewer
        self.rrV = ReqResViewer(w3af, withAudit=False)
        self.rrV.set_sensitive(False)

        # Create the title label to show the request id
        self.title0 = gtk.Label()
        self.title0.show()

        # Create page changer to handle info/vuln objects that have MORE THAN
        # ONE related request/response
        self.pagesControl = entries.PagesControl(w3af, self.page_change, 0)
        self.pagesControl.deactivate()
        self.page_change(0)
        center_box = gtk.HBox()
        center_box.pack_start(self.pagesControl, True, False)

        # Title, request/response and paginator all go together in a vbox
        http_data_vbox = gtk.VBox()
        http_data_vbox.pack_start(self.title0, False, True)
        http_data_vbox.pack_start(self.rrV, True, True)
        http_data_vbox.pack_start(center_box, False, False)

        # and show
        http_data_vbox.show()
        self.pagesControl.show()
        center_box.show()

        # The summary and http data go in a vbox too
        summary_data_vbox = entries.RememberingVPaned(w3af,
                                                      'pane-kbbexplainview',
                                                      100)
        summary_data_vbox.pack1(summary_scrollwin)
        summary_data_vbox.pack2(http_data_vbox)
        summary_data_vbox.show()

        return summary_data_vbox

    def type_filter(self, button, ptype):
        """Changes the filter of the KB in the tree."""
        self.filters[ptype] = button.get_active()
        self.kbtree.set_filter(self.filters)

    def page_change(self, page):
        """
        Handle the page change in the page control.
        """
        # Only do something if I have a list of request and responses
        if self.req_res_ids:
            request_id = self.req_res_ids[page]
            try:
                historyItem = self._historyItem.read(request_id)
            except:
                # the request brought problems
                self.rrV.request.clear_panes()
                self.rrV.response.clear_panes()
                self.rrV.set_sensitive(False)
                self.title0.set_markup("<b>Error</b>")
            else:
                self.title0.set_markup("<b>Id: %d</b>" % request_id)
                self.rrV.request.show_object(historyItem.request)
                self.rrV.response.show_object(historyItem.response)
                self.rrV.set_sensitive(True)


class URLsGraph(gtk.VBox):
    """Graph the URLs that the system discovers.

    :author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    """
    def __init__(self, w3af):
        super(URLsGraph, self).__init__()
        self.w3af = w3af

        self.toolbox = gtk.HBox()
        b = entries.SemiStockButton("", gtk.STOCK_ZOOM_IN, 'Zoom In')
        b.connect('clicked', self._zoom, "in")
        self.toolbox.pack_start(b, False, False)
        b = entries.SemiStockButton("", gtk.STOCK_ZOOM_OUT, 'Zoom Out')
        b.connect('clicked', self._zoom, "out")
        self.toolbox.pack_start(b, False, False)
        b = entries.SemiStockButton("", gtk.STOCK_ZOOM_FIT, 'Zoom Fit')
        b.connect('clicked', self._zoom, "fit")
        self.toolbox.pack_start(b, False, False)
        b = entries.SemiStockButton("", gtk.STOCK_ZOOM_100, 'Zoom 100%')
        b.connect('clicked', self._zoom, "100")
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
        f = getattr(self.widget, "on_zoom_" + what)
        f(None)

    def _draw_start(self):
        if not self._somethingnew:
            return True

        # let's draw!
        q = Queue.Queue()
        evt = Event()
        th = Process(target=self._draw_real, args=(q, evt), name='GTKDraw')
        th.start()
        gobject.timeout_add(500, self._draw_end, q, evt)
        return False

    def _draw_real(self, q, evt):
        new_widget = WrappedDotWidget()
        self._somethingnew = False
        dotcode = "graph G {%s}" % "\n".join(self.nodos_code)
        
        try:
            new_widget.set_dotcode(dotcode)
        except ValueError, ve:
            msg = ('A ValueError exception with message "%s" was found while'
                   ' trying to render a new dotcode. Please create a new'
                   ' bug report at %s including the following info:\n\n%s')
            new_issue = 'https://github.com/andresriancho/w3af/issues/new'
            args = (ve, new_issue, dotcode)
            raise ValueError(msg % args)
        else:
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

    def limit_node(self, parent, node, name):
        # I have to escape the quotes, because I don't want a "dot code
        # injection". This was sourceforge bug #2675512
        node = str(node).replace('"', '\\"')
        name = str(name).replace('"', '\\"')

        self.nodos_code.append('"%s" [label="%s"]' % (node, name))
        if parent:
            parent = str(parent).replace('"', '\\"')
            nline = '"%s" -- "%s"' % (parent, node)
            self.nodos_code.append(nline)
        self._somethingnew = True

    def new_node(self, parent, node, name, isLeaf):
        # I have to escape the quotes, because I don't want a "dot code
        # injection" This was bug #2675512
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
User-Agent: w3af.org
"""


class URLObserver(KBObserver):
    def __init__(self, urls_tree):
        self.urls_tree = urls_tree

    def add_url(self, url):
        self.urls_tree.urls.put(url)


class URLsTree(gtk.TreeView):
    """Show the URLs that the system discovers.

    :author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    """
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
        self.urls = Queue.Queue()
        kb.kb.add_observer(URLObserver(self))
        gobject.timeout_add(250, self.add_url)
        self.show()

    def _doubleClick(self, widg, event):
        """If double click, expand/collapse the row."""
        if event.type == gtk.gdk._2BUTTON_PRESS:
            path = self.get_cursor()[0]
            # This "if path" fixed bug #2205544
            if path:
                if self.row_expanded(path):
                    self.collapse_row(path)
                else:
                    self.expand_row(path, False)

    def add_url(self):
        """Adds periodically the new URLs to the tree.

        :return: True to keep being called by gobject, False when it's done.
        """
        try:
            url = self.urls.get_nowait()
        except Queue.Empty:
            pass
        else:
            path = url.get_path()
            params = url.get_params_string()
            query = str(url.querystring)
            fragment = url.get_fragment()
            scheme = url.get_protocol()
            netloc = url.get_domain()

            ini = "%s://%s" % (scheme, netloc)
            end = ""
            if params:
                end += ";" + params
            if query:
                end += "?" + query
            if fragment:
                end += "#" + fragment

            splittedPath = re.split('(\\\\|/)', path)
            nodes = []
            for i in splittedPath:
                if i not in ['\\', '/']:
                    nodes.append(i)

            nodes.insert(0, ini)
            nodes.append(end)
            parts = [x for x in nodes if x]
            
            self._insertNodes(None, parts, self.treeholder, 1)

            # TODO: Automatically sort after each insertion
            # Order the treeview
            self.treestore.sort_column_changed()
        
        return True

    def _insertNodes(self, parent, parts, holder, rec_cntr):
        """Insert a new node in the tree.

        It's recursive: it walks the path of nodes, being each node a
        part of the URL, checking every time if needs to create a new
        node or just enter in it.

        :param parent: the parent to insert the node
        :param parts: the rest of the parts to walk the path
        :param holder: the dict when what is already exists is stored.
        :param rec_cntr: the recursion counter

        :return: The new or modified holder
        """
        if not parts:
            return {}
        node = parts[0]
        rest = parts[1:]

        if rec_cntr >= RECURSION_LIMIT:
            newtreenode = self.treestore.append(parent, [RECURSION_MSG])
            self.grapher.limit_node(parent, newtreenode, RECURSION_MSG)
            return holder

        if node in holder:
            # already exists, use it if have more nodes
            (treenode, children) = holder[node]
            return self._insertNodes(treenode, rest, children, rec_cntr + 1)

        # does not exist, create it
        newtreenode = self.treestore.append(parent, [node])
        self.grapher.new_node(parent, newtreenode, node, not rest)
        newholdnode = self._insertNodes(newtreenode, rest, {}, rec_cntr + 1)
        holder[node] = (newtreenode, newholdnode)
        return holder

    def popup_menu(self, tv, event):
        """Shows a menu when you right click on a URL in the treeview.

        :param tv: the treeview.
        :param event: The GTK event
        """
        if event.button != 3:
            return

        (path, column) = tv.get_cursor()
        # Is it over a URL?
        if path is None:
            return

        # Get the information about the click
        fullurl = "/".join(
            self.treestore[path[:i + 1]][0] for i in range(len(path)))
        host = urllib2.urlparse.urlparse(fullurl)[1]
        sendtext = HEAD_TO_SEND % (fullurl, host)

        gm = gtk.Menu()

        e = gtk.ImageMenuItem(_("Open with Manual Request Editor..."))
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_INDEX, gtk.ICON_SIZE_MENU)
        e.set_image(image)
        e.connect('activate', self._send_request, sendtext,
                  ManualRequests)
        gm.append(e)

        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_PROPERTIES, gtk.ICON_SIZE_MENU)
        e = gtk.ImageMenuItem(_("Open with Fuzzy Request Editor..."))
        e.set_image(image)
        e.connect('activate', self._send_request, sendtext,
                  FuzzyRequests)
        gm.append(e)

        e = gtk.ImageMenuItem(_("Open with default browser..."))
        e.connect('activate', self._open_browser, fullurl)
        gm.append(e)

        gm.show_all()
        gm.popup(None, None, None, event.button, event.time)

    def _open_browser(self, widg, text):
        """Opens the text with an external browser."""
        webbrowser.open_new_tab(text)

    def _send_request(self, widg, text, func):
        func(self.w3af, (text, ""))


class ScanRunBody(gtk.Notebook):
    """The whole body of scan run.

    :author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    """
    def __init__(self, w3af):
        super(ScanRunBody, self).__init__()
        self.w3af = w3af
        self.helpChapter = ("Browsing_the_Knowledge_Base",
                            "Site_structure", "Requests_and_Responses")
        self.connect("switch-page", self.changed_page)

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

    def changed_page(self, notebook, page, page_num):
        """Changed the page in the Notebook."""
        self.w3af.helpChapters["scanrun"] = self.helpChapter[page_num]
