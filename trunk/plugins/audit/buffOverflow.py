'''
buffOverflow.py

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

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
from core.controllers.w3afException import w3afException, w3afMustStopException
from core.data.fuzzer.fuzzer import createMutants, createRandAlpha

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.kb.info as info
import core.data.constants.severity as severity

# options
from core.data.options.option import option
from core.data.options.optionList import optionList


class buffOverflow(baseAuditPlugin):
    '''
    Find buffer overflow vulnerabilities.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        '''
        Some notes:
            On apache, when an overflow happends on a cgic script, this is written to the log:
                *** stack smashing detected ***: /var/www/w3af/bufferOverflow/buffOverflow.cgi terminated, referer: http://localhost/w3af/bufferOverflow/buffOverflow.cgi
                Premature end of script headers: buffOverflow.cgi, referer: http://localhost/w3af/bufferOverflow/buffOverflow.cgi

            On apache, when an overflow happends on a cgic script, this is returned to the user:
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
                <address>Apache/2.0.55 (Ubuntu) mod_python/3.2.8 Python/2.4.4c1 PHP/5.1.6 Server at localhost Port 80</address>
                </body></html>
                
            Note that this is  an apache error 500, not the more common PHP error 500.
        '''
        baseAuditPlugin.__init__(self)
        
    def audit(self, freq ):
        '''
        Tests an URL for buffer overflow vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'bufferOverflow plugin is testing: ' + freq.getURL() )
        
        str_list = self._get_string_list()
        try:
            oResponse = self._sendMutant( freq , analyze=False ).getBody()
        except:
            msg = 'Failed to perform the initial request during buffer'
            msg += ' overflow testing'
            om.out.debug( msg )
        else:
            mutants = createMutants( freq , str_list, oResponse=oResponse )
                
            for mutant in mutants:
                targs = (mutant,)
                self._tm.startFunction( target=self._sendMutant, args=targs, ownerObj=self )
                
            self._tm.join( self )
            
    def _sendMutant( self, mutant, analyze=True, grepResult=True ):
        '''
        Sends a mutant to the remote web server. I override the _sendMutant of basePlugin
        just to handle errors in a different way.
        '''
        url = mutant.getURI()
        data = mutant.getData()
        headers = mutant.getHeaders()
        # Also add the cookie header.
        cookie = mutant.getCookie()
        if cookie:
            headers['Cookie'] = str(cookie)

        args = ( url, )
        method = mutant.getMethod()
        
        functor = getattr( self._urlOpener , method )
        try:
            kwdargs = {'data': data, 'headers': headers, 'grepResult': grepResult }
            res = apply( functor, args, kwdargs )
        except (w3afException,w3afMustStopException):
            i = info.info( mutant )
            i.setPluginName(self.getName())
            i.setName( 'Possible buffer overflow vulnerability' )
            if data:
                msg = 'A possible (most probably a false positive than a bug) buffer overflow was'
                msg += ' found when requesting: "' + url + '", using HTTP method ' + method
                msg += '. The data sent was: "' + str(data) + '".'
                i.setDesc( msg )
            else:
                msg = 'A possible (most probably a false positive than a bug) buffer overflow was'
                msg += ' found when requesting: "' + url + '", using HTTP method ' + method + '.'
                i.setDesc( msg )
            kb.kb.append( self, 'buffOverflow', i )
        else:
            if analyze:
                self._analyzeResult( mutant, res )
            return res
        
    def _get_string_list( self ):
        '''
        @return: This method returns a list of strings that could overflow a buffer.
        '''
        strings = []
        lengths = [ 65 , 257 , 513 , 1025, 2049 ]
        ### TODO !! if lengths = [ 65 , 257 , 513 , 1025, 2049, 4097, 8000 ]
        ### then i get a badStatusLine exception from urllib2, is seems to be a internal error.
        ### tested against tomcat 5.5.7
        for i in lengths:
            strings.append( createRandAlpha( i ) )  
        return strings
        
    def _analyzeResult( self, mutant, response ):
        '''
        Analyze results of the _sendMutant method.
        '''
        for error in self._get_errors():
            
            # Check if the error string is in the response
            if error in response:
                # And not in the originally requested (non fuzzed) request
                if not error not in mutant.getOriginalResponseBody():
                    # vuln, vuln!
                    v = vuln.vuln( mutant )
                    v.setPluginName(self.getName())
                    v.setId( response.id )
                    v.setSeverity(severity.MEDIUM)
                    v.setName( 'Buffer overflow vulnerability' )
                    msg = 'A possible buffer overflow (detection is really hard...) was found at: '
                    msg += mutant.foundAt()
                    v.setDesc( msg )
                    v.addToHighlight( error )
                    kb.kb.append( self, 'buffOverflow', v )
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._tm.join( self )
        self.printUniq( kb.kb.getData( 'buffOverflow', 'buffOverflow' ), 'VAR' )
    
    def _get_errors( self ):
        '''
        @return: A list of errors that are shown when a buffer overflow is triggered
        '''
        res = []
        
        error = '<html><head>\n<title>500 Internal Server Error</title>\n</head><body>\n<h1>'
        error += 'Internal Server Error</h1>'
        res.append( error )
        
        res.append('*** stack smashing detected ***:')
        res.append('Backtrace:')
        res.append('Memory map:')
        
        return res
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol
        
    def setOptions( self, OptionList ):
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
        return ['grep.error500']

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds buffer overflow vulnerabilities.
        
        Users have to know that detecting a buffer overflow vulnerability will be only possible if the server is configured
        to return errors, and the application is developed in cgi-c or some other language that allows the programmer to
        do their own memory management.
        '''
