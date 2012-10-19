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
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.kb.info as info
import core.data.constants.severity as severity

from core.data.bloomfilter.bloomfilter import scalable_bloomfilter
from core.data.fuzzer.fuzzer import rand_alpha, rand_alnum
from core.data.dc.headers import Headers
from core.controllers.plugins.audit_plugin import AuditPlugin


class dav(AuditPlugin):
    '''
    Verify if the WebDAV module is properly configured.
    
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        AuditPlugin.__init__(self)
        
        # Internal variables
        self._already_tested_dirs = scalable_bloomfilter()

    def audit(self, freq ):
        '''
        Searches for file upload vulns using PUT method.
        
        @param freq: A FuzzableRequest
        '''
        # Start
        domain_path = freq.getURL().getDomainPath()
        if domain_path not in self._already_tested_dirs:
            self._already_tested_dirs.add( domain_path )
            #
            #    Send the three requests in different threads, store the apply_result
            #    objects in order to be able to "join()" in the next for loop
            #
            #    TODO: This seems to be a fairly common use case: Send args to N
            #    functions that need to be run in different threads. If possible
            #    code this into threadpool.py in order to make this code clearer
            results = []
            for func in [self._PUT, self._PROPFIND, self._SEARCH]:
                apply_res = self._tm.threadpool.apply_async(func, (domain_path,) )
                results.append( apply_res )
            
            for apply_res in results:
                apply_res.get()
            
            
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

        res = self._uri_opener.SEARCH( domain_path , data=content )
        
        content_matches =  '<a:response>' in res or '<a:status>' in res or \
                           'xmlns:a="DAV:"' in res
        
        if content_matches and res.getCode() in xrange(200, 300):
            v = vuln.vuln()
            v.setPluginName(self.getName())
            v.setURL( res.getURL() )
            v.set_id( res.id )
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
        
        hdrs = Headers([('Depth', '1')])
        res = self._uri_opener.PROPFIND( domain_path , data=content, headers=hdrs )
        
        if "D:href" in res and res.getCode() in xrange(200, 300):
            v = vuln.vuln()
            v.setPluginName(self.getName())
            v.setURL( res.getURL() )
            v.set_id( res.id )
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
        url = domain_path.urlJoin( rand_alpha( 5 ) )
        rndContent = rand_alnum(6)
        put_response = self._uri_opener.PUT( url , data=rndContent )
        
        # check if uploaded
        res = self._uri_opener.GET( url , cache=True )
        if res.getBody() == rndContent:
            v = vuln.vuln()
            v.setPluginName(self.getName())
            v.setURL( url )
            v.set_id( [put_response.id, res.id] )
            v.setSeverity(severity.HIGH)
            v.setName( 'Insecure DAV configuration' )
            v.setMethod( 'PUT' )
            msg = 'File upload with HTTP PUT method was found at resource: "%s".'
            msg += ' A test file was uploaded to: "%s".'
            v.setDesc( msg % (domain_path, res.getURL()) )
            kb.kb.append( self, 'dav', v )
        
        # Report some common errors
        elif put_response.getCode() == 500:
            i = info.info()
            i.setPluginName(self.getName())
            i.setURL( url )
            i.set_id( res.id )
            i.setName( 'DAV incorrect configuration' )
            i.setMethod( 'PUT' )
            msg = 'DAV seems to be incorrectly configured. The web server answered with a 500'
            msg += ' error code. In most cases, this means that the DAV extension failed in'
            msg += ' some way. This error was found at: "' + put_response.getURL() + '".'
            i.setDesc( msg )
            kb.kb.append( self, 'dav', i )
        
        # Report some common errors
        elif put_response.getCode() == 403:
            i = info.info()
            i.setPluginName(self.getName())
            i.setURL( url )
            i.set_id( [put_response.id, res.id] )
            i.setName( 'DAV insufficient privileges' )
            i.setMethod( 'PUT' )
            msg = 'DAV seems to be correctly configured and allowing you to use the PUT method'
            msg +=' but the directory does not have the correct permissions that would allow'
            msg += ' the web server to write to it. This error was found at: "'
            msg += put_response.getURL() + '".'
            i.setDesc( msg )
            kb.kb.append( self, 'dav', i )
            
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.print_uniq( kb.kb.get( 'dav', 'dav' ), 'VAR' )
        
    def get_plugin_deps( self ):
        '''
        @return: A list with the names of the plugins that should be run before 
                 the current one.
        '''
        return ['infrastructure.allowed_methods', 'infrastructure.server_header']
    
    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds WebDAV configuration errors. These errors are generally
        server configuration errors rather than a web application errors. To
        check for vulnerabilities of this kind, the plugin will try to PUT a
        file on a directory that has WebDAV enabled, if the file is uploaded 
        successfully, then we have found a bug.
        '''
