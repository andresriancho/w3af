"""
open_api.py

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
import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.kb.config as cf

from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.options.option_types import QUERY_STRING, HEADER, BOOL, INPUT_FILE
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.parsers.doc.open_api import OpenAPI
from w3af.core.data.db.disk_set import DiskSet
from w3af.core.data.kb.info import Info
from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.data.dc.headers import Headers
from w3af.core.data.url.HTTPResponse import HTTPResponse

import os.path


class open_api(CrawlPlugin):
    """
    Extract REST API calls from Open API specifications.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    FILENAMES = ['swagger.json',
                 'openapi.json',
                 'openapi.yaml']

    DIRECTORIES = ['/',
                   '/api/',
                   '/api/v2/',
                   '/api/v1/',
                   '/api/v2.0/',
                   '/api/v2.1/',
                   '/api/v1.0/',
                   '/api/v1.1/',
                   '/api/2.0/',
                   '/api/2.1/',
                   '/api/1.0/',
                   '/api/1.1/']

    def __init__(self):
        CrawlPlugin.__init__(self)

        # Internal variables
        self._first_run = True
        self._already_analyzed = DiskSet(table_prefix='open_api')

        # User configured variables
        self._query_string_auth = ''
        self._header_auth = ''
        self._no_spec_validation = False
        self._custom_spec_location = ''
        self._discover_fuzzable_headers = True

    def crawl(self, fuzzable_request):
        """
        Try to extract all the API endpoints from various locations
        if no custom location specified.

        :param fuzzable_request: A fuzzable_request instance that contains
                                (among other things) the URL to test.
        """
        self._enable_file_name_fuzzing()
        if self._has_custom_spec_location():
            self._analyze_custom_spec()
        else:
            self._analyze_common_paths(fuzzable_request)
            self._analyze_current_path(fuzzable_request)

    def _enable_file_name_fuzzing(self):
        """
        Enable file name fuzzing:

            http://w3af.org/api/1.0/pets/{fuzz-this-part}

        Users are not going to remember to enable this in misc-settings, and
        most of the APIs which are documented with Open API are REST APIs,
        so it makes sense to enable this automatically here.

        :return: None
        """
        if self._first_run:
            cf.cf.save('fuzz_url_filenames', True)
            cf.cf.save('fuzz_url_parts', True)

    def _should_analyze(self, url):
        """
        Makes sure that we only analyze a URL once, this reduces the number
        of HTTP requests and the CPU usage required for parsing the
        response

        :param url: The URL we want to analyze
        :return: True if we never analyzed this URL before
        """
        if url in self._already_analyzed:
            return False

        self._already_analyzed.add(url)
        return True

    def _analyze_common_paths(self, fuzzable_request):
        """
        Try to find the open api specification in the most common paths,
        extract all the REST API endpoints when found.

        This is run only the first time the plugin is called.

        :return: None, everything we find is sent to the core.
        """
        if not self._first_run:
            return

        self._first_run = False

        self.worker_pool.map(
            self._extract_api_calls,
            self._spec_url_generator_common(fuzzable_request)
        )

    def _extract_api_calls(self, spec_url):
        """
        HTTP GET the `spec_url` and try to parse it. Send all the newly found
        fuzzable requests to the core after adding any authentication data
        that might have been configured.

        :return: None
        """
        http_response = self._uri_opener.GET(spec_url, cache=True)

        if is_404(http_response):
            return

        self._extract_api_calls_from_response(spec_url, http_response)

    def _extract_api_calls_from_response(self, spec_url, http_response):
        """
        Try to parse an API specification from an HTTP response.
        Send all the newly found fuzzable requests to the core
        after adding any authentication data that might have been configured.

        :parm spec_url: A URL to API specification
        :param http_response: An HTTP response
        :return: None
        """
        if not OpenAPI.can_parse(http_response):
            return

        parser = OpenAPI(http_response,
                         self._no_spec_validation,
                         self._discover_fuzzable_headers)
        parser.parse()

        self._report_to_kb_if_needed(http_response, parser)
        self._send_spec_to_core(spec_url)

        for api_call in parser.get_api_calls():
            if not self._is_target_domain(api_call):
                continue

            api_call = self._set_authentication_data(api_call)
            self.output_queue.put(api_call)

    def _send_spec_to_core(self, spec_url):
        fuzzable_request = FuzzableRequest(spec_url, method='GET')
        self.output_queue.put(fuzzable_request)

    @staticmethod
    def _is_target_domain(fuzzable_request):
        """
        :param fuzzable_request: The api call as a fuzzable request
        :return: True if the target domain matches
        """
        targets = cf.cf.get('targets')
        if not targets:
            return False

        target_domain = targets[0].get_domain()
        api_call_domain = fuzzable_request.get_url().get_domain()

        if target_domain == api_call_domain:
            return True

        om.out.debug('The OpenAPI specification has operations which point'
                     ' to a domain (%s) outside the defined target (%s).'
                     ' Ignoring the operation to prevent scanning out of scope'
                     ' targets.' % (api_call_domain, target_domain))
        return False

    def _report_to_kb_if_needed(self, http_response, parser):
        """
        If the parser did find something, then we report it to the KB.

        :param http_response: The HTTP response that was parsed
        :param parser: The OpenAPI parser instance
        :return: None
        """
        if not parser.get_api_calls():
            return

        # Save it to the kb!
        desc = ('An Open API specification was found at: "%s", the scanner'
                ' was able to extract %s API endpoints which will be audited'
                ' for vulnerabilities.')
        desc %= (http_response.get_url(), len(parser.get_api_calls()))

        i = Info('Open API specification found', desc, http_response.id, self.get_name())
        i.set_url(http_response.get_url())

        kb.kb.append(self, 'open_api', i)
        om.out.information(i.get_desc())

        # Warn the user about missing credentials
        if self._query_string_auth or self._header_auth:
            return

        desc = ('An Open API specification was found at: "%s", but no credentials'
                ' were provided in the `open_api` plugin. The scanner will try'
                ' to audit the identified endpoints but coverage will most likely'
                ' be reduced due to missing authentication.')
        desc %= http_response.get_url()

        i = Info('Open API missing credentials', desc, http_response.id, self.get_name())
        i.set_url(http_response.get_url())

        kb.kb.append(self, 'open_api', i)
        om.out.information(i.get_desc())

    def _set_authentication_data(self, fuzzable_request):
        """
        :param fuzzable_request: The fuzzable request as returned by the parser

        :return: The same fuzzable request as before, but adding authentication
                 data configured by the user, such as headers and query string
                 parameters.
        """
        headers = fuzzable_request.get_headers()
        uri = fuzzable_request.get_uri()
        query_string = uri.get_querystring()

        if self._header_auth:
            for header_name, header_value in self._header_auth.iteritems():
                headers[header_name] = header_value

        if self._query_string_auth:
            for qs_param, qs_value in self._query_string_auth.iteritems():
                query_string[qs_param] = qs_value

        uri.set_querystring(query_string)

        fuzzable_request.set_uri(uri)
        fuzzable_request.set_headers(headers)

        return fuzzable_request

    def _spec_url_generator_common(self, fuzzable_request):
        """
        Generate the potential locations for the open api specification

        :param fuzzable_request: The fuzzable request we get from the core
        :return: URLs to test
        """
        base_url = fuzzable_request.get_url().base_url()

        for directory in self.DIRECTORIES:
            for filename in self.FILENAMES:
                spec_url = base_url.url_join('%s%s' % (directory, filename))

                if not self._should_analyze(spec_url):
                    continue

                yield spec_url

    def _spec_url_generator_current_path(self, fuzzable_request):
        """
        Generate the potential locations for the open api specification
        based on the current path

        :param fuzzable_request: The fuzzable request we get from the core
        :return: URLs to test
        """
        url = fuzzable_request.get_url()

        # If the user set the swagger.json URL as target, we want to test it
        if self._should_analyze(url):
            yield url

        # Now we create some URLs based on the received URL
        for directory_url in url.get_directories():
            for filename in self.FILENAMES:
                spec_url = directory_url.url_join(filename)

                if not self._should_analyze(spec_url):
                    continue

                yield spec_url

    def _analyze_current_path(self, fuzzable_request):
        """
        Try to find the common files in the current path.

        This is faster than `_analyze_common_paths` since it doesn't test all
        the directories (such as /api/ , /api/v2/, etc).

        :return: None, we send everything we find to the core.
        """
        self.worker_pool.map(
            self._extract_api_calls,
            self._spec_url_generator_current_path(fuzzable_request)
        )

    def _has_custom_spec_location(self):
        """
        Checks if the plugin is configured to use a custom API specification
        from a local file.

        :return: True if the plugin is configured to read a custom API spec
        """
        return self._custom_spec_location != ''

    def _analyze_custom_spec(self):
        """
        Loads a custom API specification from a local file, and try to parse it.

        :return: None
        """
        if not self._first_run:
            return
        self._first_run = False

        url = URL('file://%s' % os.path.abspath(self._custom_spec_location))

        ext = os.path.splitext(self._custom_spec_location)[1][1:].lower()
        if ext not in ('yaml', 'json'):
            om.out.error('Skip loading custom API spec '
                         'because of unknown file extension: %s' % ext)
            return

        with open(self._custom_spec_location, 'r') as f:
            custom_spec_as_string = f.read()

        headers = Headers([('content-type', 'application/%s' % ext)])
        http_response = HTTPResponse(200, custom_spec_as_string, headers, url, url, _id=1)

        self._extract_api_calls_from_response(url, http_response)

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Query string parameters to add in each API request'
        h = ('Some REST APIs use query string parameters, such as `api_key`'
             ' for authentication. Set this parameter to configure one or more'
             ' query string parameters which will be added to each API HTTP'
             ' request. An example value for this field is: "api_key=0x12345"')
        o = opt_factory('query_string_auth', self._query_string_auth, d, QUERY_STRING, help=h)
        ol.add(o)

        d = 'Headers to add in each API request'
        h = ('Some REST APIs use HTTP headers, such as `X-Authenticate` or `Basic`'
             ' for authentication. Set this parameter to configure one or more'
             ' HTTP headers which will be added to each API request.'
             ' An example value for this field is: "Basic: bearer 0x12345"')
        o = opt_factory('header_auth', self._header_auth, d, HEADER, help=h)
        ol.add(o)

        d = 'Disable Open API spec validation'
        h = 'By default, the plugin validates Open API specification before extracting endpoints.'
        o = opt_factory('no_spec_validation', self._no_spec_validation, d, BOOL, help=h)
        ol.add(o)

        d = 'Path to Open API specification'
        h = ('By default, the plugin looks for the API specification on the target,'
             ' but sometimes applications do not provide an API specification.'
             ' Set this parameter to specify a local path to the API specification.'
             ' The file must have .json or .yaml extension.')
        o = opt_factory('custom_spec_location', self._custom_spec_location, d, INPUT_FILE, help=h)
        ol.add(o)

        d = 'Automatic HTTP header discovery for further testing'
        h = ('By default, the plugin looks for parameters which are passed to endpoints via HTTP headers,'
             ' and enables them for further testing.'
             ' Set this options to False if you would like to disable this feature.'
             ' You can also set `misc-settings.fuzzable_headers` option to test only specific headers.')
        o = opt_factory('discover_fuzzable_headers', self._discover_fuzzable_headers, d, BOOL, help=h)
        ol.add(o)

        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._query_string_auth = options_list['query_string_auth'].get_value()
        self._header_auth = options_list['header_auth'].get_value()
        self._no_spec_validation = options_list['no_spec_validation'].get_value()
        self._custom_spec_location = options_list['custom_spec_location'].get_value()
        self._discover_fuzzable_headers = options_list['discover_fuzzable_headers'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin parses Open API specification documents, allowing the
        scanner to perform the audit process on REST APIs.
        
        The plugin will try to identify the Open API specification file in
        multiple files and directories, such as:
            * swagger.json
            * openapi.json
            * openapi.yaml

        To provide the required information, the user can also set
        the Open API specification URL as the scan target,
        or set 'custom_spec_location' configuration parameter
        to provide a path to a local file which contains the specification.
        
        Most APIs require authentication, this plugin supports authentication
        using query string parameters and HTTP headers. The user can configure
        them using these configuration parameters:
            * query_string_auth
            * header_auth

        By default, the plugin validates Open API specification.
        The validation may be disabled by 'no_spec_validation' configuration parameter.

        During parsing an Open API specification, the plugin looks for parameters
        which are passed to endpoints via HTTP headers, and enables them for further testing.
        This behavior may be disabled by setting 'discover_fuzzable_headers' configuration parameter to False.
        """
