'''
afd.py

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

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

from core.controllers.w3afException import w3afRunOnce, w3afException
from core.data.fuzzer.fuzzer import createRandAlNum
from core.controllers.misc.levenshtein import relative_distance_lt

import urllib


class afd(baseDiscoveryPlugin):
    '''
    Find out if the remote web server has an active filter ( IPS or WAF ).
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)

        #
        #   Internal variables
        #
        self._exec = True
        # The results
        self._not_filtered = []
        self._filtered = []        
        
    def discover(self, fuzzableRequest ):
        '''
        Nothing strange, just do some GET requests to the first URL with an invented parameter and 
        the custom payloads that are supposed to be filtered, and analyze the response.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains
                                                    (among other things) the URL to test.
        '''
        if not self._exec:
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
        else:
            self._exec = False
            
            try:
                filtered, not_filtered = self._send_requests( fuzzableRequest )
            except w3afException, w3:
                om.out.error( str(w3) )
            else:
                self._analyze_results( filtered, not_filtered )

        return []

    def _send_requests( self, fuzzableRequest ):
        '''
        Actually send the requests that might be blocked.
        @parameter fuzzableRequest: The fuzzableRequest to modify in order to see if it's blocked
        '''
        rnd_param = createRandAlNum(7)
        rnd_value = createRandAlNum(7)
        originalURL = fuzzableRequest.getURL() + '?' + rnd_param + '=' + rnd_value
        
        try:
            original_response_body = self._urlOpener.GET( originalURL , useCache=True ).getBody()
        except Exception:
            msg = 'Active filter detection plugin failed to recieve a '
            msg += 'response for the first request. Can not perform analysis.'
            raise w3afException( msg )
        else:
            original_response_body = original_response_body.replace( rnd_param, '' )
            original_response_body = original_response_body.replace( rnd_value, '' )
            
            for offending_string in self._get_offending_strings():
                offending_URL = fuzzableRequest.getURL() + '?' + rnd_param + '=' + offending_string
                
                # Perform requests in different threads
                targs = (offending_string, offending_URL, original_response_body, rnd_param)
                self._tm.startFunction( target=self._send_and_analyze, args=targs, ownerObj=self )
            
            # Wait for threads to finish
            self._tm.join( self )
            
            # Analyze the results
            return self._filtered, self._not_filtered
                
    def _send_and_analyze(self, offending_string, offending_URL, original_resp_body, rnd_param):
        '''
        Actually send the HTTP request.
        @return: None, everything is saved to the self._filtered and self._not_filtered lists.
        '''
        try:
            resp_body = self._urlOpener.GET(offending_URL, useCache=False).getBody()
        except KeyboardInterrupt, e:
            raise e
        except Exception:
            # I get here when the remote end closes the connection
            self._filtered.append(offending_URL)
        else:
            # I get here when the remote end returns a 403 or something like that...
            # So I must analyze the response body
            resp_body = resp_body.replace(offending_string, '')
            resp_body = resp_body.replace(rnd_param, '')
            if relative_distance_lt(resp_body, original_resp_body, 0.15):
                self._filtered.append(offending_URL)
            else:
                self._not_filtered.append(offending_URL)
            
        
    def _analyze_results( self, filtered, not_filtered ):
        '''
        Analyze the test results and save the conclusion to the kb.
        '''
        if len( filtered ) >= len(self._get_offending_strings()) / 5.0:
            i = info.info()
            i.setPluginName(self.getName())
            i.setName('Active filter detected')
            msg = 'The remote network has an active filter. IMPORTANT: The result of all the other'
            msg += ' plugins will be unaccurate, web applications could be vulnerable but '
            msg += '"protected" by the active filter.'
            i.setDesc( msg )
            i['filtered'] = filtered
            kb.kb.append( self, 'afd', i )
            om.out.information( i.getDesc() )
            
            om.out.information('The following URLs were filtered:')
            for i in filtered:
                om.out.information('- ' + i )
            
            om.out.information('The following URLs passed undetected by the filter:')
            for i in not_filtered:
                om.out.information('- ' + i )
    
    def _get_offending_strings( self ):
        '''
        @return: A list of strings that will be filtered by most IPS devices.
        '''
        res = []
        res.append('../../../../etc/passwd')
        res.append('./../../../etc/motd\0html')
        res.append('id;uname -a')
        res.append('<? passthru("id");?>')
        res.append('../../WINNT/system32/cmd.exe?dir+c:\\')
        res.append('type+c:\\winnt\\repair\\sam._')
        res.append('ps -aux;')
        res.append('../../../../bin/chgrp nobody /etc/shadow|')
        res.append('SELECT TOP 1 name FROM sysusers')
        res.append('exec master..xp_cmdshell dir')
        res.append('exec xp_cmdshell dir')
        
        res = [ urllib.quote_plus(x) for x in res ]
        
        return res
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter optionsMap: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass
        
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
        This plugin sends custom requests to the remote web server in order to verify if the
        remote network is protected by an IPS or WAF. 
        
        afd plugin detects both TCP-Connection-reset and HTTP level filters, the first one (usually
         implemented by IPS devices) is easy to verify: if afd requests the custom page and the GET
        method raises an exception, then its being probably blocked by an active filter. The second
        one (usually implemented by Web Application Firewalls like mod_security) is a little harder
         to verify: first afd requests a page without adding any offending parameters, afterwards it 
        requests the same URL but with a faked parameter and customized values; if the response 
        bodies differ, then its safe to say that the remote end has an active filter.
        '''
