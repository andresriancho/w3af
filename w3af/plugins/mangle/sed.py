"""
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

"""
import re

import w3af.core.controllers.output_manager as om

from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.dc.headers import Headers

from w3af.core.controllers.plugins.mangle_plugin import ManglePlugin
from w3af.core.controllers.exceptions import BaseFrameworkException


class sed(ManglePlugin):
    """
    This plugin is a "stream editor" for http requests and responses.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        ManglePlugin.__init__(self)
        self._manglers = {'q': {'b': set(), 'h': set()},
                          's': {'b': set(), 'h': set()},}
        
        # User options
        self._user_option_fix_content_len = True
        self._expressions = ''

    def mangle_request(self, request):
        """
        This method mangles the request.

        :param request: This is the request to mangle.
        :return: A mangled version of the request.
        """
        data = request.get_data()
        for regex, string in self._manglers['q']['b']:
            data = regex.sub(string, data)

        header_string = str(request.get_headers())
        
        for regex, string in self._manglers['q']['h']:
            header_string = regex.sub(string, header_string)
        
        headers_inst = Headers.from_string(header_string)

        request.set_headers(headers_inst)
        request.add_data(data)
        return request

    def mangle_response(self, response):
        """
        This method mangles the response.

        :param response: This is the response to mangle.
        :return: A mangled version of the response.
        """
        body = response.get_body()

        for regex, string in self._manglers['s']['b']:
            body = regex.sub(string, body)

        response.set_body(body)

        header_string = str(response.get_headers())

        for regex, string in self._manglers['s']['h']:
            header_string = regex.sub(string, header_string)

        try:
            mangled_header = Headers.from_string(header_string)
        except ValueError:
            error = 'Your header modifications created an invalid header'\
                    ' string that could NOT be parsed back to a Header object.'
            om.out.error(error)
        else:
            response.set_headers(mangled_header)

        if self._user_option_fix_content_len:
            response = self._fix_content_len(response)

        return response

    def set_options(self, option_list):
        """
        Sets the Options given on the OptionList to self. The options are the
        result of a user entering some data on a window that was constructed
        using the XML Options that was retrieved from the plugin using
        get_options()

        This method MUST be implemented on every plugin.

        :return: No value is returned.
        """
        self._user_option_fix_content_len = option_list['fix_content_len'].get_value()

        self._expressions = ','.join(option_list['expressions'].get_value())
        found_expressions = re.findall('([qs])([bh])/(.*?)/(.*?)/;?',
                                       self._expressions)

        if len(found_expressions) == 0 and len(option_list['expressions'].get_value()) != 0:
            msg = 'The user specified expression is invalid.'
            raise BaseFrameworkException(msg)

        for exp in found_expressions:
            req_res, body_header, regex_str, target_str = exp

            if req_res not in ('q', 's'):
                msg = 'The first letter of the sed expression should be "q"'\
                      ' for indicating request or "s" for response, got "%s"'\
                      ' instead.'
                raise BaseFrameworkException(msg % req_res)

            if body_header not in ('b', 'h'):
                msg = 'The second letter of the expression should be "b"'\
                      ' for body or "h" for header, got "%s" instead.'
                raise BaseFrameworkException(msg % body_header)

            try:
                regex = re.compile(regex_str)
            except re.error, re_err:
                msg = 'Regular expression compilation error at "%s", the'\
                      ' original exception was "%s".'
                raise BaseFrameworkException(msg % (regex_str, re_err))

            self._manglers[req_res][body_header].add((regex, target_str))

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Stream edition expressions'
        h = ('Stream edition expressions are strings that tell the sed plugin'
             ' which transformations to apply to the HTTP requests and'
             ' responses. The sed plugin uses regular expressions, some'
             ' examples:\n'
             '\n'
             '    - qh/User/NotLuser/\n'
             '      This will make sed search in the the re[q]uest [h]eader'
             ' for the string User and replace it with NotLuser.\n'
             '\n'
             '    - sb/[fF]orm/form\n'
             '      This will make sed search in the re[s]ponse [b]ody for'\
             ' the strings form or Form and replace it with form.\n'
             '\n'
             'Multiple expressions can be specified separated by commas.')
        o = opt_factory('expressions', self._expressions, d, 'list', help=h)
        ol.add(o)

        d = 'Fix the content length header after mangling'
        o = opt_factory('fix_content_len', self._user_option_fix_content_len,
                        d, 'boolean')
        ol.add(o)

        return ol

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin is a stream editor for web requests and responses.

        Two configurable parameters exist:
            - expressions
            - fix_content_len

        Stream edition expressions are strings that tell the sed plugin which
        transformations to apply to the HTTP requests and responses. The sed
        plugin uses regular expressions, some examples:
        
            - qh/User/NotLuser/
            This will make sed search in the the re[q]uest [h]eader for the
            string User and replace it with NotLuser.
            
            - sb/[fF]orm/form
            This will make sed search in the re[s]ponse [b]ody for the strings
            form or Form and replace it with form.
        
        Multiple expressions can be specified separated by commas.
        """