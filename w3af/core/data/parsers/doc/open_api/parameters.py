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
from w3af.core.data.fuzzer.form_filler import (smart_fill,
                                               smart_fill_file)


class OpenAPIParamResolutionException(Exception):
    pass


class ParameterHandler(object):

    DEFAULT_VALUES_BY_TYPE = {'int64': 42,
                              'int32': 42,
                              'float': 4.2,
                              'double': 4.2,
                              'date': '2017-06-30T23:59:60Z',
                              'date-time': '2017-06-30T23:59:60Z',
                              'boolean': True}

    def __init__(self, spec, operation):
        """
        :param spec: The parsed specification. We need this to get the param value
                     in special cases where it's type is defined to a Model.
        :param operation: The REST API operation, eg. addStoreItem
        """
        self.spec = spec
        self.operation = operation

    def get_parameters(self):
        """
        This is the main entry point. We return a set with the required and
        optional parameters for the provided operation / specification.
        """
        optional = {}
        required = {}

        for parameter_name, parameter in self.operation.params.iteritems():
            if parameter.required:
                required[parameter_name] = self._get_param_value(parameter)
            else:
                optional[parameter_name] = self._get_param_value(parameter)

        return optional, required

    def _get_param_value(self, parameter):
        """
        If the parameter has a default value, then we return that. If there is
        no value, we try to fill it with something that makes sense based on
        the parameter type and name.

        :param parameter: The parameter to fill
        :return: The value
        """
        #
        #   Easiest case, the parameter already has a default value
        #
        if parameter.default is not None:
            return parameter.default

        value = self._get_param_value_for_primitive(parameter)
        if value is not None:
            return value

        return self._get_param_value_for_model(parameter)

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

    def _get_param_value_for_primitive(self, parameter):
        """
        Helper method for _get_param_value().

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
        value = self._get_param_value_for_array(parameter)

        if value is not None:
            return value

        # We should never reach here!
        msg = 'Failed to get a value for parameter with type: %s'
        raise OpenAPIParamResolutionException(msg % parameter_type)

    def _get_param_value_for_array(self, parameter):
        """
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
        # The array definition is a little bit more complex than just
        # returning [some-primitive-type]. For example it might
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
            value = self._get_param_value_for_model_ref(array_model_ref)

        if value is not None:
            return [value]
        else:
            return []

    def _get_param_value_for_model_ref(self, model_ref):
        """
        Get a valid value for the $ref specified in `model_ref`

        :param model_ref: A reference / pointer to a model defined in another
                          part of the spec. This is used to define classes which
                          are then re-used through the document.

        :return: An instance (most likely a dict) containing default values for
                 all of the values.
        """
        #
        #   The parameter is a Model, this is the hardest case of all,
        #   we need to fetch the model, process it and then return a value
        #
        raise NotImplementedError

    def _get_param_value_for_model(self, parameter):
        """
        Each model attribute can be of a primitive type or another model. To
        resolve this we call _get_param_value() in a recursive way.

        :param spec: The parsed specification
        :param parameter: The parameter object
        :return: A dict instance representing the model. The keys are the model
                 attributes and the values are the default / guessed values
                 defined by _get_param_value().
        """
        print get_format(self.spec, parameter.param_spec)
        raise NotImplementedError