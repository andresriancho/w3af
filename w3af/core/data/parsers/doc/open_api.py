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
from w3af.core.data.fuzzer.form_filler import (smart_fill,
                                               smart_fill_file)

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

    DEFAULT_VALUES_BY_TYPE = {'int64': 42,
                              'int32': 42,
                              'float': 4.2,
                              'double': 4.2,
                              'date': '2017-06-30T23:59:60Z',
                              'date-time': '2017-06-30T23:59:60Z',
                              'boolean': True}

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
        Extract all the API endpoints using the bravado Open API parser
        """
        spec_dict = self._load_spec_dict()
        if spec_dict is None:
            return

        spec = self._parse_spec_from_dict(spec_dict)
        if spec is None:
            return

        for api_resource_name, resource in spec.resources.items():
            for operation_name, operation in resource.operations.items():

                try:
                    optional, required = self._get_params(spec, operation)
                except RuntimeError as rte:
                    msg = ('A RuntimeError was raised by the OpenAPI._get_params()'
                           ' method. This is most likely by a reference loop in'
                           ' the OpenAPI models. The exception was: "%s"')
                    om.out.debug(msg % rte)
                    continue
                except OpenAPIParamResolutionException as oae:
                    msg = ('An Open API parameter resolution exception was raised'
                           ' by OpenAPI._get_params(). The exception was: "%s".')
                    om.out.debug(msg % oae)
                    continue

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

        value = self._get_param_value_for_primitive(spec, parameter)
        if value is not None:
            return value

        return self._get_param_value_for_model(spec, parameter)

    def _get_param_value_for_type_and_name(self, parameter_type, parameter_name):
        """
        :param parameter_type: The type of parameter (string, int32, array, etc.)
        :param parameter_name: The name of the parameter to fill
        :return: The parameter value
        """
        default_value = self.DEFAULT_VALUES_BY_TYPE.get(parameter_type, None)
        if default_value is not None:
            return default_value

        if parameter_type == 'string':
            return smart_fill(parameter_name)

        if parameter_type == 'file':
            return smart_fill_file(parameter_name, 'cat.png')

    def _get_param_value_for_primitive(self, spec, parameter):
        """
        Helper method for _get_param_value().

        :param spec: The open api specification
        :param parameter: The parameter which (might or might not) be of a primitive type
        :return: The value to assign to this parameter in HTTP requests
        """
        #
        #   The parameter has a strong type
        #   https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md
        #
        try:
            parameter_type = parameter.param_spec['format']
        except KeyError:
            try:
                parameter_type = parameter.param_spec['type']
            except KeyError:
                # This is not a primitive type, most likely a model
                return None

        value = self._get_param_value_for_type_and_name(parameter_type,
                                                        parameter.name)
        if value is not None:
            return value

        #
        #   Arrays are difficult to handle since they can contain complex data
        #
        value = self._get_param_value_for_array(spec, parameter)

        if value is not None:
            return value

        # We should never reach this!
        msg = 'Failed to get a value for parameter with type: %s'
        raise OpenAPIParamResolutionException(msg % parameter_type)

    def _get_param_value_for_array(self, spec, parameter):
        """
        :param spec: The parsed open api specification
        :param parameter: The parameter name
        :return: A python list (json array) containing values
        """
        if parameter.param_spec.get('type', None) != 'array':
            return None

        if parameter.param_spec.get('items', None) is None:
            # Potentially invalid array specification, we just return
            # an empty array
            return []

        # Do we have a default value which can be used?
        if 'default' in parameter.param_spec['items']:
            return [parameter.param_spec['items']['default']]

        #
        # The array definition is a little bit more complex
        # than just returning a string. For example it might
        # look like this:
        #
        #     u'photoUrls': {u'items': {u'type': u'string'},
        #                    u'type': u'array',
        #
        # Where this is completely valid: ['http://abc/']
        #
        # Or like this:
        #
        #     u'ids': {u'items': {u'type': u'int32'},
        #              u'type': u'array',
        #
        # Where we need to fill with integers: [1, 3, 4]
        #
        # Or even worse... there is a model in the array:
        #
        #     u'tags': {u'items': {u'$ref': u'#/definitions/Tag',
        #                           'x-scope': [u'http://moth/swagger.json',
        #                                      u'http://moth/swagger.json#/definitions/Pet']},
        #               u'type': u'array',
        #
        # And we need to fill the array with one or more tags
        #
        value = None

        # Handle arrays which hold primitive types
        array_item_type = parameter.param_spec['items'].get('type', None)
        if array_item_type is not None:
            value = self._get_param_value_for_type_and_name(array_item_type,
                                                            parameter.name)

        # Handle arrays which hold models
        array_model_ref = parameter.param_spec['items'].get('$ref', None)
        if array_model_ref is not None:
            value = self._get_param_value_for_model(array_model_ref,
                                                    parameter.name)

        if value is not None:
            return [value]
        else:
            return []

    def _get_param_value_for_model(self, spec, parameter):
        #
        #   The parameter is a Model, this is the hardest case of all,
        #   we need to fetch the model, process it and then return a value
        #
        try:
            parameter.param_spec['schema']['$ref']
            parameter.param_spec['schema']['x-scope']
        except KeyError:
            pass
        else:
            return self._handle_model(spec, parameter)

        # We did our best with the previous steps, now we just guess
        return smart_fill(parameter.name)

    def _handle_model(self, spec, parameter):
        """
        Each model attribute can be of a primitive type or another model. To
        resolve this we call _get_param_value() in a recursive way.

        :param spec: The parsed specification
        :param parameter: The parameter object
        :return: A dict instance representing the model. The keys are the model
                 attributes and the values are the default / guessed values
                 defined by _get_param_value().
        """
        print get_format(spec, parameter.param_spec)
        return {'name': 'y', 'photoUrls': ['x']}

    def get_forms(self):
        """
        :return: A list with fuzzable requests representing the REST API calls
        """
        return self.api_calls

    get_references_of_tag = get_references = BaseParser._return_empty_list
    get_comments = BaseParser._return_empty_list
    get_meta_redir = get_meta_tags = get_emails = BaseParser._return_empty_list
    get_clear_text_body = BaseParser._return_empty_list


class OpenAPIParamResolutionException(Exception):
    pass
