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
from bravado.client import construct_request
from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.json_container import JSONContainer
from w3af.core.data.dc.factory import dc_from_content_type_and_raw_params
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL


class RequestFactory(object):

    DEFAULT_CONTENT_TYPE = JSONContainer.JSON_CONTENT_TYPE

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

    def forge(self):
        """
        Creates a fuzzable request by querying different parts of the spec
        parameters, operation, etc.

        :return: A fuzzable request.
        """
        marshal_param
        'https://github.com/Yelp/bravado-core/blob/master/bravado_core/marshal.py'
        'https://github.com/Yelp/bravado-core/blob/master/bravado_core/param.py#L95'
        'https://github.com/Yelp/bravado/blob/master/bravado/requests_client.py'

        method = self.get_method()
        uri = self.get_uri()
        headers = self.get_headers()
        data_container = self.get_data_container(headers)

        fuzzable_request = FuzzableRequest(uri,
                                           headers=headers,
                                           post_data=data_container,
                                           method=method)

        return fuzzable_request

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
        return construct_request(self.operation,
                                 request_options={},
                                 **self.parameters)

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
        return URL(url)

    def get_headers(self):
        """
        Query the spec / operation and return the headers, including the
        content-type, which will be used later to know how to serialize the
        body.
        """
        request_dict = self._bravado_construct_request()
        headers = Headers(request_dict['headers'].items())

        content_type, _ = headers.iget('content-type', None)
        if content_type is None:
            # The content type is not in the headers, so we try to extract
            # it from the operation.
            #
            # The REST API endpoint might support more than one content-type
            # for consuming it. We only use the first one since in 99% of the cases
            # a vulnerability which we find using one content-type will be present
            # in others. This works the other way around also, there are very few
            # vulnerabilities which are going to be exploitable with one content-
            # type.
            if self.operation.consumes:
                content_type = self.operation.consumes[0]
                headers['Content-Type'] = content_type
            else:
                # Finally, there are some specification documents where the consumes
                # section might be empty. This is because the operation doesn't
                # receive anything or because the specification is wrong.
                #
                # If there are parameters then we opt for serializing them as
                # JSON, which is a safe default
                if self.parameters:
                    headers['Content-Type'] = self.DEFAULT_CONTENT_TYPE

        return headers

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
        # This means that the operation doesn't consume any post-data, most
        # likely it is a DELETE or GET request
        if not self.operation.consumes:
            return None

        content_type = headers.get('Content-Type')
        dc = dc_from_content_type_and_raw_params(content_type, self.parameters)

        return dc
