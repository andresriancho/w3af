'''
archiveDotOrg.py

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
import core.controllers.outputManager as om
import core.data.parsers.urlParser as urlParser
from core.controllers.w3afException import w3afException
import core.data.kb.knowledgeBase as kb
from core.data.parsers.dpCache import dpc as dpc
from core.data.request.httpQsRequest import httpQsRequest
from core.data.dc.dataContainer import dataContainer  
import re

class archiveDotOrg(baseDiscoveryPlugin):
    '''
    Search archive.org to find new pages in the target site.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    @author: Darren Bilby, thanks for the good idea!
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        self._alreadyVisited = []
        
        # User configured parameters
        self._maxDepth = 3

    def discover(self, fuzzableRequest ):
        '''
        Does a search in archive.org and searches for links on the html. Then searches those URLs in the
        target site. This is a time machine ! 
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        om.out.debug( 'archiveDotOrg plugin is testing: ' + fuzzableRequest.getURL() )
        self.is404 = kb.kb.getData( 'error404page', '404' )
        
        # Init some internal variables
        res = []
        
        startURL = 'http://web.archive.org/web/*/' + fuzzableRequest.getURL()
        domain = urlParser.getDomain( fuzzableRequest.getURL() )
        references = self._spiderArchive( [ startURL, ] , self._maxDepth, domain )
        
        # Translate archive.org URL's to normal URL's
        referencesURL = []
        for url in references:
            try:
                url = url[url.index('http',1):]
            except:
                pass
            else:
                referencesURL.append( url )
        referencesURL = list(set(referencesURL))
        
        if len( referencesURL ):
            om.out.debug('Archive.org cached the following pages:')
            for r in referencesURL:
                om.out.debug('- ' + r )
        else:
            om.out.debug('Archive.org did not find any pages.')
        
        # Verify if they exist in the target site and add them to the result if they do.
        for ru in referencesURL:
            if self._existsInTarget( ru ):
                QSObject = urlParser.getQueryString( ru )
                qsr = httpQsRequest()
                qsr.setURI( ru )
                qsr.setDc( QSObject )
                res.append( qsr )

        if len( res ):
            om.out.debug('The following pages are in Archive.org cache and also in the target site:')
            for r in res:
                om.out.debug('- ' + r.getURI() )
        else:
            om.out.debug('All pages found in archive.org cache are missing in the target site.')
            
        return res
    
    def _spiderArchive( self, urlList, maxDepth, domain ):
        '''
        Here I perform a web Spidering with searchURL as a parameter.
        The idea is to configure the webSpider so it can have a regex as a config parameter that says what URLs
        to navigate and what not to.
        After getting the result, I should filter the URLs and change them back to the original ones
        and check them against the original site.
        '''
        # Start the recursive spidering         
        res = []
        
        for url in urlList:
            if url not in self._alreadyVisited:
                self._alreadyVisited.append( url )
                
                try:
                    httpRes = self._urlOpener.GET( url, useCache=True )
                except:
                    pass
                else:
                    # Get the references
                    docuParser = dpc.getDocumentParserFor( httpRes.getBody(), httpRes.getURL() )
                    references = docuParser.getReferences()
                    
                    # Filter the ones I want
                    url = 'http[s]?://' + domain + '/'
                    newUrls = [ u for u in references if re.match('http://web\.archive\.org/web/.*/' + url + '.*', u ) ]
                    
                    # Go recursive
                    if maxDepth -1 > 0:
                        if newUrls:
                            res.extend( newUrls )
                            res.extend( self._spiderArchive( newUrls, maxDepth -1, domain ) )
                    else:
                        om.out.debug('Some sections of the archive.org site were not analyzed because of the configured maxDepth.')
                        return newUrls
        
        return res
    
    def _existsInTarget( self, url ):
        res = False
        
        try:
            response = self._urlOpener.GET( url, useCache=True )
        except KeyboardInterrupt,e:
            raise e
        except w3afException,e:
            pass
        else:
            if not self.is404( response ):
                res = True
        
        if res:
            om.out.debug('The URL: ' + url + ' was found at archive.org and is STILL AVAILABLE in the target site.')
        else:
            om.out.debug('The URL: ' + url + ' was found at archive.org and was DELETED from the target site.')
        
        return res
            
    def getOptionsXML(self):
        '''
        This method returns a XML containing the Options that the plugin has.
        Using this XML the framework will build a window, a menu, or some other input method to retrieve
        the info from the user. The XML has to validate against the xml schema file located at :
        w3af/core/ui/userInterface.dtd
        
        @return: XML with the plugin options.
        ''' 
        return  '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <OptionList>\
        </OptionList>\
        '

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptionsXML().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass
        
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return [ 'discovery.allowedMethods' ]
            
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin does a search in archive.org and parses the results. It then uses the results to find new
        URLs in the target site. This plugin is a time machine !    
        '''
