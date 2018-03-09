# -*- coding: UTF-8 -*-
"""
requests.py

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
from bravado_core.spec import Spec

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import w3af.core.controllers.output_manager as om

from w3af.core.data.parsers.doc.open_api.parameters import (ParameterHandler,
                                                            OpenAPIParamResolutionException)


class SpecificationHandler(object):
    def __init__(self, http_response):
        self.http_response = http_response
        self.spec = None

    def get_http_response(self):
        return self.http_response

    def get_api_information(self):
        """
        This is the main method.

        :yield: All the information we were able to collect about each API endpoint
                This includes the specification, parameters, URL, etc.
        """
        spec_dict = self._load_spec_dict()

        if spec_dict is None:
            return

        self.spec = self._parse_spec_from_dict(spec_dict)
        if self.spec is None:
            return

        for api_resource_name, resource in self.spec.resources.items():
            for operation_name, operation in resource.operations.items():
                parameters_list = self._get_parameters(api_resource_name,
                                                       resource,
                                                       operation_name,
                                                       operation)

                for parameters in parameters_list:
                    data = (self.spec,
                            api_resource_name,
                            resource,
                            operation_name,
                            operation,
                            parameters)
                    yield data

    def _get_parameters(self, api_resource_name, resource, operation_name, operation):
        """
        Takes all of the information associated with an operation and creates
        a fuzzable request which can be sent by the w3af framework.

        :param api_resource_name: A rest api resource name
        :param resource: Data associated with the resource
        :param operation_name: Operation name, eg. 'Delete pet'
        :param operation: Data associated with the operation
        :return: The parameters to invoke the operation
        """
        parameters_list = []
        parameter_handler = ParameterHandler(self.spec, operation)

        try:
            optional, required = parameter_handler.get_parameters()
        except RuntimeError as rte:
            msg = ('A RuntimeError was raised by the OpenAPI._get_params()'
                   ' method. This is most likely by a reference loop in'
                   ' the OpenAPI models. The exception was: "%s"')
            om.out.debug(msg % rte)
            return []
        except OpenAPIParamResolutionException as oae:
            msg = ('An Open API parameter resolution exception was raised'
                   ' by OpenAPI._get_params(). The exception was: "%s".')
            om.out.debug(msg % oae)
            return []

        #
        # First we create a REST API call only with required parameters
        #
        parameters_list.append(required)

        if optional:
            #
            # Now we create a REST API call with all parameters, including
            # the optional ones. This will yield a higher code coverage for
            # our scan.
            #
            optional.update(required)
            parameters_list.append(optional)

        return parameters_list

    def _parse_spec_from_dict(self, spec_dict):
        """
        load_spec_dict will load the open api document into a dict. We use this
        function to parse the dict into a bravado Spec instance.

        :param spec_dict: The output of load_spec_dict
        :return: A Spec instance which holds all the dict information in an
                 accessible way.
        """
        config = {'use_models': False}
        url_string = self.http_response.get_url().url_string

        try:
            self.spec = Spec.from_dict(spec_dict,
                                       origin_url=url_string,
                                       config=config)
        except Exception, e:
            msg = ('The document at "%s" is not a valid Open API specification.'
                   ' The following exception was raised while parsing the dict'
                   ' into a specification object: "%s"')
            om.out.debug(msg % (self.http_response.get_url(), e))
            return None

        return self.spec

    def _load_spec_dict(self):
        """
        Load the specification from json / yaml into a dict
        :return: The dict with the open api data
        """
        try:
            spec_dict = json.loads(self.http_response.body)
        except ValueError:
            # Seems like the OpenAPI was specified using Yaml instead of
            # JSON. Let's parse the Yaml data!

            try:
                spec_dict = load(self.http_response.body, Loader=Loader)
            except yaml.scanner.ScannerError:
                # Oops! We should never reach here because is_valid_json_or_yaml
                # checks that we have a JSON or YAML object, but well... just in
                # case we use a try / except.
                return None

        return spec_dict
