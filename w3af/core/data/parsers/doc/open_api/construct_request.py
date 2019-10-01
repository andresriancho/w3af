"""
construct_request.py

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
from six import iteritems
from six import itervalues

from bravado_core.exception import SwaggerMappingError
from bravado_core.param import marshal_param


def construct_request(operation, request_options, **op_kwargs):
    """
    Construct the outgoing request dict.

    :type operation: :class:`bravado_core.operation.Operation`
    :param request_options: _request_options passed into the operation invocation.
    :param op_kwargs: parameter name/value pairs to passed to the invocation of the operation.

    :return: request in dict form
    """
    url = operation.swagger_spec.api_url.rstrip('/') + operation.path_name

    request = {
        'method': str(operation.http_method.upper()),
        'url': url,
        'params': {},  # filled in downstream
        'headers': request_options.get('headers', {}),
    }
    # Adds Accept header to request for msgpack response if specified
    if request_options.get('use_msgpack', False):
        request['headers']['Accept'] = 'application/msgpack'

    # Copy over optional request options
    for request_option in ('connect_timeout', 'timeout'):
        if request_option in request_options:
            request[request_option] = request_options[request_option]

    construct_params(operation, request, op_kwargs)

    return request


def construct_params(operation, request, op_kwargs):
    """
    Given the parameters passed to the operation invocation, validates and
    marshals the parameters into the provided request dict.

    :type operation: :class:`bravado_core.operation.Operation`
    :type request: dict
    :param op_kwargs: the kwargs passed to the operation invocation

    :raises: SwaggerMappingError on extra parameters or when a required
             parameter is not supplied.
    """
    current_params = operation.params.copy()
    for param_name, param_value in iteritems(op_kwargs):
        param = current_params.pop(param_name, None)
        if param is None:
            raise SwaggerMappingError(
                "{0} does not have parameter {1}"
                .format(operation.operation_id, param_name))
        marshal_param(param, param_value, request)

    # Check required params and non-required params with a 'default' value
    for remaining_param in itervalues(current_params):
        if remaining_param.location == 'header' and remaining_param.name in request['headers']:
            marshal_param(remaining_param, request['headers'][remaining_param.name], request)
        else:
            if remaining_param.required:
                raise SwaggerMappingError(
                    '{0} is a required parameter'.format(remaining_param.name))
            if not remaining_param.required and remaining_param.has_default():
                marshal_param(remaining_param, None, request)
