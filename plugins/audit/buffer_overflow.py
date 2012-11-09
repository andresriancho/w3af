'''
buffer_overflow.py

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
import core.controllers.output_manager as om
import core.data.kb.knowledge_base as kb
import core.data.kb.vuln as vuln
import core.data.kb.info as info
import core.data.constants.severity as severity

from core.controllers.plugins.audit_plugin import AuditPlugin
from core.controllers.exceptions import w3afException, w3afMustStopException
from core.data.fuzzer.fuzzer import create_mutants
from core.data.fuzzer.utils import rand_alpha
from core.data.esmre.multi_in import multi_in


class buffer_overflow(AuditPlugin):
    '''
    Find buffer overflow vulnerabilities.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    OVERFLOW_ERRORS = (
        '*** stack smashing detected ***:',
        'Backtrace:',
        'Memory map:',
        '<html><head>\n<title>500 Internal Server Error</title>\n</head><body>\n<h1>'
        'Internal Server Error</h1>'
    )

    _multi_in = multi_in( OVERFLOW_ERRORS )
    
    # TODO: if lengths = [ 65 , 257 , 513 , 1025, 2049, 4097, 8000 ]
    # then i get a BadStatusLine exception from urllib2, is seems to be an
    # internal error. Tested against tomcat 5.5.7
    BUFFER_TESTS = [ rand_alpha(l) for l in [ 65 , 257 , 513 , 1025, 2049 ] ]


    def __init__(self):
        '''
        Some notes:
            On Apache, when an overflow happends on a cgic script, this is written
            to the log:
                *** stack smashing detected ***: /var/www/.../buffer_overflow.cgi terminated,
                referer: http://localhost/w3af/bufferOverflow/buffer_overflow.cgi
                Premature end of script headers: buffer_overflow.cgi, referer: ...

            On Apache, when an overflow happends on a cgic script, this is
            returned to the user:
                <!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
                <html><head>
                <title>500 Internal Server Error</title>
                </head><body>
                <h1>Internal Server Error</h1>
                <p>The server encountered an internal error or
                misconfiguration and was unable to complete
                your request.</p>
                <p>Please contact the server administrator,
                 webmaster@localhost and inform them of the time the error occurred,
                and anything you might have done that may have
                caused the error.</p>
                <p>More information about this error may be available
                in the server error log.</p>
                <hr>
                <address>Apache/2.0.55 (Ubuntu) mod_python/3.2.8 Python/2.4.4c1
                PHP/5.1.6 Server at localhost Port 80</address>
                </body></html>
                
            Note that this is an Apache error 500, not the more common PHP error 500.
        '''
        AuditPlugin.__init__(self)
        
    def audit(self, freq ):
        '''
        Tests an URL for buffer overflow vulnerabilities.
        
        @param freq: A FuzzableRequest
        '''
        try:
            orig_resp = self._uri_opener.send_mutant(freq)
        except:
            msg = 'Failed to perform the initial request during buffer'
            msg += ' overflow testing'
            om.out.debug( msg )
        else:
            mutants = create_mutants(freq , self.BUFFER_TESTS, orig_resp=orig_resp)
            
            self._tm.threadpool.map(self._send_request, mutants)
            
    def _send_request(self, mutant):
        '''
        Sends a mutant to the remote web server. I wrap urllib's _send_mutant 
        just to handle errors in a different way.
        '''
        try:
            response = self._uri_opener.send_mutant(mutant)
        except (w3afException,w3afMustStopException):
            i = info.info( mutant )
            i.setPluginName(self.get_name())
            i.set_name( 'Potential buffer overflow vulnerability' )
            msg = 'A potential (most probably a false positive than a bug) buffer-'
            msg += 'overflow was found when requesting: "%s", using HTTP method'
            msg += ' %s. The data sent was: "%s".' 
            msg = msg % ( mutant.getURL(), mutant.get_method(), mutant.get_dc())
            i.set_desc( msg )
            kb.kb.append_uniq( self, 'buffer_overflow', i )
        else:
            self._analyze_result( mutant, response )
                
    def _analyze_result( self, mutant, response ):
        '''
        Analyze results of the _send_mutant method.
        '''
        for error_str in self._multi_in.query( response.body ):
            # And not in the original response
            if error_str not in mutant.get_original_response_body() and \
            self._has_no_bug(mutant):
                v = vuln.vuln( mutant )
                v.setPluginName(self.get_name())
                v.set_id( response.id )
                v.set_severity(severity.MEDIUM)
                v.set_name( 'Buffer overflow vulnerability' )
                msg = 'A potential buffer overflow (accurate detection is hard...)'
                msg += ' was found at: ' + mutant.found_at()
                v.set_desc( msg )
                v.addToHighlight( error_str )
                kb.kb.append_uniq( self, 'buffer_overflow', v )
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.print_uniq( kb.kb.get( 'buffer_overflow', 'buffer_overflow' ), 'VAR' )

    def get_plugin_deps( self ):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return ['grep.error_500']

    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds buffer overflow vulnerabilities.
        
        Users have to know that detecting a buffer overflow vulnerability will
        be only possible if the server is configured to return errors, and the
        application is developed in cgi-c or some other language that allows 
        the programmer to do their own memory management.
        '''
