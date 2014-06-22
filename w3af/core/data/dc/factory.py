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
import w3af.core.controllers.output_manager as om

from w3af.core.data.dc.urlencoded_form import URLEncodedForm
from w3af.core.data.dc.json_container import JSONContainer
from w3af.core.data.dc.xmlrpc import XmlRpcContainer
from w3af.core.data.dc.multipart_container import MultipartContainer
from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.generic.plain import PlainContainer

POST_DATA_CONTAINERS = (MultipartContainer, JSONContainer, XmlRpcContainer,
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

        # These lines are for debugging
        #import traceback
        #traceback.print_stack()

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