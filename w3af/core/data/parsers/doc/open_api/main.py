"""
open_api.py

Copyright 2017 Andres Riancho

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
import json
import yaml

from yaml import load

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.misc.traceback_utils import get_traceback, get_exception_location
from w3af.core.data.parsers.doc.baseparser import BaseParser
from w3af.core.data.parsers.doc.open_api.specification import SpecificationHandler
from w3af.core.data.parsers.doc.open_api.requests import RequestFactory


class OpenAPI(BaseParser):
    """
    This class parses REST API definitions written in OpenAPI [0] format
    using bravado-core [1].

    The parser only returns interesting results for get_forms(), where all
    FuzzableRequests associated with REST API calls are returned.

    [0] https://www.openapis.org/
    [1] https://github.com/Yelp/bravado-core

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    CONTENT_TYPES = ('application/json',
                     'text/yaml',
                     'text/x-yaml',
                     'application/yaml',
                     'application/x-yaml',)

    KEYWORDS = ('consumes',
                'produces',
                'swagger',
                'paths')

    def __init__(self, http_response, no_validation=False, discover_fuzzable_headers=True):
        super(OpenAPI, self).__init__(http_response)
        self.api_calls = []
        self.no_validation = no_validation
        self.discover_fuzzable_headers = discover_fuzzable_headers
        self.specification_handler = None
        self.request_to_operation_id = {}

    @staticmethod
    def content_type_match(http_resp):
        """
        :param http_resp: The HTTP response we want to parse
        :return: True if we know how to parse this content type
        """
        for _type in OpenAPI.CONTENT_TYPES:
            if _type in http_resp.content_type:
                return True

        return False

    @staticmethod
    def matches_any_keyword(http_resp):
        """
        :param http_resp: The HTTP response we want to parse
        :return: True if it seems that this page is an open api doc
        """
        for keyword in OpenAPI.KEYWORDS:
            if keyword in http_resp.body:
                return True

        return False

    @staticmethod
    def is_valid_json_or_yaml(http_resp):
        """
        :param http_resp: The HTTP response we want to parse
        :return: True if it seems that this page is an open api doc
        """
        try:
            json.loads(http_resp.body)
        except ValueError:
            pass
        else:
            return True

        try:
            load(http_resp.body, Loader=Loader)
        except yaml.scanner.ScannerError:
            return False
        else:
            return True

    @staticmethod
    def can_parse(http_resp):
        """
        :param http_resp: A http response object that contains a document of
                          type JSON or YAML.

        :return: True if it seems that the HTTP response contains an Open API spec
        """
        # Only parse JSON and YAML
        if not OpenAPI.content_type_match(http_resp):
            return False

        # Only parse documents that look like Open API docs
        if not OpenAPI.matches_any_keyword(http_resp):
            return False

        # Only parse if they are valid json or yaml docs
        if not OpenAPI.is_valid_json_or_yaml(http_resp):
            return False

        # It seems that this is an openapi doc, but we can't never be 100%
        # sure until we really parse it in OpenAPI.parse()
        return True

    def get_specification_handler(self):
        """
        TODO
        :return:
        """
        return self.specification_handler

    def get_request_to_operation_id(self):
        """
        TODO
        :return:
        """
        return self.request_to_operation_id

    def parse(self):
        """
        Extract all the API endpoints using the bravado Open API parser.

        The method also looks for all parameters which are passed to endpoints via headers,
        and stores them in to the fuzzable request
        """
        self.specification_handler = SpecificationHandler(self.get_http_response(),
                                                          self.no_validation)

        self.request_to_operation_id = {}
        for data in self.specification_handler.get_api_information():
            try:
                request_factory = RequestFactory(*data)
                fuzzable_request = request_factory.get_fuzzable_request(self.discover_fuzzable_headers)

                key = '%s|%s' % (fuzzable_request.get_method(), fuzzable_request.get_url())
                self.request_to_operation_id[key] = data[4].operation_id
            except Exception, e:
                #
                # This is a strange situation because parsing of the OpenAPI
                # spec can fail awfully for one of the operations but succeed
                # for the rest.
                #
                # Usually we would simply stop processing the document, but it
                # is better to a) provide value to the user, and b) warn him
                # so that they can report the issue and improve w3af
                #
                # Just crashing wouldn't provide any value to the user
                #
                tb = get_traceback()
                path, filename, _function, line = get_exception_location(tb)
                spec_url = self.get_http_response().get_url()

                msg = ('Failed to generate a fuzzable request for one of the'
                       ' OpenAPI operations. The parser will continue with the'
                       ' next operation. The OpenAPI specification is at "%s" and'
                       ' the exception was: "%s" at %s/%s:%s():%s.')

                args = (spec_url, e, path, filename, _function, line)

                om.out.error(msg % args)
            else:
                if not self._should_audit(fuzzable_request):
                    continue

                self.api_calls.append(fuzzable_request)

    @staticmethod
    def _should_audit(fuzzable_request):
        """
        We want to make sure that w3af doesn't delete all the items from the
        REST API, so we ignore DELETE calls.

        :param fuzzable_request: The fuzzable request with a call to the REST API
        :return: True if we should scan this fuzzable request
        """
        if fuzzable_request.get_method().upper() == 'DELETE':
            return False

        return True

    def get_api_calls(self):
        """
        :return: A list with fuzzable requests representing the REST API calls
        """
        return self.api_calls

    get_references_of_tag = get_references = BaseParser._return_empty_list
    get_comments = BaseParser._return_empty_list
    get_meta_redir = get_meta_tags = get_emails = BaseParser._return_empty_list
    get_clear_text_body = BaseParser._return_empty_list
    get_forms = BaseParser._return_empty_list
