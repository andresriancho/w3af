"""
serialized_object.py

Copyright 2018 Andres Riancho

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
import zlib
import itertools

from collections import deque

import w3af.core.data.constants.severity as severity
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.misc.encoding import smart_str_ignore
from w3af.core.data.misc.base64_nopadding import maybe_decode_base64
from w3af.core.data.dc.cookie import Cookie
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.kb.info_set import InfoSet
from w3af.core.data.dc.factory import dc_from_hdrs_post


class serialized_object(GrepPlugin):
    """
    Find serialized objects sent by the Web application

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    CACHE_MAX_SIZE = 100

    SERIALIZED_OBJECT_RE = {
        'PHP': [
            re.compile('^(a|O):\d{1,3}:({[sai]|")'),
        ]
    }

    def __init__(self):
        GrepPlugin.__init__(self)
        self._cache = deque()

    def grep(self, request, response):
        """
        Plugin entry point. Search for private IPs in the header and the body.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None, results are saved to the kb.
        """
        for parameter_name, parameter_value in self._get_all_parameters(request):

            # Performance enhancement
            if self._should_skip_analysis(parameter_value):
                continue

            for language, regular_expressions in self.SERIALIZED_OBJECT_RE.iteritems():
                for serialized_object_re in regular_expressions:

                    self._analyze_param(request,
                                        response,
                                        parameter_name,
                                        parameter_value,
                                        language,
                                        serialized_object_re)

    def _should_skip_analysis(self, parameter_value):
        """
        This method was introduced to improve the overall performance of the
        serialized_object plugin. It tried to prevent the multiple regular
        expressions from being applied against strings which we know (with
        a good degree of certainty) that will not be a serialized object.

        This method also has a small cache to prevent analyzing the same
        parameter value multiple times.

        :param parameter_value: The parameter value to inspect
        :return: True if we should skip analysis phase for this parameter
        """
        if len(parameter_value) <= 16:
            # Really short strings can't contain a serialized object
            return True

        pv_hash = zlib.adler32(parameter_value)

        if pv_hash in self._cache:
            # The parameter value was found in the cache, this means that it is
            # not the first time we see / analyze this parameter value (at least
            # not recently), so lets skip!
            return True

        # The parameter value hash will be analyzed, but I only want to do that
        # once (at least for some time) so I add the hash to the cache:
        self._cache.append(pv_hash)

        # Keep the cache size under control. For each append() call we make, also
        # run a popleft() if the cache max size was reached
        if len(self._cache) >= self.CACHE_MAX_SIZE:
            self._cache.popleft()

        return False

    def _analyze_param(self, request, response, parameter_name, parameter_value,
                       language, serialized_object_re):
        """
        Check if one parameter holds a serialized object

        :param request: The HTTP request which holds the parameter
        :param response: The HTTP response
        :param parameter_name: The name of the parameter
        :param parameter_value: The parameter value (might have been decoded from b64)
        :param language: The programming language
        :param serialized_object_re: The regular expression to match
        :return: None. We just save the vulnerability to the KB
        """
        try:
            match_object = serialized_object_re.search(parameter_value)
        except Exception, e:
            args = (e, parameter_value)
            om.out.debug('An exception was found while trying to find a'
                         ' serialized object in a parameter value. The exception'
                         ' is: "%s", and the parameter value is: "%r"' % args)
            return

        if not match_object:
            return

        # We found a match! The parameter value is a serialized object
        # Just report this to get the user's attention
        desc = ('Identified a %s serialized object being sent by the web'
                ' application in a request to "%s" in a parameter named "%s".'
                ' While this is not a vulnerability by itself, it is a strong'
                ' indicator of potential insecure deserialization issues.')
        desc %= (language, request.get_url(), parameter_name)

        v = Vuln('Serialized object', desc, severity.LOW, response.id, self.get_name())

        v.set_url(response.get_url())
        v.add_to_highlight(parameter_value)
        v[SerializedObjectInfoSet.ITAG] = parameter_name

        self.kb_append_uniq_group(self,
                                  'serialized_object', v,
                                  group_klass=SerializedObjectInfoSet)

    def _get_all_parameters(self, request):
        """
        :param request: The HTTP request
        :yield: All the HTTP request parameters as tuples of (name, value)
        """
        headers = request.get_headers()
        query_string = request.get_uri().get_querystring()
        dc = dc_from_hdrs_post(headers, request.get_data())

        cookie_str, _ = headers.iget('cookie', '')
        cookie_dc = Cookie(cookie_str)

        token_generators = itertools.chain(
            query_string.iter_tokens(),
            dc.iter_tokens(),
            headers.iter_tokens(),
            cookie_dc.iter_tokens()
        )

        for token in token_generators:
            token_name = token.get_name()

            token_value = token.get_value()
            token_value = smart_str_ignore(token_value)

            yield token_name, token_value

            # Handle the case where the parameter is base64 encoded
            is_b64, decoded_data = maybe_decode_base64(token_value)
            if is_b64:
                yield token_name, decoded_data

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin identifies serialized objects in HTTP request parameters.
        
        While sending serialized objects in HTTP requests is not a vulnerability
        by itself, these objects could be abused by an attacker to perform 
        attacks such as PHP Object Injection.
        """


class SerializedObjectInfoSet(InfoSet):
    ITAG = 'parameter_name'
    TEMPLATE = (
        'A total of {{ uris|length }} HTTP requests contained a serialized'
        ' object in the parameter with name "{{ parameter_name }}". The first'
        ' ten matching URLs are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )
