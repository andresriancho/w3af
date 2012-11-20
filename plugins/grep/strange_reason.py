'''
strange_reason.py

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
import core.data.kb.knowledge_base as kb
import core.data.kb.info as info

from core.controllers.plugins.grep_plugin import GrepPlugin


class strange_reason(GrepPlugin):
    '''
    Analyze HTTP response reason (Not Found, Ok, Internal Server Error).

    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    W3C_REASONS = {
        100: ['continue', ],
        101: ['switching protocols', ],

        200: ['ok', ],
        201: ['created', ],
        202: ['accepted', ],
        203: ['non-authoritative information', ],
        204: ['no content', ],
        205: ['reset content', ],
        206: ['partial content', ],

        300: ['multiple choices', ],
        301: ['moved permanently', ],
        302: ['found', ],
        303: ['see other', ],
        304: ['not modified', ],
        305: ['use proxy', ],
        306: ['(unused)', ],
        307: ['temporary redirect', ],

        400: ['bad request', ],
        401: ['unauthorized', 'authorization required'],
        402: ['payment required', ],
        403: ['forbidden', ],
        404: ['not found', ],
        405: ['method not allowed', 'not allowed'],
        406: ['not acceptable', ],
        407: ['proxy authentication required', ],
        408: ['request timeout', ],
        409: ['conflict', ],
        410: ['gone', ],
        411: ['length required', ],
        412: ['precondition failed', ],
        413: ['request entity too large', ],
        414: ['request-uri too long', ],
        415: ['unsupported media type', ],
        416: ['requested range not satisfiable', ],
        417: ['expectation failed', ],

        500: ['internal server error', ],
        501: ['not implemented', ],
        502: ['bad gateway', ],
        503: ['service unavailable', ],
        504: ['gateway timeout', ],
        505: ['http version not supported', ],
    }

    def __init__(self):
        GrepPlugin.__init__(self)

    def grep(self, request, response):
        '''
        Plugin entry point. Analyze if the HTTP response reason messages are strange.

        @param request: The HTTP request object.
        @param response: The HTTP response object
        @return: None, all results are saved in the kb.
        '''
        response_code = response.get_code()
        msg_list = self.W3C_REASONS.get(response_code, None)

        if msg_list is not None:

            response_reason = response.get_msg().lower()

            if response_reason not in msg_list:
                #
                #   I check if the kb already has a info object with this code:
                #
                strange_reason_infos = kb.kb.get(
                    'strange_reason', 'strange_reason')

                corresponding_info = None
                for info_obj in strange_reason_infos:
                    if info_obj['reason'] == response.get_msg():
                        corresponding_info = info_obj
                        break

                if corresponding_info:
                    # Work with the "old" info object:
                    id_list = corresponding_info.get_id()
                    id_list.append(response.id)
                    corresponding_info.set_id(id_list)

                else:
                    # Create a new info object from scratch and save it to the kb:
                    i = info.info()
                    i.set_plugin_name(self.get_name())
                    i.set_name('Strange HTTP Reason message - ' +
                               str(response.get_msg()))
                    i.set_url(response.get_url())
                    i.set_id(response.id)
                    i['reason'] = response.get_msg()
                    desc = 'The remote Web server sent a strange HTTP reason message: "'
                    desc += str(
                        response.get_msg()) + '" manual inspection is advised.'
                    i.set_desc(desc)
                    i.add_to_highlight(response.get_msg())
                    kb.kb.append(self, 'strange_reason', i)

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.print_uniq(kb.kb.get('strange_reason', 'strange_reason'), 'URL')

    def get_long_desc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        Analyze HTTP response reason messages sent by the remote web application
        and report uncommon findings.
        '''
