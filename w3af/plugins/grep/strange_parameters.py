"""
strange_parameters.py

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
import urllib

import w3af.core.data.parsers.parser_cache as parser_cache
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.misc.encoding import smart_str_ignore
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.kb.info import Info
from w3af.core.data.kb.vuln import Vuln


class strange_parameters(GrepPlugin):
    """
    Grep the HTML response and find URIs that have strange parameters.

    :author: Andres Riancho ((andres.riancho@gmail.com))
    """
    STRANGE_RE_CHARS = re.compile(r'([a-zA-Z0-9. ]+)')

    STRANGE_RE_LIST = [re.compile(r'\w+\(.*?\)')]

    SQL_RE = re.compile(r'(SELECT .*? FROM|'
                        r'INSERT INTO .*? VALUES|'
                        r'UPDATE .*? SET .*? WHERE)', re.IGNORECASE)

    def __init__(self):
        GrepPlugin.__init__(self)

        # Internal variables
        self._already_reported = ScalableBloomFilter()

    def grep(self, request, response):
        """
        Plugin entry point.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None, all results are saved in the kb.
        """
        try:
            dp = parser_cache.dpc.get_document_parser_for(response)
        except BaseFrameworkException:
            return

        # Note:
        #
        # - With parsed_references I'm 100% that it's really something in the
        #   HTML that the developer intended to add.
        #
        # - The re_references are the result of regular expressions, which in
        #   some cases are just false positives.
        #
        parsed_references, _ = dp.get_references()
        analyzers = {self._analyze_SQL, self._analyze_strange}

        for ref in parsed_references:
            for token in ref.querystring.iter_tokens():

                token_name = token.get_name()
                token_value = token.get_value()

                if (ref.uri2url(), token_name) in self._already_reported:
                    continue

                for analyzer in analyzers:
                    if analyzer(request, response, ref, token_name, token_value):
                        # Don't repeat findings
                        self._already_reported.add((ref.uri2url(), token_name))

    def _analyze_strange(self, request, response, ref, token_name, token_value):
        if not self._is_strange(request, token_name, token_value):
            return False

        if request.sent(token_value):
            return False

        desc = ('The URI: "%s" has a parameter named: "%s" with value:'
                ' "%s", which is very uncommon and requires manual'
                ' inspection.')
        args = (response.get_uri(), token_name, token_value)
        args = tuple(smart_str_ignore(i) for i in args)
        desc %= args

        i = Info('Uncommon query string parameter', desc, response.id,
                 self.get_name())
        i['parameter_value'] = token_value
        i.add_to_highlight(token_value)
        i.set_uri(ref)

        self.kb_append(self, 'strange_parameters', i)
        return True

    def _analyze_SQL(self, request, response, ref, token_name, token_value):
        """
        To find these kinds of vulnerabilities

        http://thedailywtf.com/Articles/Oklahoma-Leaks-Tens-of-Thousands-of-Social-Security-Numbers,-Other-Sensitive-Data.aspx

        :return: True if the parameter value contains SQL sentences
        """
        for match in self.SQL_RE.findall(token_value):
            if request.sent(match):
                continue

            desc = ('The URI: "%s" has a parameter named: "%s" with value:'
                    ' "%s", which is a SQL query.')
            desc %= (response.get_uri(), token_name, token_value)

            v = Vuln('Parameter has SQL sentence', desc, severity.LOW,
                     response.id, self.get_name())
            v['parameter_value'] = token_value
            v.add_to_highlight(token_value)
            v.set_uri(ref)

            self.kb_append(self, 'strange_parameters', v)
            return True

        return False

    def _is_strange(self, request, parameter, value):
        """
        :return: True if the parameter value is strange
        """
        decoded_value = urllib.unquote(value)
        decoded_parameter = urllib.unquote(parameter)

        #
        # Parameters holding URLs will always be flagged as "strange" because
        # they contain multiple "special characters", but we don't care about
        # them enough to report them
        #
        if decoded_value.startswith('http://'):
            return False

        if decoded_value.startswith('https://'):
            return False

        #
        # The wicket framework uses strange URLs like this by design:
        #
        # https://www.DOMAIN.com/
        #     ?wicket:bookmarkablePage=:com.DOMAIN.web.pages.SignInPage
        #     &wicket:interface=:0:signInForm::IFormSubmitListener::
        #     ;jsessionid=7AC76A46A86BBC3F5253E374241BC892
        #
        # Which are strange in all cases, except from wicket!
        #
        if 'wicket:' in parameter or 'wicket:' in decoded_parameter:
            return False

        #
        # Match specific things such as function calls
        #
        for regex in self.STRANGE_RE_LIST:
            for match in regex.findall(value):
                if not request.sent(match):
                    return True

        #
        # Split the parameter by any character that is not A-Za-z0-9 and if
        # the length is greater than X then report it
        #
        split_value = [x for x in self.STRANGE_RE_CHARS.split(value) if x != '']
        if len(split_value) > 4:
            if not request.sent(value):
                return True

        return False

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps all responses and tries to identify URIs with strange
        parameters, some examples of strange parameters are:
            - http://a/?b=method(a,c)
            - http://a/?c=x|y|z|d
        """
