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

from core.controllers.w3afException import w3afRunOnce
from core.data.fuzzer.fuzzer import createRandAlNum
import urllib

class afd(baseDiscoveryPlugin):
    '''
    Find out if the remote web server has an active filter ( IPS or WAF ).
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)

        # Internal variable
        self._exec = True
        
    def discover(self, fuzzableRequest ):
        '''
        Nothing strange, just do some GET requests to the first URL with an invented parameter and 
        the custom payloads that are supposed to be filtered, and analyze the response.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        if not self._exec:
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
        else:
            self._exec = False
            
            filtered, notFiltered = self._sendRequests( fuzzableRequest )
            self._analyzeResult( filtered, notFiltered )

        return []

    def _sendRequests( self, fuzzableRequest ):
        '''
        Actually send the requests
        '''
        rndParam = createRandAlNum(7)
        rndValue = createRandAlNum(7)
        originalURL = fuzzableRequest.getURL() + '?' + rndParam + '=' + rndValue
        
        # The results
        notFiltered = []
        filtered = []        
        
        try:
            originalResponseBody = self._urlOpener.GET( originalURL , useCache=True ).getBody()
        except Exception:
            msg = 'Active filter detection plugin failed to recieve a '
            msg += 'response for the first request.'
            om.out.error( msg )
        else:
            originalResponseBody = originalResponseBody.replace( rndParam, '' )
            originalResponseBody = originalResponseBody.replace( rndValue, '' )
            
            for toBeFiltered in self._getFilteredStrings():
                badURL = fuzzableRequest.getURL() + '?' + rndParam + '=' + toBeFiltered
                try:
                    responseBody = self._urlOpener.GET( badURL, useCache=False ).getBody()
                except KeyboardInterrupt,e:
                    raise e
                except Exception, e:
                    # I get here when the remote end closes the connection
                    filtered.append( badURL )
                else:
                    # I get here when the remote end returns a 403 or something like that...
                    # So I must analyze the response body
                    responseBody = responseBody.replace(toBeFiltered,'')
                    responseBody = responseBody.replace(rndParam,'')
                    if responseBody != originalResponseBody:
                        filtered.append( badURL )
                    else:
                        notFiltered.append( badURL )
        
        return filtered, notFiltered

    def _analyzeResult( self, filtered, notFiltered ):
        '''
        Analyze the test results and save the conclusion to the kb.
        '''
        if len( filtered ) >= len(self._getFilteredStrings()) / 5.0:
            i = info.info()
            i.setName('Active filter detected')
            msg = 'The remote network has an active filter. IMPORTANT: The result of all the other'
            msg += ' plugins will be unaccurate, web applications could be vulnerable but '
            msg += '"protected" by the active filter.'
            i.setDesc( msg )
            i['filtered'] = filtered
            kb.kb.append( self, 'afd', i )
            om.out.information( i.getDesc() )
            
            om.out.information('The following URLs were filtered:')
            for f in filtered:
                om.out.information('- ' + f )
            
            om.out.information('The following URLs passed undetected by the filter:')
            for f in notFiltered:
                om.out.information('- ' + f )
    
    def _getFilteredStrings( self ):
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
         to verify: first afd requests a page without adding any special parameters, afterwards it 
        requests the same URL but with a faked parameter and customized values; if the response 
        bodies differ, then its safe to say that the remote end has an active filter.
        '''
