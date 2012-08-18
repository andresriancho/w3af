'''
findJboss.py

Copyright 2012 Andres Riancho

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
import core.data.kb.info as info
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln

from core.controllers.basePlugin.baseInfrastructurePlugin import baseInfrastructurePlugin
from core.controllers.misc.decorators import runonce
from core.controllers.w3afException import w3afRunOnce


class find_jboss(baseInfrastructurePlugin):
    '''
    Find default Jboss installations.

    @author: Nahuel Sanchez (nsanchez@bonsai-sec.com)
    '''
    _jboss_vulns = (
        {'url': '/admin-console/', 
         'name': 'JBoss Admin Console enabled',
         'desc': 'Jboss Admin Console was found!',
         'type': 'info'},
        {'url': '/jmx-console/', 
         'name': 'JBoss JMX Console found',
         'desc': 'JMX Console found without Auth Enabled',
         'type': 'vuln'},
        {'url': '/status', 
         'name': 'JBoss Status Servlet found',
         'desc': 'JBoss Status Servlet gives valuable information',
         'type': 'info'},
        {'url': '/web-console/ServerInfo.jsp', 
         'name': 'WebConsole ServerInfo.jsp found',
         'desc': 'WebConsole ServerInfo.jsp gives valuable information',
         'type': 'info'},
        {'url': '/WebConsole/Invoker', 
         'name': 'WebConsole Invoker found',
         'desc': 'JBoss WebConsole Invoker enables attackers to send any JMX '
                    'command to JBoss AS',
         'type': 'vuln'},
        {'url': '/invoker/JMXInvokerServlet', 
         'name': 'JMX Invoker enabled without Auth',
         'desc': 'JMX Invoker enables attackers to send any JMX command to '
                    'JBoss AS',
         'type': 'vuln'}
        )
    
    def __init__(self):
        baseInfrastructurePlugin.__init__(self)
        self._fuzzable_requests_to_return = []
        
    @runonce(exc_class=w3afRunOnce)
    def discover(self, fuzzable_request):
        '''
        Checks if JBoss Interesting Directories exist in the target server.
        Also verifies some vulnerabilities.
        '''
        base_url = fuzzable_request.getURL().baseUrl()
        
        for vuln_db_instance in find_jboss._jboss_vulns:
            vuln_url = base_url.urlJoin( vuln_db_instance['url'] )
            response = self._uri_opener.GET(vuln_url)
            
            if response.getCode() == 200:
                
                if vuln_db_instance['type'] == 'info':
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setName(vuln_db_instance['name'])
                    i.setURL(vuln_url)
                    i.setId(response.id)
                    i.setDesc(vuln_db_instance['desc'])
                    kb.kb.append(self, vuln_db_instance['name'], i)
                    
                else:
                    v = vuln.vuln()
                    v.setPluginName(self.getName())
                    v.setName(vuln_db_instance['name'])
                    v.setURL(vuln_url)
                    v.setId(response.id)
                    v.setDesc(vuln_db_instance['desc'])
                    kb.kb.append(self, vuln_db_instance['name'], v)
                
                fuzzable_requests = self._create_fuzzable_requests(response)
                self._fuzzable_requests_to_return.extend(fuzzable_requests)
      
        return self._fuzzable_requests_to_return

    def handleUrlError(self, url_error):
        return (True, None)
    
    def getLongDesc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin identifies JBoss installation directories and possible
        security vulnerabilities.
        '''
