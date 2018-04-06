# -*- coding: utf8 -*-
"""
factory.py

Copyright 2014 Andres Riancho

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

import w3af.core.controllers.output_manager as om

from w3af.core.data.dc.urlencoded_form import URLEncodedForm
from w3af.core.data.dc.json_container import JSONContainer
from w3af.core.data.dc.xmlrpc import XmlRpcContainer
from w3af.core.data.dc.multipart_container import MultipartContainer
from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.generic.plain import PlainContainer
from w3af.core.data.parsers.utils.form_params import FormParameters
from w3af.core.data.dc.utils.json_encoder import DateTimeJSONEncoder


POST_DATA_CONTAINERS = (MultipartContainer,
                        JSONContainer,
                        XmlRpcContainer,
                        URLEncodedForm)


def dc_from_hdrs_post(headers, post_data):
    """
    :param headers: HTTP request headers, most importantly containing the
                    content-type info.
    :param post_data: The HTTP request post-data as a string
    :return: The best-match from POST_DATA_CONTAINERS to hold the information
             in self._post_data @ FuzzableRequest
    """
    if headers is None:
        headers = Headers()

    for pdc_klass in POST_DATA_CONTAINERS:
        try:
            return pdc_klass.from_postdata(headers, post_data)
        except (ValueError, TypeError) as e:
            pass
    else:
        content_type, _ = headers.iget('content-type', 'None')
        msg = 'Unknown post-data. Content-type: "%s" and/or post-data "%s"'
        om.out.debug(msg % (content_type, post_data[:50]))

        return PlainContainer.from_postdata(headers, post_data)


def dc_from_form_params(form_parameters):
    """
    :param form_parameters: The form parameters is the result of parsing HTML,
                            and contains information such as the parameter names
                            and types.

    :return: An instance of URLEncodedForm or MultipartContainer
    """
    if form_parameters.get_file_vars():
        # If it has files, I don't care if the form encoding wasn't specified
        # we must send it as multipart.
        return MultipartContainer(form_parameters)

    if 'multipart' in form_parameters.get_form_encoding().lower():
        # If there are no files but the web developer specified the multipart
        # form encoding, then we'll use multipart also
        return MultipartContainer(form_parameters)

    return URLEncodedForm(form_parameters)


def dc_from_content_type_and_raw_params(content_type, params):
    """
    This function will create a data container when we have the following:

        * content_type: application/json, multipart/form-data, etc.
        * params: A dict containing parameters and values.

    Note that we can't just send the params dict to the data container
    since some expect a different format.

    :param content_type: A string representing the HTTP content type
    :param params: A dict containing parameters and values.
    :return: A data container
    """
    temp_headers = Headers([('Content-Type', content_type)])

    for data_container_cls in POST_DATA_CONTAINERS:
        if data_container_cls.content_type_matches(temp_headers):
            return _create_instance(data_container_cls, params)

    return None


def _create_instance_from_json_string(data_container_cls, params):
    json_string = DateTimeJSONEncoder().encode(params)
    return data_container_cls(json_string)


def _create_instance_from_form_params(data_container_cls, params):
    form_params = FormParameters()

    for param_name, param_value in params.iteritems():
        form_params.add_field_by_attrs({'name': param_name, 'value': param_value})

    return data_container_cls(form_params)


def _create_instance(data_container_cls, params):
    post_data_container_builder = {MultipartContainer: _create_instance_from_form_params,
                                   JSONContainer: _create_instance_from_json_string,
                                   URLEncodedForm: _create_instance_from_form_params}

    builder_func = post_data_container_builder[data_container_cls]
    return builder_func(data_container_cls, params)
