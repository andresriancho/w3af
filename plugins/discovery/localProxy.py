'''
localProxy.py

Copyright 2006 Andres Riancho

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


import core.controllers.outputManager as om
from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.controllers.w3afException import w3afException
from core.controllers.w3afException import w3afRunOnce
from core.controllers.daemons.proxy import *
import core.data.parsers.urlParser as urlParser
import cgi , urllib
from core.controllers.basePlugin.baseManglePlugin import *
import core.data.constants.w3afPorts as w3afPorts

import re

class localProxy(baseDiscoveryPlugin):
    '''
    Local proxy for HTTP requests ( like paros ).
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._proxyd = None
        
        # User options
        self._userOptionfixContentLen = True
        self._interceptRegex = re.compile('.*')
        self._interceptImages = False
        self._w3afMarker = 'w3afMarker'
        self._proxyAddress = '127.0.0.1'
        self._proxyPort = w3afPorts.LOCALPROXY
        self._css = 'plugins' + os.path.sep + 'discovery' + os.path.sep + 'localProxy' + os.path.sep +'default.css'
    
    def setUrlOpener( self, urlOpener ):
        self._urlOpener = urlOpener
        
        # Now, I'm starting the proxy server !
        self._proxy()
    
    def discover(self, fuzzableRequest ):
        '''
        Do nothing, this plugin is rather odd, cause it will never return new URIs to the core.
        This plugin is a local proxy server thats used for mangling requests. All the "magic" is done
        in the _proxy method and in the handler class.
        '''
        
        # All i need to run is runned from setUrlOpener and setOptions
        # All i need to run is self._proxy() with the correct parameters
        raise w3afRunOnce()
        
    def setOptions( self, OptionsMap ):
        
        self._userOptionfixContentLen = OptionsMap['fixContentLen']
        self._interceptImages = OptionsMap['interceptImages']
        try:
            self._interceptRegex = re.compile( OptionsMap['interceptRegex'] )
        except:
            raise w3afException('Invalid regular expression in parameter interceptRegex.')
        
        self._w3afMarker = OptionsMap['w3afMarker']
        self._proxyPort = OptionsMap['proxyPort']
        self._proxyAddress = OptionsMap['proxyAddress']
        self._css = OptionsMap['css']
        
        # Restart the proxy, with the new options
        self._proxy()
    
    class proxyHandler(w3afProxyHandler):
        
        imageExtensions = ['css','jpg', 'jpeg', 'gif', 'png', 'svg', 'ico', 'pgm' , 'tif', 'tiff', 'bmp', 'flv']
        
        def _isImage( self, uri ):
            for i in self.imageExtensions:
                if uri.endswith( i ):
                    return True
            return False
        
        def _mustBeEdited( self ):
            
            marker = True
            self._postData = ''
            if self.headers.dict.has_key('content-length'):
                cl = int( self.headers['content-length'] )
                self._postData = self.rfile.read( cl )
                qs = urlParser.getQueryString( 'http://a/b?' + self._postData )
                if self._w3afMarker in qs:
                    marker = False
            
            return marker and self._interceptRegex.match( self.path )

        def doAll( self ):
            
            if ( self._isImage( self.path ) and not self._interceptImages ) or not self._interceptRegex.match( self.path ):
                om.out.debug('The URL: '+ self.path +' is sent directly to the server it MUST NOT be edited')
                try:
                    res = self._sendToServer()
                except Exception, e:
                    self._sendError( e )
                else:
                    self._sendToBrowser( res )
            
            elif self._mustBeEdited():
                # The URL hasnt been edited yet AND it MUST be edited
                # Return the data to the browser for editing
                res = self._editWithBrowser()
                
            else:
                # The URL was edited and we are ready to send the data to the server
                # We remove the w3afMarker before sending.
                self._sendEditedRequest()
        
        def _sendEditedRequest( self ):
            try:
                qs = urlParser.getQueryString( self._postData )
                qs.pop( self._w3afMarker )
            except:
                pass
            else:
                self._postData = str(qs)
            
            # The URI is now in self.path
            # The method is in the postData, I always get here after a POST from the form
            # created in editWithBrowser()
            qs = urlParser.getQueryString( 'http://a/b?' + self._postData )
            request = qs['request']
            request = urllib.unquote_plus( request )
            
            try:
                requestLine = request.split('\n')[0]
                method = requestLine.split(' ')[0]
                
                request = request.replace( requestLine + '\n', '' )
                
                headers = stringToHeaders( request.split('\n\n')[0] )
                try: headers.pop( 'proxy-connection' )
                except: pass
                editedPostData = '\n\n'.join( request.split('\n\n')[1:] )
            except:
                self._sendError( 'Malformed request to localProxy.' )
            else:
                try:
                    # Send the request to the remove webserver
                    res = self._mySendToServer( method, self.path, headers , editedPostData )
                except Exception, e:
                    self._sendError( e )
                else:
                    self._sendToBrowser( res )
        
        do_GET = do_POST = do_HEAD = doAll
        
        def _mySendToServer( self, method, URI, headers, postData='' ):
            '''
            Send a request to the server.
            '''
            om.out.debug('Requesting ' + self.path + ' to server.')
            
            # The content-length is removed to be recalculated inside:
            # functionReference( URI, data=postData, headers=headers )
            if 'content-length' in headers:
                del headers['content-length']
                
            try:
                functionReference = getattr( self._urlOpener , method )
            except:
                self._sendError( 'Unknown method: ' + method )
            else:
                response = functionReference( URI, data=postData, headers=headers )
                return response
            
            
        def _editWithBrowser( self ):
            '''
            This method returns an HTML form to the user, where he can edit the request to the
            remote webserver.
            '''
            om.out.debug('Editing ' + self.path + ' with browser.')
            
            self.send_response( 200 )
            self.send_header( 'Content-type', 'text/html')
            self.send_header( 'Connection', 'close')
            
            self.end_headers()
            
            action = self.path
            
            request = self.requestline + '\n'
            request += cgi.escape( headersToString( self.headers ) ) + '\n\n'
            request += self._postData
            
            rows = request.count('\n')
            
            script = '''  <SCRIPT LANGUAGE="JavaScript">
            <!--
            function changeAction() {
            document.requestForm.action = document.requestForm.request.value.split(" ")[1];
            }
            
            function countLines(strtocount, cols) {
                var lines = 1;
                var last = 0;
                while ( true ) {
                    newLast = strtocount.indexOf("\\n", last+1);
                    lines ++;

                    if ( newLast <= -1 ){
                        break;
                    }
                    else{
                        lines += Math.round( (newLast - last) / (cols-1));
                        last = newLast;
                    }
                    
                }
                return lines;
            }
            
            function cleanForm() {
                var the_form = document.requestForm;
                for ( var x in the_form ) {
                    if ( ! the_form[x] ) continue;
                    if( typeof the_form[x].rows != "number" ) continue;
                    the_form[x].rows = countLines(the_form[x].value,the_form[x].cols) +1;
                }
                setTimeout("cleanForm();", 300);
            }
            // -->
            </SCRIPT>'''
            
            style = '<style type="text/css"><!--' + file( self._css ).read() +'--></style>'
            
            self.wfile.write( '<html><head><title>Local Proxy - Request Editor</title>'+ script + style
            +'</head><body onload="cleanForm();"><h1>Request Editor</h1><div align="center"><form name="requestForm" Method="POST" Action="'+ cgi.escape( action )
            +'"><TEXTAREA name="request" onChange="changeAction();" rows="'+str(rows)+'" cols="90">'+ cgi.escape( request )
            +'</TEXTAREA><input type="hidden" name="'+ self._w3afMarker
            +'"><br/><INPUT Type="submit" Value="Send Request"></form></div></body></html>' )
            self.wfile.close()
        
    def _proxy( self ):
        '''
        This method starts the proxy server with the configured options.
        '''
        if self._proxyd != None and self._proxyd.isRunning():
            self._proxyd.stop()
        
        # Pass some parameters to the handler
        self.proxyHandler._interceptRegex = self._interceptRegex
        self.proxyHandler._w3afMarker = self._w3afMarker
        self.proxyHandler._css = self._css
        self.proxyHandler._interceptImages = self._interceptImages
        
        self._proxyd = proxy( self._proxyAddress, self._proxyPort , self._urlOpener, proxyHandler=self.proxyHandler )
        self._proxyd.start2()
        
    def getOptionsXML(self):
        '''
        This method returns a XML containing the Options that the plugin has.
        Using this XML the framework will build a window, a menu, or some other input method to retrieve
        the info from the user. The XML has to validate against the xml schema file located at :
        w3af/core/output.xsd
        '''
        return  '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <OptionList>\
            <Option name="proxyPort">\
                <default>'+str(self._proxyPort)+'</default>\
                <desc>Local TCP port where the proxy will listen on.</desc>\
                <type>integer</type>\
            </Option>\
            <Option name="proxyAddress">\
                <default>'+str(self._proxyAddress)+'</default>\
                <desc>Local IP Address where the proxy will listen on.</desc>\
                <type>string</type>\
            </Option>\
            <Option name="fixContentLen">\
                <default>'+str(self._userOptionfixContentLen)+'</default>\
                <desc>Fix the content length header after mangling</desc>\
                <type>boolean</type>\
            </Option>\
            <Option name="interceptRegex">\
                <default>.*</default>\
                <desc>Regular expression that defines what requests will be intercepted</desc>\
                <help>This regular expression is applied only to the URI part of the request.</help>\
                <type>string</type>\
            </Option>\
            <Option name="interceptImages">\
                <default>'+str(self._interceptImages)+'</default>\
                <desc>Indicate if images are going to be intercepted or not.</desc>\
                <type>boolean</type>\
            </Option>\
            <Option name="w3afMarker">\
                <default>'+self._w3afMarker+'</default>\
                <desc>This option sets the w3afMarker that is going to be used internally to identify requests that have been already mangled.</desc>\
                <help>In most cases, this should be left as it is.</help>\
                <type>string</type>\
            </Option>\
            <Option name="css">\
                <default>'+self._css+'</default>\
                <desc>CSS filename to use while editing request with the browser</desc>\
                <type>string</type>\
            </Option>\
        </OptionList>\
        '

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin is a local proxy ( like paros proxy ).
        
        Seven configurable parameters exist:
            - proxyPort
            - proxyAddress
            - fixContentLen
            - interceptRegex
            - interceptImages
            - w3afMarker
            - css
        
        This plugin is usefull for manual testing, when this plugin is enabled a proxy server is runned, the
        w3af user should configure that proxy on their browser and navigate the site changing the parameters
        on the fly.
        '''
