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

import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

from core.controllers.w3afException import w3afException
import core.data.parsers.urlParser as urlParser
from core.data.fuzzer.fuzzer import createRandAlpha, createRandAlNum


class dav(baseAuditPlugin):
    '''
    Verify if the WebDAV module is properly configured.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        # Internal variables
        self.is_404 = None
        self._already_tested_dirs = []

    def _fuzzRequests(self, freq ):
        '''
        Searches for file upload vulns using PUT method.
        
        @param freq: A fuzzableRequest
        '''
        # Init...
        if self.is_404 == None:
            self.is_404 = kb.kb.getData( 'error404page', '404' )

        # Start
        domain_path = urlParser.getDomainPath( freq.getURL() )
        if domain_path not in self._already_tested_dirs:
            om.out.debug( 'dav plugin is testing: ' + freq.getURL() )
            self._already_tested_dirs.append( domain_path )
            
            self._PUT( domain_path )
            self._PROPFIND( domain_path )
            self._SEARCH( domain_path )
            
    def _SEARCH( self, domain_path ):
        '''
        Test SEARCH method.
        '''
        content = "<?xml version='1.0'?>\r\n"
        content += "<g:searchrequest xmlns:g='DAV:'>\r\n"
        content += "<g:sql>\r\n"
        content += "Select 'DAV:displayname' from scope()\r\n"
        content += "</g:sql>\r\n"
        content += "</g:searchrequest>\r\n"

        res = self._urlOpener.SEARCH( domain_path , data=content )
        # Remember that httpResponse objects have a faster "__in__" than
        # the one in strings; so string in response.getBody() is slower than
        # string in response        
        if "DAV:" in res and res.getCode() in xrange(200, 300):
            v = vuln.vuln()
            v.setURL( res.getURL() )
            v.setId( res.id )
            v.setSeverity(severity.MEDIUM)
            v.setName( 'Insecure DAV configuration' )
            v.setMethod( 'SEARCH' )
            msg = 'Directory listing with HTTP SEARCH method was found at directory: "'
            msg += domain_path + '"'
            v.setDesc( msg )
            kb.kb.append( self, 'dav', v )
            
    def _PROPFIND( self, domain_path ):
        '''
        Test PROPFIND method
        '''
        content = "<?xml version='1.0'?>\r\n"
        content += "<a:propfind xmlns:a='DAV:'>\r\n"
        content += "<a:prop>\r\n"
        content += "<a:displayname:/>\r\n"
        content += "</a:prop>\r\n"
        content += "</a:propfind>\r\n"
        
        res = self._urlOpener.PROPFIND( domain_path , data=content, headers={'Depth': '1'} )
        # Remember that httpResponse objects have a faster "__in__" than
        # the one in strings; so string in response.getBody() is slower than
        # string in response               
        if "D:href" in res and res.getCode() in xrange(200, 300):
            v = vuln.vuln()
            v.setURL( res.getURL() )
            v.setId( res.id )
            v.setSeverity(severity.MEDIUM)
            v.setName( 'Insecure DAV configuration' )
            v.setMethod( 'PROPFIND' )
            msg = 'Directory listing with HTTP PROPFIND method was found at directory: "'
            msg += domain_path + '"'
            v.setDesc( msg )
            kb.kb.append( self, 'dav', v )
        
    def _PUT( self, domain_path ):
        '''
        Tests PUT method.
        '''
        # upload
        url = urlParser.urlJoin( domain_path, createRandAlpha( 5 ) )
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
            msg = 'File upload with HTTP PUT method was found at resource: "' + domain_path + '".'
            msg += ' A test file was uploaded to: "' + res.getURL() + '".'
            v.setDesc( msg )
            kb.kb.append( self, 'dav', v )

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.printUniq( kb.kb.getData( 'dav', 'dav' ), 'VAR' )
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol
        
    def setOptions( self, optionMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
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
        This plugin finds WebDAV configuration errors. These errors are generally server configuration errors rather
        than a web application errors. To check for vulnerabilities of this kind, the plugin will try to PUT a file on a directory
        that has WebDAV enabled, if the file is uploaded successfully, then we have found a bug.
        '''
