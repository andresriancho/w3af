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
import re

from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.query_string import QueryString
from w3af.core.data.dc.json_container import JSONContainer
from w3af.core.data.dc.factory import dc_from_content_type_and_raw_params
from w3af.core.data.dc.urlencoded_form import URLEncodedForm
from w3af.core.data.dc.multipart_container import MultipartContainer
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers.doc.open_api.construct_request import construct_request

import w3af.core.controllers.output_manager as om


class RequestFactory(object):

    DEFAULT_CONTENT_TYPE = JSONContainer.JSON_CONTENT_TYPE
    URL_PARTS_RE = re.compile('({[^}]+})')

    def __init__(self, spec, api_resource_name, resource, operation_name,
                 operation, parameters):
        """
        Receives what comes out of SpecificationHandler.get_api_information()
        and creates a fuzzable request which w3af can send to the wire.

        :param api_resource_name: A rest api resource name
        :param resource: Data associated with the resource
        :param operation_name: Operation name, eg. 'Delete pet'
        :param operation: Data associated with the operation
        :param parameters: The parameters to invoke the operation
        """
        self.spec = spec
        self.api_resource_name = api_resource_name
        self.resource = resource
        self.operation_name = operation_name
        self.operation = operation
        self.parameters = parameters

    def get_fuzzable_request(self,
                             discover_fuzzable_headers=False,
                             discover_fuzzable_url_parts=False):
        """
        Creates a fuzzable request by querying different parts of the spec
        parameters, operation, etc.

        :param discover_fuzzable_headers: If it's set to true,
                                          then all fuzzable headers will be added to the fuzzable request.
        :param discover_fuzzable_url_parts: If it's set to true,
                                            then all fuzzable url parts will be added to the fuzzable request.

        :return: A fuzzable request.
        """
        method = self.get_method()
        uri = self.get_uri()
        headers = self.get_headers()
        data_container = self.get_data_container(headers)

        fuzzable_request = FuzzableRequest(uri,
                                           headers=headers,
                                           post_data=data_container,
                                           method=method)

        if discover_fuzzable_headers:
            fuzzable_request.set_force_fuzzing_headers(self._get_parameter_headers())

        if discover_fuzzable_url_parts:
            fuzzable_request.set_force_fuzzing_url_parts(self._get_url_parts())

        return fuzzable_request

    def _get_parameter_headers(self):
        """
        Looks for all parameters which are passed to the endpoint via headers.

        :return: A list of unique header names.
        """
        parameter_headers = set()
        for parameter_name in self.parameters:
            parameter = self.parameters[parameter_name]
            if parameter.location == 'header':
                parameter_headers.add(parameter.name)
                om.out.debug('Found a parameter header for %s endpoint: %s'
                             % (self.operation.path_name, parameter.name))

        return list(parameter_headers)

    def _get_url_parts(self):
        """
        Builds a forced url parts string based in 
        """
        path = self.operation.path_name
        segments = self.URL_PARTS_RE.split(path)
        params = self._get_filled_parameters()
        parts = []

        for seg in segments:
            if seg.startswith('{') and seg.endswith('}'):
                name = seg[1:-1]
                val = '{}'.format(params.get(name, seg))
                parts.append((val, True))
            else:
                parts.append((seg, False))

        return parts

    def _bravado_construct_request(self):
        """
        An example request dict from swagger's pet store application looks like:

        {'url': u'http://petstore.swagger.io/v2/pet/42',
         'headers': {},
         'params': {},
         'method': 'DELETE'}

        Or also like:

        {'url': u'http://petstore.swagger.io/v2/pet/42',
         'headers': {u'api_key': 'FrAmE30.'},
         'params': {},
         'method': 'DELETE'}

        :return: The dict
        """
        parameters = self._get_filled_parameters()

        return construct_request(self.operation,
                                 request_options={},
                                 **parameters)

    def _get_filled_parameters(self):
        return dict((name, value.fill) for (name, value) in self.parameters.iteritems())

    def get_method(self):
        """
        Query the spec / operation and return the HTTP method.
        """
        request_dict = self._bravado_construct_request()
        return request_dict['method']

    def get_uri(self):
        """
        Query the spec / operation and return the URI (with query string
        parameters included).
        """
        request_dict = self._bravado_construct_request()
        url = request_dict['url']

        parameters = self._get_filled_parameters()

        # We only send in the body the parameters that belong there
        for param_name, param_def in self.operation.params.iteritems():
            if param_def.location != 'query':
                parameters.pop(param_name)

        # If the parameter type is an array, we only send the first item
        # TODO: Handle collectionFormat from the param_spec to know if
        #       we should send comma separated (csv) or multiple
        #       parameters with the same name and different values
        for param_name, param_def in self.operation.params.iteritems():
            if 'type' not in param_def.param_spec:
                continue

            if param_def.param_spec['type'] == 'array':
                parameters[param_name] = parameters[param_name][0]

        if parameters:
            formatted_params = [(k, [str(v)]) for k, v in parameters.items() if v is not None]
            query_string = QueryString(formatted_params)
        else:
            # If there are no parameters, we create an empty query string, which is
            # not going to be shown in the HTTP request in any way since it is
            # serialized to an empty string.
            query_string = QueryString()

        uri = URL(url)
        uri.set_querystring(query_string)

        return uri

    def get_headers(self):
        """
        Query the spec / operation and return the headers, including the
        content-type, which will be used later to know how to serialize the
        body.
        """
        request_dict = self._bravado_construct_request()
        headers = Headers(request_dict['headers'].items())

        # First, we try to extract content type from a 'consumes'
        # if the operation has one.
        content_type = self.get_consuming_content_type()
        if content_type is not None:
            headers['Content-Type'] = content_type

        content_type, _ = headers.iget('content-type', None)
        if content_type is None and self.parameters:
            # Content-Type is not set yet.
            #
            # There are some specification documents where the consumes
            # section might be empty. This is because the operation doesn't
            # receive anything or because the specification is wrong.
            #
            # If there are parameters then we opt for serializing them as
            # JSON, which is a safe default
            headers['Content-Type'] = self.DEFAULT_CONTENT_TYPE

        return headers

    def get_consuming_content_type(self):
        """
        Look for the best content type in a 'consumes' list of the operation.

        First, check if any of the consumes values contains JSON,
        and choose that one. If that fails, continue with url-encoded,
        and finally multipart.

        The method throws an exception if no data container was found
        for content types specified in the 'consumes' list.

        :return: One of the content types listed in the 'consumes' list,
                 or None if the operation doesn't have a 'consumes' list.
        """
        if not self.operation.consumes:
            return None

        container_types = [JSONContainer, MultipartContainer, URLEncodedForm]
        for container_type in container_types:
            content_type = self._look_for_consuming_content_type(container_type)
            if content_type is not None:
                return content_type

        raise ValueError("'consumes' list contains only unknown content types")

    def _look_for_consuming_content_type(self, container_type):
        if not self.operation.consumes:
            return None

        for content_type in self.operation.consumes:
            temp_headers = Headers([('Content-Type', content_type)])
            if container_type.content_type_matches(temp_headers):
                return content_type

        return None

    def get_data_container(self, headers):
        """
        Query the spec / operation and return the data container which
        will be used to perform the fuzzing operation.

        This method translates the operation parameters into a data container
        which can be sent in HTTP request body. Also updates the headers
        in order to include the proper Content-Type.

        :param headers: The open API specified headers
        :return: A string which can be sent in HTTP request body
        """
        content_type = headers.get('Content-Type')
        parameters = self._get_filled_parameters()

        # We only send in the body the parameters that belong there
        for param_name, param_def in self.operation.params.iteritems():
            if param_def.location != 'body':
                parameters.pop(param_name)

        # If there are no parameters, we don't create an empty data container,
        # we just send an empty string in the HTTP request body
        if not parameters:
            return None

        # Create the data container
        dc = dc_from_content_type_and_raw_params(content_type, parameters)
        if dc is None:
            om.out.error("No data container for content type '%s'" % content_type)
            return None

        dc.set_header('Content-Type', content_type)

        return dc
