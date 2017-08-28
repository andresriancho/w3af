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
import logging

from yaml import load
from yaml import CLoader as Loader

from bravado.client import construct_request
from bravado_core.spec import Spec
from bravado_core.schema import get_format

import w3af.core.controllers.output_manager as om

from w3af.core.data.parsers.doc.baseparser import BaseParser
from w3af.core.data.fuzzer.form_filler import smart_fill

# Silence please.
SILENCE = ('bravado_core.resource',
           'bravado_core.spec',
           'swagger_spec_validator.ref_validators',
           'bravado_core.model')

for to_silence in SILENCE:
    logger = logging.getLogger(to_silence)
    logger.setLevel(logging.ERROR)


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

    def __init__(self, http_response):
        super(OpenAPI, self).__init__(http_response)
        self.api_calls = []

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
                          type HTML / PDF / WML / etc.

        :return: True if the document parameter is a string that contains a PDF
                 document.
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

    def parse(self):
        """
        Get the URLs using a regex
        """
        spec_dict = self._load_spec_dict()
        if spec_dict is None:
            return

        spec = self._parse_spec_from_dict(spec_dict)
        if spec is None:
            return

        for api_resource_name, resource in spec.resources.items():
            for operation_name, operation in resource.operations.items():

                optional, required = self._get_params(spec, operation)

                #
                # First we create a REST API call only with required parameters
                #
                parameter_sets = [required]

                if optional:
                    #
                    # Now we create a REST API call with all parameters, including
                    # the optional ones. This will yield a higher code coverage for
                    # our scan.
                    #
                    optional.update(required)
                    parameter_sets.append(optional)

                for parameter_set in parameter_sets:
                    request_dict = construct_request(operation,
                                                     request_options={},
                                                     **parameter_set)
                    fuzzable_request = self._to_fuzzable_request(request_dict)
                    self.api_calls.append(fuzzable_request)

    def _parse_spec_from_dict(self, spec_dict):
        """

        :param spec_dict:
        :return:
        """
        config = {'use_models': False}
        url_string = self.get_http_response().get_url().url_string

        try:
            spec = Spec.from_dict(spec_dict,
                                  origin_url=url_string,
                                  config=config)
        except Exception, e:
            msg = ('The document at "%s" is not a valid Open API specification.'
                   ' The following exception was raised while parsing the dict'
                   ' into a specification object: "%s"')
            om.out.debug(msg % (self._http_response.get_url(), e))
            return None

        return spec

    def _load_spec_dict(self):
        """
        Load the specification from json / yaml into a dict
        :return: The dict with the open api data
        """
        try:
            spec_dict = json.loads(self.get_http_response().body)
        except ValueError:
            # Seems like the OpenAPI was specified using Yaml instead of
            # JSON. Let's parse the Yaml data!

            try:
                spec_dict = load(self.get_http_response().body, Loader=Loader)
            except yaml.scanner.ScannerError:
                # Oops! We should never reach here because is_valid_json_or_yaml
                # checks that we have a JSON or YAML object, but well... just in
                # case we use a try / except.
                return None

        return spec_dict

    def _to_fuzzable_request(self, request_dict):
        """
        Transforms HTTP request information from a dict (as returned from bravado)
        into a fuzzable request we can use in w3af.

        An example request dict from swagger's pet store application looks like:

        {'url': u'http://petstore.swagger.io/v2/pet/42',
         'headers': {},
         'params': {},
         'method': 'DELETE'}

        :param request_dict: The dict with the HTTP request information
        :return: A FuzzableRequest instance
        """
        return None

    def _get_params(self, spec, operation):
        """
        :param spec: The parsed specification. We need this to get the param value
                     in special cases where it's type is defined to a Model.
        :param operation: The REST API operation, eg. addStoreItem
        :return: A tuple with required and optional parameters for the call
        """
        optional = {}
        required = {}

        for parameter_name, parameter in operation.params.iteritems():
            if parameter.required:
                required[parameter_name] = self._get_param_value(spec, parameter)
            else:
                optional[parameter_name] = self._get_param_value(spec, parameter)

        return optional, required

    def _get_param_value(self, spec, parameter):
        """
        If the parameter has a default value, then we return that. If there is
        no value, we try to fill it with something that makes sense based on
        the parameter type and name.

        :param spec: The parsed specification. We need this to get the param value
                     in special cases where it's type is defined to a Model.
        :param parameter: The parameter to fill
        :return: The value
        """
        #
        #   Easiest case, the parameter already has a default value
        #
        if parameter.default is not None:
            return parameter.default

        #
        #   The parameter has a strong type
        #   https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md
        #
        try:
            parameter_format = parameter.param_spec['format']
        except KeyError:
            pass
        else:
            if parameter_format in ('int64', 'int32'):
                return 42

            if parameter_format in ('float', 'double'):
                return 4.2

            if parameter_format in ('date', 'date-time'):
                return '2017-06-30T23:59:60Z'

        try:
            parameter_type = parameter.param_spec['type']
        except KeyError:
            pass
        else:
            if parameter_type in ('string',):
                return smart_fill(parameter.name)

            if parameter_type in ('boolean',):
                return True

            if parameter_type == 'array':
                try:
                    return [parameter.param_spec['items']['default']]
                except KeyError:
                    return [smart_fill(parameter.name)]

        #
        #   The parameter is a Model, this is the hardest case of all,
        #   we need to fetch the model, process it and then return a value
        #
        if 'schema' in parameter.param_spec and \
           'x-scope' in parameter.param_spec['schema'] and \
           '$ref' in parameter.param_spec['schema']:
            return self._handle_model(spec, parameter)

        # We did our best with the previous steps, now we just guess
        return smart_fill(parameter.name)

    def _handle_model(self, spec, parameter):
        """
        :param spec: The parsed specification
        :param parameter: The parameter object
        :return: A model instance with the parameters set and ready to send to
                 the wire.
        """
        print get_format(spec, parameter.param_spec)

    def get_forms(self):
        """
        :return: A list with fuzzable requests representing the REST API calls
        """
        return self.api_calls

    get_references_of_tag = get_references = BaseParser._return_empty_list
    get_comments = BaseParser._return_empty_list
    get_meta_redir = get_meta_tags = get_emails = BaseParser._return_empty_list
    get_clear_text_body = BaseParser._return_empty_list
