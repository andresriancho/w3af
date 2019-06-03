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
import logging

from yaml import load

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import w3af.core.controllers.output_manager as om

from w3af.core.data.parsers.doc.open_api.parameters import ParameterHandler
from w3af.core.data.parsers.doc.open_api.relaxed_spec import RelaxedSpec


# Silence please.
SILENCE = ('bravado_core.resource',
           'bravado_core.spec',
           'swagger_spec_validator.ref_validators',
           'bravado_core.model',
           'swagger_spec_validator.validator20')

for to_silence in SILENCE:
    logger = logging.getLogger(to_silence)
    logger.setLevel(logging.ERROR)


class SpecificationHandler(object):
    def __init__(self, http_response, no_validation=False):
        self.http_response = http_response
        self.spec = None
        self.no_validation = no_validation

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
                operations = self._set_operation_params(operation)

                for _operation in operations:
                    data = (self.spec,
                            api_resource_name,
                            resource,
                            operation_name,
                            _operation,
                            _operation.params)
                    yield data

    def _set_operation_params(self, operation):
        """
        Takes all of the information associated with an operation and fills the
        parameters with some values in order to have a non-empty REST API call
        which will increase our chances of finding vulnerabilities.

        :param operation: Data associated with the operation
        :return: Two instances of the operation instance:
                    * One only containing values for the required fields
                    * One containing values for the required and optional fields
        """
        parameter_handler = ParameterHandler(self.spec, operation)
        has_optional = parameter_handler.operation_has_optional_params()

        for optional in {False, has_optional}:
            op = parameter_handler.set_operation_params(optional=optional)
            if op is not None:
                yield op

    def _parse_spec_from_dict(self, spec_dict, retry=True):
        """
        load_spec_dict will load the open api document into a dict. We use this
        function to parse the dict into a bravado Spec instance. By default,
        it validates the spec, but validation may be disabled
        by passing `no_validation=True` to the construction

        :param spec_dict: The output of load_spec_dict
        :return: A Spec instance which holds all the dict information in an
                 accessible way.
        """
        config = {'use_models': False,
                  'use_spec_url_for_base_path': False}

        if self.no_validation:
            om.out.debug('Open API spec validation disabled')
            config.update({
                'validate_swagger_spec': False,
                'validate_requests': False,
                'validate_responses': False
            })

        url_string = self.http_response.get_url().url_string

        try:
            self.spec = RelaxedSpec.from_dict(spec_dict,
                                              origin_url=url_string,
                                              config=config)
        except Exception, e:
            msg = ('The document at "%s" is not a valid Open API specification.'
                   ' The following exception was raised while parsing the dict'
                   ' into a specification object: "%s"')
            args = (self.http_response.get_url(), e)
            om.out.debug(msg % args)

            if not retry:
                return None

            error_message = str(e)

            if 'version' in error_message and 'is a required property' in error_message:
                om.out.debug('The Open API specification seems to be missing the'
                             ' version attribute, forcing version 1.0.0 and trying'
                             ' again.')

                spec_dict['info'] = {}
                spec_dict['version'] = '1.0.0'

                return self._parse_spec_from_dict(spec_dict, retry=False)

            return None
        else:
            # Everything went well
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
