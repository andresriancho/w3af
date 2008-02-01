'''
dav.py

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

from core.data.fuzzer.fuzzer import *
import core.controllers.outputManager as om
from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
import core.data.kb.knowledgeBase as kb
from core.controllers.w3afException import w3afException
import core.data.kb.vuln as vuln
import core.data.parsers.urlParser as urlParser
import core.data.constants.severity as severity

class dav(baseAuditPlugin):
    '''
    Tries to upload a file using HTTP PUT method.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        # Internal variables
        self.is404 = None
        self._alreadyTested = []
        self._rand = createRandAlpha( 5 )

    def _fuzzRequests(self, freq ):
        '''
        Searches for file upload vulns using PUT method.
        
        @param freq: A fuzzableRequest
        '''
        # Init...
        if self.is404 == None:
            self.is404 = kb.kb.getData( 'error404page', '404' )

        # Start
        davURLs = [ i[0] for i in kb.kb.getData( 'allowedMethods' , 'dav-methods' ) ]
        domainPath = urlParser.getDomainPath( freq.getURL() )
        if domainPath in davURLs and domainPath not in self._alreadyTested:
            om.out.debug( 'dav plugin is testing: ' + freq.getURL() )
            self._alreadyTested.append( domainPath )
            
            self._PUT( domainPath )
            self._PROPFIND( domainPath )
            self._SEARCH( domainPath )
            
    def _SEARCH( self, domainPath ):
        '''
        Test SEARCH method.
        '''
        content = "<?xml version='1.0'?>\r\n\
        <g:searchrequest xmlns:g='DAV:'>\r\n\
        <g:sql>\r\n\
        Select 'DAV:displayname' from scope()\r\n\
        </g:sql>\r\n\
        </g:searchrequest>\r\n"

        res = self._urlOpener.SEARCH( domainPath , data=content )
        if res.getCode() in xrange(200,300) and "DAV:" in res.getBody():
            v = vuln.vuln()
            v.setURL( url )
            v.setId( res.id )
            v.setSeverity(severity.MEDIUM)
            v.setName( 'Insecure DAV configuration' )
            v.setMethod( 'SEARCH' )
            v.setDesc( 'Directory listing with HTTP SEARCH method was found at directory: ' + domainPath )
            kb.kb.append( self, 'dav', v )
            
    def _PROPFIND( self, domainPath ):
        '''
        Test PROPFIND method
        '''
        content = "<?xml version='1.0'?>\r\n\
        <a:propfind xmlns:a='DAV:'>\r\n\
        <a:prop>\r\n\
        <a:displayname:/>\r\n\
        </a:prop>\r\n\
        </a:propfind>\r\n"
        
        res = self._urlOpener.PROPFIND( domainPath , data=content, headers={'Depth': '1'} )
        if res.getCode() in xrange(200,300) and "D:href" in res.getBody():
            v = vuln.vuln()
            v.setURL( res.getURL() )
            v.setId( res.id )
            v.setSeverity(severity.MEDIUM)
            v.setName( 'Insecure DAV configuration' )
            v.setMethod( 'PROPFIND' )
            v.setDesc( 'Directory listing with HTTP PROPFIND method was found at directory: ' + domainPath )
            kb.kb.append( self, 'dav', v )
        
    def _PUT( self, domainPath ):
        '''
        Tests PUT method.
        '''
        # upload
        url = urlParser.urlJoin( domainPath, self._rand )
        rndContent = createRandAlNum(6)
        self._urlOpener.PUT( url , data=rndContent )
        
        # check if uploaded
        res = self._urlOpener.GET( url , useCache=True )
        if res.getBody() == rndContent:
            v = vuln.vuln()
            v.setURL( url )
            v.setId( res.id )
            v.setSeverity(severity.HIGH)
            v.setName( 'Insecure DAV configuration' )
            v.setMethod( 'PUT' )
            v.setDesc( 'File upload with HTTP PUT method was found at directory: ' + domainPath + ' . Uploaded test file: ' + res.getURL() )
            kb.kb.append( self, 'dav', v )

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.printUniq( kb.kb.getData( 'dav', 'dav' ), 'VAR' )
        
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

    def setOptions( self, optionMap ):
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
        return ['discovery.allowedMethods', 'discovery.serverHeader']
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin will find webdav configuration errors. This errors are generally server configuration errors rather
        than a web application error. To check for vulnerabilities of this kind, the plugin will try to PUT a file on a directory
        that has webDav enabled, if the file is uploaded successfully, then we have found a bug.        
        '''
