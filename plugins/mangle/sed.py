'''
sed.py

Copyright 2006 Andres Riancho

This file is part of w3af, http://w3af.org/ .

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
import re

import core.controllers.output_manager as om

from core.data.options.opt_factory import opt_factory
from core.data.options.option_list import OptionList
from core.data.request.factory import create_fuzzable_request_from_parts
from core.data.dc.headers import Headers

from core.controllers.plugins.mangle_plugin import ManglePlugin
from core.controllers.exceptions import w3afException


class sed(ManglePlugin):
    '''
    This plugin is a "stream editor" for http requests and responses.

    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        ManglePlugin.__init__(self)
        self._req_body_manglers = []
        self._req_head_manglers = []
        self._res_body_manglers = []
        self._res_head_manglers = []

        # User options
        self._user_option_fix_content_len = True
        self._priority = 20
        self._expressions = ''

    def mangle_request(self, request):
        '''
        This method mangles the request.

        @param request: This is the request to mangle.
        @return: A mangled version of the request.
        '''
        data = request.get_data()
        for regex, string in self._req_body_manglers:
            data = regex.sub(string, data)

        header_string = str(request.get_headers())
        
        for regex, string in self._req_head_manglers:
            header_string = regex.sub(string, header_string)
        
        headers_inst = Headers.from_string(header_string)

        return create_fuzzable_request_from_parts(
                                                  request.get_url(),
                                                  request.get_method(),
                                                  data, headers_inst
                                                  )

    def mangle_response(self, response):
        '''
        This method mangles the response.

        @param response: This is the response to mangle.
        @return: A mangled version of the response.
        '''
        body = response.get_body()

        for regex, string in self._res_body_manglers:
            body = regex.sub(string, body)

        response.set_body(body)

        header_string = str(response.get_headers())

        for regex, string in self._res_head_manglers:
            header_string = regex.sub(string, header_string)

        try:
            mangled_header = Headers.from_string(header_string)
        except ValueError:
            error = 'Your header modifications created an invalid header string'\
                    ' that could NOT be parsed back to a Header object.'
            om.out.error(error)
        else:
            response.set_headers(mangled_header)

        if self._res_body_manglers and self._user_option_fix_content_len:
            response = self._fixContentLen(response)

        return response

    def set_options(self, option_list):
        '''
        Sets the Options given on the OptionList to self. The options are the
        result of a user entering some data on a window that was constructed
        using the XML Options that was retrieved from the plugin using
        get_options()

        This method MUST be implemented on every plugin.

        @return: No value is returned.
        '''
        self._user_option_fix_content_len = option_list[
            'fixContentLen'].get_value()
        self._priority = option_list['priority'].get_value()

        self._expressions = ','.join(option_list['expressions'].get_value())
        self._expressions = re.findall(
            '([qs])([bh])/(.*?)/(.*?)/;?', self._expressions)

        if len(self._expressions) == 0 and len(option_list['expressions'].get_value()) != 0:
            raise w3afException('The user specified expression is invalid.')

        for exp in self._expressions:
            if exp[0] not in ['q', 's']:
                msg = 'The first letter of the sed expression should be q(reQuest) or s(reSponse).'
                raise w3afException(msg)

            if exp[1] not in ['b', 'h']:
                msg = 'The second letter of the sed expression should be b(body) or h(header).'
                raise w3afException(msg)

            try:
                regex = re.compile(exp[2])
            except:
                raise w3afException(
                    'Invalid regular expression in sed plugin.')

            if exp[0] == 'q':
                # The expression mangles the request
                if exp[1] == 'b':
                    self._req_body_manglers.append((regex, exp[3]))
                else:
                    self._req_head_manglers.append((regex, exp[3]))
            else:
                # The expression mangles the response
                if exp[1] == 'b':
                    self._res_body_manglers.append((regex, exp[3]))
                else:
                    self._res_head_manglers.append((regex, exp[3]))

    def get_options(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Stream edition expressions'
        h1 = 'Stream edition expressions are strings that tell the sed plugin what to change.'
        h1 += ' Sed plugin uses regular expressions, some examples: \n - qh/User/NotLuser/ ;'
        h1 += ' This will make sed search in the the re[q]uest [h]eader for the string User'
        h1 += ' and replace it with NotLuser.\n - sb/[fF]orm/form ; This will make sed search'
        h1 += ' in the re[s]ponse [b]ody for the strings form or Form and replace it with form.'
        h1 += ' Multiple expressions can be specified separated by commas.'
        o1 = opt_factory('expressions', self._expressions, d1, 'list', help=h1)

        d2 = 'Fix the content length header after mangling'
        o2 = opt_factory(
            'fixContentLen', self._user_option_fix_content_len, d2, 'boolean')

        d3 = 'Plugin execution priority'
        h3 = 'Mangle plugins are ordered using the priority parameter'
        o3 = opt_factory('priority', self._priority, d3, 'integer', help=h3)

        ol = OptionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        return ol

    def get_priority(self):
        '''
        This function is called when sorting mangle plugins.
        Each mangle plugin should implement this.

        @return: An integer specifying the priority. 100 is run first, 0 last.
        '''
        return self._priority

    def get_long_desc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin is a stream editor for web requests and responses.

        Three configurable parameters exist:
            - priority
            - expressions
            - fixContentLen

        Stream edition expressions are strings that tell the sed plugin what to change. Sed plugin
        uses regular expressions, some examples:
            - qh/User/NotLuser/
                This will make sed search in the the re[q]uest [h]eader for the string User and
                replace it with NotLuser.

            - sb/[fF]orm/form
                This will make sed search in the re[s]ponse [b]ody for the strings form or Form
                and replace it with form.

        Multiple expressions can be specified separated by commas.
        '''
