'''
findJboss.py

Copyright 2012 Nahuel Sanchez

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
from functools import partial
import socket

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.controllers.misc.decorators import runonce
from core.controllers.w3afException import w3afRunOnce
from core.data.options.optionList import optionList
from core.data.parsers.urlParser import url_object
import core.data.kb.info as info
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln


class findJBoss(baseDiscoveryPlugin):
    '''
    Find Default Jboss Installations
    @author: Nahuel Sanchez (nsanchez@bonsai-sec.com)
    '''
    _jboss_vulns = (
        {'url': '/admin-console/', 
         'name': 'JBoss Admin Console enabled',
         'desc': 'Jboss Admin Console was found!',
         'type': 'i'},
        {'url': '/jmx-console/', 
         'name': 'JBoss JMX Console found',
         'desc': 'JMX Console found without Auth Enabled',
         'type': 'v'},
        {'url': '/status', 
         'name': 'JBoss Status Servlet found',
         'desc': 'JBoss Status Servlet gives valuable information',
         'type': 'i'},
        {'url': '/web-console/ServerInfo.jsp', 
         'name': 'WebConsole ServerInfo.jsp found',
         'desc': 'WebConsole ServerInfo.jsp gives valuable information',
         'type': 'i'},
        {'url': 'WebConsole/Invoker', 
         'name': 'WebConsole ServerInfo.jsp found',
         'desc': 'JBoss WebConsole Invoker enables attackers to send any JMX '
                    'command to JBoss AS',
         'type': 'v'},
        {'url': '/invoker/JMXInvokerServlet', 
         'name': 'JMX Invoker enabled without Auth',
         'desc': 'JMX Invoker enables attackers to send any JMX command to '
                    'JBoss AS',
         'type': 'v'}
        )
    
    _ports = ['80', '8080']
    
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        self._fuzzable_requests_to_return = []
        
    @runonce(exc_class=w3afRunOnce)
    def discover(self, fuzzableRequest):
        '''
        Checks if exists JBoss Interesting Directories 
        And possible vulnerabilities
        '''
        domain = fuzzableRequest.getURL().baseUrl()
        enc = domain._encoding
        domain = domain.url_string
        host = fuzzableRequest.getURL().getDomain()
        # ports test
        ports = filter(partial(self._portTest, host), self._ports)
        
        for vulnd in findJBoss._jboss_vulns:
            for port in ports:
                domain_port = url_object(domain + ":" + port, encoding=enc)
                vuln_url = domain_port.urlJoin(vulnd['url'])
                response = self._urlOpener.GET(vuln_url)
                
                if response and response.getCode() == 200: 
                    
                    if vulnd['type'] == 'i':
                        i = info.info()
                        i.setPluginName(self.getName())
                        i.setName(vulnd['name'])
                        i.setURL(vuln_url)
                        i.setId(response.id)
                        i.setDesc(vulnd['desc'])
                        kb.kb.append(self, vulnd['name'], i)
                        
                    else:
                        v = vuln.vuln()
                        v.setPluginName(self.getName())
                        v.setName(vulnd['name'])
                        v.setURL(vuln_url)
                        v.setId(response.id)
                        v.setDesc(vulnd['desc'])
                        kb.kb.append(self, vulnd['name'], v)
                    
                    fuzzable_requests = self._createFuzzableRequests(response)
                    self._fuzzable_requests_to_return.extend(fuzzable_requests)
      
        return self._fuzzable_requests_to_return
    
    def handleUrlError(self, url_error):
        return (True, None)
    
    def _portTest(self, host, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            sock.connect((host, int(port)))
        except:
            return False
        finally:
            sock.close()
        return True 
                         
    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol
        
    def setOptions(self, OptionList):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass

    def getPluginDeps(self):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []

    def getLongDesc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This Plugin searches JBoss installation directories and possible
        security vulnerabilities.
        '''