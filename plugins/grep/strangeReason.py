'''
strangeReason.py

Copyright 2009 Andres Riancho

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

from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

class strangeReason(baseGrepPlugin):
    '''
    Analyze HTTP response reason (Not Found, Ok, Internal Server Error).
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self):
        baseGrepPlugin.__init__(self)
        self._w3c_reasons = {
            100: 'Continue',
            101: 'Switching Protocols',

            200: 'OK',
            201: 'Created',
            202: 'Accepted',
            203: 'Non-Authoritative Information',
            204: 'No Content',
            205: 'Reset Content',
            206: 'Partial Content',

            300: 'Multiple Choices',
            301: 'Moved Permanently',
            302: 'Found',
            303: 'See Other',
            304: 'Not Modified',
            305: 'Use Proxy',
            306: '(Unused)',
            307: 'Temporary Redirect',

            400: 'Bad Request',
            401: 'Unauthorized',
            402: 'Payment Required',
            403: 'Forbidden',
            404: 'Not Found',
            405: 'Method Not Allowed',
            406: 'Not Acceptable',
            407: 'Proxy Authentication Required',
            408: 'Request Timeout',
            409: 'Conflict',
            410: 'Gone',
            411: 'Length Required',
            412: 'Precondition Failed',
            413: 'Request Entity Too Large',
            414: 'Request-URI Too Long',
            415: 'Unsupported Media Type',
            416: 'Requested Range Not Satisfiable',
            417: 'Expectation Failed',

            500: 'Internal Server Error',
            501: 'Not Implemented',
            502: 'Bad Gateway',
            503: 'Service Unavailable',
            504: 'Gateway Timeout',
            505: 'HTTP Version Not Supported',
        }
        
    def grep(self, request, response):
        '''
        Plugin entry point. Analyze if the HTTP response reason messages are strange.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None, all results are saved in the kb.
        '''
        if response.getCode() in self._w3c_reasons:
            
            w3c_reason = self._w3c_reasons[response.getCode()]
            w3c_reason = w3c_reason.lower()
            
            response_reason = response.getMsg().lower()
            
            if response_reason != w3c_reason:
                #
                #   I check if the kb already has a info object with this code:
                #
                strange_reason_infos = kb.kb.getData('strangeReason', 'strangeReason')
                
                corresponding_info = None
                for info_obj in strange_reason_infos:
                    if info_obj['reason'] == response.getMsg():
                        corresponding_info = info_obj
                        break
                
                if corresponding_info:
                    # Work with the "old" info object:
                    id_list = corresponding_info.getId()
                    id_list.append( response.id )
                    corresponding_info.setId( id_list )
                    
                else:
                    # Create a new info object from scratch and save it to the kb:
                    i = info.info()
                    i.setName('Strange HTTP Reason message - ' + str(response.getMsg()))
                    i.setURL( response.getURL() )
                    i.setId( response.id )
                    i['reason'] = response.getMsg()
                    desc = 'The remote Web server sent a strange HTTP reason message: "'
                    desc += str(response.getMsg()) + '" manual inspection is advised.'
                    i.setDesc( desc )
                    i.addToHighlight( response.getMsg() )
                    kb.kb.append( self , 'strangeReason' , i )
    
    def setOptions( self, OptionList ):
        pass
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.printUniq( kb.kb.getData( 'strangeReason', 'strangeReason' ), 'URL' )

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
        Analyze HTTP response reason messages sent by the remote web application and report uncommon
        findings.
        '''
