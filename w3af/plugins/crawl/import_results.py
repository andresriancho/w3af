"""
import_results.py

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
import os
import base64

from lxml import etree
from lxml.etree import XMLSyntaxError

import w3af.core.controllers.output_manager as om
from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.exceptions import RunOnce, BaseFrameworkException
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import INPUT_FILE
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.parsers.doc.http_request_parser import http_request_parser


class import_results(CrawlPlugin):
    """
    Import HTTP requests found by output.export_requests and Burp
    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):
        super(import_results, self).__init__()

        # User configured parameters
        self._input_base64 = ''
        self._input_burp = ''

    @runonce(exc_class=RunOnce)
    def crawl(self, fuzzable_request, debugging_id):
        """
        Read the input file, and create the fuzzable_request_list based on that
        information.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
                                    In this case it is simply ignored and data
                                    is read from the input files.
        """
        self._load_data_from_base64()
        self._load_data_from_burp()

    def _load_data_from_base64(self):
        """
        Load data from the base64 file
        """
        if not self._input_base64:
            return

        if not os.path.isfile(self._input_base64):
            return

        try:
            file_handler = file(self._input_base64, 'rb')
        except BaseFrameworkException, e:
            msg = 'An error was found while trying to read "%s": "%s".'
            om.out.error(msg % (self._input_base64, e))
            return

        for line in file_handler:
            line = line.strip()

            # Support empty lines
            if not line:
                continue

            # Support comments
            if line.startswith('#'):
                continue

            try:
                fuzzable_request = FuzzableRequest.from_base64(line)
            except ValueError:
                om.out.debug('Invalid import_results input: "%r"' % line)
            else:
                self.output_queue.put(fuzzable_request)

    def _load_data_from_burp(self):
        """
        Load data from Burp's log
        """
        if not self._input_burp:
            return

        if not os.path.isfile(self._input_burp):
            return

        try:
            fuzzable_request_list = self._objs_from_burp_log(self._input_burp)
        except BaseFrameworkException, e:
            msg = ('An error was found while trying to read the Burp log'
                   ' file (%s): "%s".')
            om.out.error(msg % (self._input_burp, e))
        else:
            for fr in fuzzable_request_list:
                self.output_queue.put(fr)

    def _objs_from_burp_log(self, burp_file):
        """
        Read a burp log (XML) and extract the information.
        """
        xp = BurpParser()
        parser = etree.XMLParser(target=xp, resolve_entities=False)

        try:
            requests = etree.fromstring(file(burp_file).read(), parser)
        except XMLSyntaxError, xse:
            msg = ('The Burp input file is not a valid XML document. The'
                   ' parser error is: "%s"')
            om.out.error(msg % xse)
            return []

        return requests

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Base64 input file from which to create the fuzzable requests'
        h = 'The file format is described in output.export_requests'
        o = opt_factory('input_base64', self._input_base64, d, INPUT_FILE,
                        help=h)
        ol.add(o)

        d = 'Burp log file from which to create the fuzzable requests'
        h = 'The input file needs to be in Burp format.'
        o = opt_factory('input_burp', self._input_burp, d, INPUT_FILE, help=h)
        ol.add(o)

        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._input_base64 = options_list['input_base64'].get_value()
        self._input_burp = options_list['input_burp'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin serves as an entry point for the results of other tools that
        identify URLs. The plugin reads from different input files and
        directories and creates the fuzzable requests which are needed by the
        audit plugins.

        Two configurable parameter exist:
            - input_base64
            - input_burp

        One or more of these need to be configured in order for this plugin to
        yield any results.
        """


class BurpParser(object):
    """
    TODO: Support protocol (http|https) and port extraction. Now it only
          works with http and 80.
    """
    requests = []
    parsing_request = False
    current_is_base64 = False

    def start(self, tag, attrib):
        """
        <request base64="true"><![CDATA[R0VUI...4zDQoNCg==]]></request>

        or

        <request base64="false"><![CDATA[GET /w3af/ HTTP/1.1
        Host: moth
        ...
        ]]></request>
        """
        if tag == 'request':
            self.parsing_request = True

            if not 'base64' in attrib:
                # Invalid file?
                return

            use_base64 = attrib['base64']
            if use_base64.lower() == 'true':
                self.current_is_base64 = True
            else:
                self.current_is_base64 = False

    def data(self, data):
        if self.parsing_request:
            if not self.current_is_base64:
                request_text = data
                head, postdata = request_text.split('\n\n', 1)
            else:
                request_text_b64 = data
                request_text = base64.b64decode(request_text_b64)
                head, postdata = request_text.split('\r\n\r\n', 1)

            fuzzable_request = http_request_parser(head, postdata)
            self.requests.append(fuzzable_request)

    def end(self, tag):
        if tag == 'request':
            self.parsing_request = False

    def close(self):
        return self.requests