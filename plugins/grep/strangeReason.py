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
            100: ['continue',],
            101: ['switching protocols',],

            200: ['ok',],
            201: ['created',],
            202: ['accepted',],
            203: ['non-authoritative information',],
            204: ['no content',],
            205: ['reset content',],
            206: ['partial content',],

            300: ['multiple choices',],
            301: ['moved permanently',],
            302: ['found',],
            303: ['see other',],
            304: ['not modified',],
            305: ['use proxy',],
            306: ['(unused)',],
            307: ['temporary redirect',],

            400: ['bad request',],
            401: ['unauthorized', 'authorization required'],
            402: ['payment required',],
            403: ['forbidden',],
            404: ['not found',],
            405: ['method not allowed','not allowed'],
            406: ['not acceptable',],
            407: ['proxy authentication required',],
            408: ['request timeout',],
            409: ['conflict',],
            410: ['gone',],
            411: ['length required',],
            412: ['precondition failed',],
            413: ['request entity too large',],
            414: ['request-uri too long',],
            415: ['unsupported media type',],
            416: ['requested range not satisfiable',],
            417: ['expectation failed',],

            500: ['internal server error',],
            501: ['not implemented',],
            502: ['bad gateway',],
            503: ['service unavailable',],
            504: ['gateway timeout',],
            505: ['http version not supported',],
        }
        
    def grep(self, request, response):
        '''
        Plugin entry point. Analyze if the HTTP response reason messages are strange.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None, all results are saved in the kb.
        '''
        if response.getCode() in self._w3c_reasons:
            
            w3c_reason_list = self._w3c_reasons[ response.getCode() ]
            
            response_reason = response.getMsg().lower()
            
            if response_reason not in w3c_reason_list:
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
                    i.setPluginName(self.getName())
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
