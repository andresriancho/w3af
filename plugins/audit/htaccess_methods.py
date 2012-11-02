'''
htaccess_methods.py

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
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity
import core.data.constants.response_codes as http_constants

from core.controllers.plugins.audit_plugin import AuditPlugin
from core.data.bloomfilter.bloomfilter import scalable_bloomfilter


class htaccess_methods(AuditPlugin):
    '''
    Find misconfigurations in Apache's "<LIMIT>" configuration.
    
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    BAD_METHODS = set([ http_constants.UNAUTHORIZED, 
                        http_constants.NOT_IMPLEMENTED, 
                        http_constants.METHOD_NOT_ALLOWED,
                        http_constants.FORBIDDEN])
    
    def __init__(self):
        AuditPlugin.__init__(self)
        self._already_tested = scalable_bloomfilter()
        
    def audit(self, freq ):
        '''
        Tests an URL for htaccess misconfigurations.
        
        @param freq: A FuzzableRequest
        '''
        response = self._uri_opener.GET( freq.getURL() , cache=True )

        if response.getCode() in self.BAD_METHODS:
            for url in filter(self._uniq, self._generate_urls(freq.getURL())):
                self._check_methods( url )

    def _uniq(self, url):
        return not url.url_string in self._already_tested

    def _generate_urls(self, url):
        '''
        Generate the URLs to test based on the initial URL we get from the core.
        
        Please note that I don't care much about duplicates coming out of this
        function since I'm filtering using the _unique method.
        
        I want to test URLs with PHP extensions because they are handled in a
        different way by Apache:
        
        andres@workstation:~/workspace/threading2$ nc moth 80 -v -v
        Connection to moth 80 port [tcp/http] succeeded!
        GGET /w3af/audit/htaccess_methods/index.html HTTP/1.1
        Host: moth
        
        HTTP/1.1 501 Method Not Implemented
        Date: Wed, 01 Aug 2012 12:10:13 GMT
        Server: Apache/2.2.22 (Ubuntu)
        Allow: POST,OPTIONS,GET,HEAD,TRACE
        Vary: Accept-Encoding
        Content-Length: 314
        Connection: close
        Content-Type: text/html; charset=iso-8859-1
        
        ...
        
        andres@workstation:~/workspace/threading2$ nc moth 80 -v -v
        Connection to moth 80 port [tcp/http] succeeded!
        GGET /w3af/audit/htaccess_methods/index.php HTTP/1.1
        Host: moth
        
        HTTP/1.1 200 OK
        Date: Wed, 01 Aug 2012 12:11:22 GMT
        Server: Apache/2.2.22 (Ubuntu)
        X-Powered-By: PHP/5.3.10-1ubuntu3.2
        Vary: Accept-Encoding
        Content-Length: 4
        Content-Type: text/html
        
        ABC
        '''
        yield url
        
        if url.getExtension():
            tmp_url = url.copy()
            tmp_url.setExtension('php')
            yield tmp_url
        
        if url.getFileName():
            tmp_url = url.copy()
            tmp_url.setExtension('php')
            tmp_url.setFileName('index')
            yield tmp_url
        else:
            tmp_url = url.copy()
            yield tmp_url.urlJoin('index.php')
            

    def _check_methods( self, url ):
        '''
        Perform some requests in order to check if we are able to retrieve
        some data with methods that may be wrongly enabled.
        '''
        allowed_methods = []
        for method in ['GET', 'POST', 'ABCD', 'HEAD']:
            method_functor = getattr( self._uri_opener, method )
            try:
                response = apply( method_functor, (url,) , {} )
                code = response.getCode()
            except:
                pass
            else:
                if code not in self.BAD_METHODS:
                    allowed_methods.append( (method, response.id) )
        
        if len(allowed_methods)>0:
            v = vuln.vuln()
            v.setPluginName(self.get_name())
            v.setURL( url )
            v.set_id([i for m, i in allowed_methods])
            v.set_name( 'Misconfigured access control' )
            v.setSeverity(severity.MEDIUM)
            msg = 'The resource: "'+ url + '" requires authentication but the access'
            msg += ' is misconfigured and can be bypassed using these methods: ' 
            msg += ', '.join([m for m, i in allowed_methods]) + '.'
            v.set_desc( msg )
            v['methods'] = allowed_methods
            kb.kb.append( self , 'auth' , v )
            om.out.vulnerability( v.get_desc(), severity=v.getSeverity() )             
                
    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds .htaccess misconfigurations in the LIMIT configuration
        parameter.
        
        This plugin is based on a paper written by Frame and madjoker from 
        kernelpanik.org. The paper is called : "htaccess: bilbao method exposed"
        
        The idea of the technique (and the plugin) is to exploit common
        misconfigurations of .htaccess files like this one:
        
            <LIMIT GET>
                require valid-user
            </LIMIT>
        
        The configuration only allows authenticated users to perform GET requests,
        but POST requests (for example) can be performed by any user.
        '''
