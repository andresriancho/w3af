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
    def __init__(self, http_response, validate_swagger_spec=False):
        self.http_response = http_response
        self.spec = None
        self.validate_swagger_spec = validate_swagger_spec
        self._parsing_errors = []

    def get_http_response(self):
        return self.http_response

    def get_parsing_errors(self):
        """
        :return: A list with all the errors found during parsing
        """
        return self._parsing_errors

    def append_parsing_error(self, parsing_error):
        self._parsing_errors.append(parsing_error)

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

    def _parse_spec_from_dict(self, spec_dict):
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

        if not self.validate_swagger_spec:
            om.out.debug('Open API spec validation disabled')
            config.update({
                'validate_swagger_spec': False,
                'validate_requests': False,
                'validate_responses': False
            })

        url_string = self.http_response.get_url().url_string

        self._apply_known_fixes_before_parsing(spec_dict)

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
            self.append_parsing_error(msg % args)

            return None
        else:
            # Everything went well
            return self.spec

    def _apply_known_fixes_before_parsing(self, spec_dict):
        """
        Applies known fixes to the input dict before sending it to the parser.

        :param spec_dict: The dict, as received from the wire.
        :return: A new (potentially unchanged) spec_dict
        """
        self._add_version_to_spec_dict(spec_dict)
        self._add_info_version_to_spec_dict(spec_dict)
        self._add_license_name(spec_dict)

    def _add_version_to_spec_dict(self, spec_dict):
        """
        If the spec_dict is missing the version this method will add one

        :param spec_dict: The dict, as received from the wire.
        :return: A new (potentially unchanged) spec_dict
        """
        swagger = spec_dict.get('swagger', None)
        openapi = spec_dict.get('openapi', None)

        if swagger is not None or openapi is not None:
            # No changes are required
            return

        # We choose one and cross our fingers
        spec_dict['swagger'] = '2.0'

    def _add_info_version_to_spec_dict(self, spec_dict):
        """
        If the spec_dict is missing the version this method will add one

        :param spec_dict: The dict, as received from the wire.
        :return: A new (potentially unchanged) spec_dict
        """
        info = spec_dict.get('info', dict())
        version = info.get('version', None)

        if version is not None:
            # No changes are required
            return

        spec_dict['info'] = info
        spec_dict['info']['version'] = '1.0.0'

    def _add_license_name(self, spec_dict):
        """
        If the spec_dict has a license field but doesn't have a "name" then we
        just add one

        :param spec_dict: The dict, as received from the wire.
        :return: A new (potentially unchanged) spec_dict
        """
        info = spec_dict.get('info', dict())
        license = info.get('license', dict())
        name = license.get('name', None)

        if name is not None:
            # No changes are required
            return

        spec_dict['info'] = info
        spec_dict['info']['license'] = license
        spec_dict['info']['license']['name'] = 'Apache 2.0'
        spec_dict['info']['license']['url'] = 'https://www.apache.org/licenses/LICENSE-2.0.html'

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
            except Exception:
                # Oops! We should never reach here because is_valid_json_or_yaml
                # checks that we have a JSON or YAML object, but well... just in
                # case we use a try / except.
                msg = 'The OpenAPI specification at %s is not in JSON or YAML format'
                args = (self.http_response.get_url(),)

                om.out.error(msg % args)
                self.append_parsing_error(msg % args)

                return None

        return spec_dict
