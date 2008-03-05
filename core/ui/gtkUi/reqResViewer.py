'''
reqResViewer.py

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
import gobject
import core.data.kb.knowledgeBase as kb
import core.controllers.outputManager as om
import re
from core.ui.gtkUi.entries import ValidatedEntry

useMozilla = False
useGTKHtml2 = True

try:
    import gtkmozembed
    withMozillaTab = True
except Exception, e:
    withMozillaTab = False

try:
    import gtkhtml2
    withGtkHtml2 = True
except Exception, e:
    withGtkHtml2 = False
   
class reqResViewer(gtk.HPaned):
    '''
    A VPaned with the request and the response inside.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self):
        super(reqResViewer,self).__init__()
        
        # Create the result viewer
        resultNotebook = gtk.Notebook()
        # Create the request viewer
        requestNotebook = gtk.Notebook()
        
        # Create the HTML renderer
        renderWidget = None
        if (withMozillaTab and useMozilla) or (withGtkHtml2 and useGTKHtml2):
            swRenderedHTML = gtk.ScrolledWindow()
            renderedLabel = gtk.Label("Rendered response")
            
            if withMozillaTab and useMozilla:
                renderWidget = gtkmozembed.MozEmbed()
            if withGtkHtml2 and useGTKHtml2:
                renderWidget = gtkhtml2.View()
                
            swRenderedHTML.add(renderWidget)
        
        # Create the objects that go inside the request and the response...
        reqLabel = gtk.Label("Request")
        self.request = requestPaned()
        resLabel = gtk.Label("Response")
        self.response = responsePaned(renderWidget)
        
        # Add all to the notebook
        requestNotebook.append_page(self.request, reqLabel)
        self.pack1(requestNotebook)
        resultNotebook.append_page(self.response, resLabel)
        
        if (withMozillaTab and useMozilla) or (withGtkHtml2 and useGTKHtml2):
            resultNotebook.append_page(swRenderedHTML, renderedLabel)
            
        self.pack2(resultNotebook)
        self.set_position(400)
        self.show_all()

class requestResponsePaned:
    def __init__( self ):
        # The textview where a part of the req/res is showed
        self._upTv = gtk.TextView()
        self._upTv.set_border_width(5)
        
        # Scroll where the textView goes
        sw1 = gtk.ScrolledWindow()
        sw1.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw1.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        
        # The textview where a part of the req/res is showed (this is for postdata and response body)
        self._downTv = gtk.TextView()
        self._downTv.set_border_width(5)
        
        # Scroll where the textView goes
        sw2 = gtk.ScrolledWindow()
        sw2.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw2.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        
        # Add everything to the scroll views
        sw1.add(self._upTv)
        sw2.add(self._downTv)
        
        # vertical pan (allows resize of req/res texts)
        vpan = gtk.VPaned()
        ### TODO: This should be centered
        vpan.set_position( 200 )
        vpan.pack1( sw1 )
        vpan.pack2( sw2 )
        vpan.show_all()
        
        self.add( vpan )
        
    def _clear( self, textView ):
        '''
        Clears a text view.
        '''
        buffer = textView.get_buffer()
        start, end = buffer.get_bounds()
        buffer.delete(start, end)
        
class requestPaned(gtk.HPaned, requestResponsePaned):
    def __init__(self):
        gtk.HPaned.__init__(self)
        requestResponsePaned.__init__( self )
        
    def show( self, method, uri, version, headers, postData ):
        '''
        Show the data in the corresponding order in self._upTv and self._downTv
        '''
        # Clear previous results
        self._clear( self._upTv )
        self._clear( self._downTv )
        
        buffer = self._upTv.get_buffer()
        iter = buffer.get_end_iter()
        buffer.insert( iter, method + ' ' + uri + ' ' + 'HTTP/' + version + '\n')
        buffer.insert( iter, headers )
        
        buffer = self._downTv.get_buffer()
        iter = buffer.get_end_iter()
        buffer.insert( iter, postData )
    
class responsePaned(gtk.HPaned, requestResponsePaned):
    def __init__(self, renderingWidget):
        gtk.HPaned.__init__(self)
        requestResponsePaned.__init__( self )
        self._renderingWidget = renderingWidget
        
    def show( self, version, code, msg, headers, body, baseURI ):
        '''
        Show the data in the corresponding order in self._upTv and self._downTv
        '''
        # Clear previous results
        self._clear( self._upTv )
        self._clear( self._downTv )

        buffer = self._upTv.get_buffer()
        iter = buffer.get_end_iter()
        buffer.insert( iter, 'HTTP/' + version + ' ' + str(code) + ' ' + str(msg) + '\n')
        buffer.insert( iter, headers )
        
        buffer = self._downTv.get_buffer()
        iter = buffer.get_end_iter()
        buffer.insert( iter, body )
        
        # Get the mimeType from the response headers
        mimeType = 'text/html'
        headers = headers.split('\n')
        for h in headers:
            if 'content-type' in h.lower():
                h_name, h_value = h.split(':')
                mimeType = h_value.strip()
                break
        
        ### TODO: Make this work FOR REAL!!!
        if mimeType not in ['text/html']:
            mimeType = 'text/html'
        
        # Show it rendered
        if withGtkHtml2 and useGTKHtml2:
            document = gtkhtml2.Document()
            document.clear()
            document.open_stream(mimeType)
            document.write_stream(body)
            document.close_stream()
            self._renderingWidget.set_document(document)
        
        if withMozillaTab and useMozilla:
            self._renderingWidget.render_data( body,long(len(body)), baseURI , mimeType)
