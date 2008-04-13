'''
web20Spider.py

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

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
import core.data.kb.knowledgeBase as kb
import core.controllers.outputManager as om
# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.data.getResponseType import *
from core.controllers.w3afException import w3afException
from core.controllers.daemons.proxy import *
from core.data.request.frFactory import createFuzzableRequestRaw
import core.data.constants.w3afPorts as w3afPorts
import time

reportedError = False

try:
    from extlib.testbrowser.src.zc.testbrowser.real import Browser
except Exception, e:
    om.out.error('You won\'t be able to use the web20Spider without zc.testbrowser.real library installed. Exception: ' + str(e) )
    
class _web20Spider(baseDiscoveryPlugin):
    '''
    A web spider with javascript support **PLUGIN UNDER DEVELOPMENT**.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )  
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Some internal variables
        self._proxyd = None
        self._browser = None
        
        # This connects to mozrepl, so the user should have mozilla running and mozrepl started
        try:
            self._browser = Browser()
        except Exception, e:
            global reportedError
            if not reportedError:
                om.out.error( str(e) + '. You can get MozRepl at http://hyperstruct.net/projects/mozlab .')
                reportedError = True
        else:
            # I want all requests to be sent to my proxy, firefox shouldn't get anything from the cache
            self._browser.clearCache()
        
        # User options
        self._proxyPort = w3afPorts.WEB20SPIDER

        
    def discover(self, fuzzableRequest ):
        '''
        Searches for javascript attributes(onClick, onMouseOver, etc) and calls them.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        try:
            # Check if the user has zc.testbrowser installed
            Browser
            # Check if I have been able to connect to mozrepl
            assert self._browser != None
        except:
            return []
        else:
            self._fuzzableRequests = []
            
            om.out.debug( 'web20Spider plugin is analyzing: ' + fuzzableRequest.getURL() )
            
            self._loadURI( fuzzableRequest.getURI() )
            jsList = self._findJs()
            for js in jsList:
                self._execJs( js )
                
                if self._browser.url != fuzzableRequest.getURI():
                    # Go back to the previous URI
                    om.out.debug('[web20Spider] The URI changed, clicking on back.')
                    self._loadURI( fuzzableRequest.getURI() )
                    
            return self._fuzzableRequests
    
    def _findJs( self ):
        '''
        Analyzes the DOM in the browser and returns a list of "tags" that are "clickable"
        '''
        # Left here for some simple tests
        #l = self._browser.getLink('Redirect to the w3af test page.')
        #linkList = [ l,]

        linkList = self._browser.getAllLinks()
        
        if len( linkList ):
            om.out.debug('[web20Spider] getAllLinks returned:')
            for i in linkList:
                om.out.debug('- ' + repr(i) )
        else:
            om.out.debug('[web20Spider] getAllLinks returned no links.')
        
        return linkList
        
    def _execJs( self, js ):
        '''
        "click" on the "tag" that is sent as parameter
        '''
        om.out.debug('[web20Spider] "Clicking" on "tag".')
        js.click()
        
    def _loadURI( self, URI ):
        '''
        Load the URI in the browser and return.
        '''
        # This call will make the browser thread load the URI
        try:
            self._browser.open( URI )
        except RuntimeError, re:
            om.out.debug('[web20Spider] ' + str(re) )
            # Let the page actually load
            time.sleep( 1 )
        except Exception, e:
            om.out.error('[web20Spider] Unhandled error: ' + str(e) )

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Local TCP port where the proxy will listen on.'
        h1 = 'This plugin embeds a browser, that is configured to browse through a local proxy server. It is done this way\
    to be able to intercept all request and responses and use all the xUrlLib configurations and features. You can safely\
    leave this setting as it is.'
        o1 = option('proxyPort', str(self._proxyPort), d1, 'integer', help=h1)
        
        ol = optionList()
        ol.add(o1)
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._proxyPort = optionsMap['proxyPort']
    
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return [ ]
            
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        **PLUGIN UNDER DEVELOPMENT**

        This plugin is a web spider on anabolics, it will search through the DOM tree of the loaded
        HTML for tags that have an onClick, onChange or onMouseOver and it will call them. The javascript
        will be executed just as if you would have *really* clicked on the link using your favorite browser.
    
        The following is a list of all configurable parameters:
            - localProxy
            
        '''
    
    def _createFuzzableRequestRaw( self, method, url, postData, headers ):
        '''
        Takes the data from a raw request, and creates the corresponding object to return 
        to w3afCore.
        '''
        freq = createFuzzableRequestRaw( method, url, postData, headers )
        self._fuzzableRequests.append( freq )
        om.out.debug('web20Spider created new fuzzable request: ' + str(freq) )
    
    #########################
    #                                                           #
    #      This is the proxy stuff                  #
    #                                                           #
    #########################
    
    def setUrlOpener( self, urlOpener ):
        self._urlOpener = urlOpener
        
        # Now, I'm starting the proxy server !
        self._proxy()
        
    def _proxy( self ):
        '''
        This method starts the proxy server with the configured options.
        '''
        self.proxyHandler._createFuzzableRequests = self._createFuzzableRequestRaw
        if self._proxyd != None and self._proxyd.isRunning():
            self._proxyd.stop()
        
        self._proxyd = proxy( '127.0.0.1', self._proxyPort , self._urlOpener, proxyHandler=self.proxyHandler )
        self._proxyd.start2()
        time.sleep(0.5)
        if self._proxyd.isRunning():
            om.out.debug('The proxy server was successfully started.')
        else:
            om.out.error('Error while starting web20Spider proxy on TCP port: ' + str(self._proxyPort) )
        
    class proxyHandler(w3afProxyHandler):
        
        def _sendToServer( self ):
            
            # Do the request to the remote server
            if self.headers.dict.has_key('content-length'):
                # POST
                cl = int( self.headers['content-length'] )
                postData = self.rfile.read( cl )
                
                # Create the fuzzable requests to be sent to w3afCore and to other plugins.
                self._createFuzzableRequests( self.command , self.path, postData, self.headers)

                try:
                    res = self._urlOpener.POST( self.path, data=postData, headers=self.headers )
                except w3afException, w:
                    om.out.error('The proxy request failed, error: ' + str(w) )
                    raise w
                except:
                    raise
                return res
                
            else:
                # GET
                url = uri2url( self.path )
                qs = getQueryString( self.path )
                
                # Create the fuzzable requests to be sent to w3afCore and to other plugins.
                self._createFuzzableRequests( self.command , self.path, qs, self.headers)

                try:
                    res = self._urlOpener.GET( url, data=str(qs), headers=self.headers )
                except w3afException, w:
                    om.out.error('The proxy request failed, error: ' + str(w) )
                    raise w
                except:
                    raise
                return res      

