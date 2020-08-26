"""
wsdl.py

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
import contextlib
import sys
import xml.parsers.expat as expat
from cStringIO import StringIO

import SOAPpy
import zeep
from requests import HTTPError
from zeep.exceptions import XMLSyntaxError

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.kb.info import Info
from w3af.core.data.parsers.doc.baseparser import BaseParser
from w3af.core.data.parsers.doc.url import URL
from w3af.core.controllers import output_manager


class WSDLParser(BaseParser):
    """
    This class parses WSDL documents.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self, http_response):
        self._proxy = None
        super(WSDLParser, self).__init__(http_response)
        self._wsdl_client = zeep.Client(str(http_response.get_uri()))
        self._discovered_urls = set()

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['_wsdl_client']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._wsdl_client = zeep.Client(str(self._http_response.get_uri()))

    @staticmethod
    def can_parse(http_resp):
        url = http_resp.get_uri()
        try:
            wsdl_client = zeep.Client(str(url))
        except (XMLSyntaxError, HTTPError):
            exception_description = (
                "The result of url: {} seems not to be valid XML.".format(
                    url,
                )
            )
            output_manager.out.debug(exception_description)
            return False
        if not wsdl_client.wsdl.services:
            exception_description = (
                "The result of url: {} seems not to be valid WSDL".format(
                    url,
                )
            )
            output_manager.out.debug(exception_description)
            return False
        return True

    def parse(self):
        for service_name in self._wsdl_client.wsdl.services:
            ports = self._wsdl_client.wsdl.services[service_name].ports
            for _, port in ports.items():
                operation_url = port.binding_options['address']
                self._discovered_urls.add(URL(operation_url))

    get_references_of_tag = BaseParser._return_empty_list
    get_forms = BaseParser._return_empty_list
    get_comments = BaseParser._return_empty_list
    get_meta_redir = BaseParser._return_empty_list
    get_meta_tags = BaseParser._return_empty_list
    get_emails = BaseParser._return_empty_list

    def get_references(self):
        self._report_wsdl_dump()
        return list(self._discovered_urls), []

    @contextlib.contextmanager
    def _redirect_stdout(self, new_stdout):
        old_stdout = sys.stdout
        try:
            sys.stdout = new_stdout
            yield
        finally:
            sys.stdout = old_stdout

    def _report_wsdl_dump(self):
        dump_capturer = StringIO()
        with self._redirect_stdout(dump_capturer):
            self._wsdl_client.wsdl.dump()
        dump_string = dump_capturer.getvalue()
        dump_info = Info(
            name='SOAP details',
            desc=dump_string,
            response_ids=[],
            plugin_name='web_spider',
        )
        kb.kb.append(self, 'soap_actions', dump_info)

    @staticmethod
    def get_name():
        return 'wsdl_parser'
