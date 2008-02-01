'''
oracleDiscovery.py

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
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
import core.data.parsers.urlParser as urlParser
from core.controllers.w3afException import *
import re

class oracleDiscovery(baseDiscoveryPlugin):
    '''
    Find Oracle applications on the remote web server.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        self._exec = True

    def discover(self, fuzzableRequest ):
        '''
        GET some files and parse them.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        dirs = []
        if not self._exec :
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
            
        else:
            # Only run once
            self._exec = False
            
            self.is404 = kb.kb.getData( 'error404page', '404' )
            baseUrl = urlParser.baseUrl( fuzzableRequest.getURL() )
            
            for url, regexString in self.getOracleData():

                oracleDiscoveryUrl = urlParser.urlJoin(  baseUrl , url )
                response = self._urlOpener.GET( oracleDiscoveryUrl, useCache=True )
                
                if not self.is404( response ):
                    dirs.extend( self._createFuzzableRequests( response ) )
                    if re.match( regexString , response.getBody(), re.DOTALL):
                        i = info.info()
                        i.setURL( response.getURL() )
                        i.setDesc( self._parseFunction( url, response ) )
                        i.setId( response.id )
                        kb.kb.append( self, 'info', i )
                        om.out.information( i.getDesc() )
                    else:
                        om.out.debug('oracleDiscovery found the URL: ' + response.getURL() + ' but failed to parse it.')
                        om.out.debug('The content of the URL is: ' + response.getBody() )
        
        return dirs
    
    def _parseFunction( self, url, response ):
        '''
        This function parses responses and returns the message to be setted in the information object.
        @parameter url: The requested url
        @parameter response: The response object
        @return: A string with the message
        '''
        res = ''
        if url == '/portal/page':
            # Check if I can get the oracle version
            # <html><head><title>PPE is working</title></head><body>PPE version 1.3.4 is working.</body></html>
            if re.match( '<html><head><title>PPE is working</title></head><body>PPE version (.*?) is working\.</body></html>', response.getBody() ):
            
                version = re.findall( '<html><head><title>PPE is working</title></head><body>PPE version (.*?) is working\.</body></html>' , response.getBody() )[0]
                res = 'Oracle Parallel Page Engine version "'+ version +'" was detected at: ' + response.getURL()
            
            else:
                # I dont have the version!
                res = 'Oracle Parallel Page Engine was detected at: ' +  response.getURL()
                
        elif url == '/reports/rwservlet/showenv':
            # Example string: Reports Servlet Omgevingsvariabelen 9.0.4.2.0
            try:
                version = re.findall( 'Reports Servlet .*? (.*)' , response.getBody() )[0][:-1]
                res = 'Oracle reports version "'+version+'" was detected at: ' + response.getURL()
            except:
                om.out.error('Failed to parse the Oracle reports version from HTML: ' + response.getBody() )
                res = 'Oracle reports was detected at: ' + response.getURL()
                
        return res
    
    def getOracleData( self ):
        '''
        @return: A list of tuples with ( url, regexString, message )
        '''
        res = []
        res.append( ('/portal/page','<html><head><title>PPE is working</title></head><body>PPE .*?is working\.</body></html>') )
        res.append( ('/reports/rwservlet/showenv','.*<title>Oracle Application Server Reports Services - Servlet</title>.*') )
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

    def setOptions( self, OptionList ):
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
        return ['grep.pathDisclosure']
        
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin fetches some Oracle Application Server URLs and parses the information available on them.
        '''
