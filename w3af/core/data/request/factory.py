"""
factory.py

Copyright 2006 Andres Riancho

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
import w3af.core.data.kb.config as cf
import w3af.core.data.parsers.parser_cache as parser_cache

from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.request.urlencoded_post_request import URLEncPostRequest
from w3af.core.data.request.multipart_request import MultipartRequest
from w3af.core.data.request.querystring_request import QsRequest
from w3af.core.data.request.json_request import JSONPostDataRequest
from w3af.core.data.request.xmlrpc_request import XMLRPCRequest
from w3af.core.data.request.post_data_request import PostDataRequest
from w3af.core.data.dc.cookie import Cookie
from w3af.core.data.dc.headers import Headers
from w3af.core.data.parsers.url import URL
from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.core.data.misc.encoding import smart_unicode


URL_HEADERS = ('location', 'uri', 'content-location')


def create_fuzzable_requests(resp, request=None, add_self=True):
    """
    Generates the fuzzable requests based on an HTTP response instance.

    :param resp: An HTTPResponse instance.
    :param request: The HTTP request that generated the resp
    :param add_self: If I should add the current HTTP request
                         (:param request) to the result on not.

    :return: A list of fuzzable requests.
    """
    res = []

    # Headers for all fuzzable requests created here:
    # And add the fuzzable headers to the dict
    req_headers = dict((h, '') for h in cf.cf.get('fuzzable_headers'))
    req_headers.update(request and request.get_headers() or {})
    req_headers = Headers(req_headers.items())

    # Get the cookie!
    cookie_obj = _create_cookie(resp)

    # Create the fuzzable request that represents the request object
    # passed as parameter
    if add_self:
        qsr = QsRequest(resp.get_uri(), headers=req_headers, cookie=cookie_obj)
        res.append(qsr)

    # If response was a 30X (i.e. a redirect) then include the
    # corresponding fuzzable request.
    resp_headers = resp.get_headers()

    for url_header_name in URL_HEADERS:
        url_header_value, _ = resp_headers.iget(url_header_name, '')
        if url_header_value:
            url = smart_unicode(url_header_value, encoding=resp.charset)
            try:
                absolute_location = resp.get_url().url_join(url)
            except ValueError:
                msg = 'The application sent a "%s" redirect that w3af' \
                      ' failed to correctly parse as an URL, the header' \
                      ' value was: "%s"'
                om.out.debug(msg % (url_header_name, url))
            else:
                qsr = QsRequest(absolute_location,
                                headers=req_headers,
                                cookie=cookie_obj)
                res.append(qsr)

    # Try to find forms in the document
    try:
        dp = parser_cache.dpc.get_document_parser_for(resp)
    except BaseFrameworkException:
        # Failed to find a suitable parser for the document
        form_list = []
    else:
        form_list = dp.get_forms()
        same_domain = lambda f: f.get_action().get_domain() == \
                                resp.get_url().get_domain()
        form_list = [f for f in form_list if same_domain(f)]

    if form_list:
        # Create one PostDataRequest for each form variant
        mode = cf.cf.get('form_fuzzing_mode')
        for form in form_list:
            for variant in form.get_variants(mode):
                if form.get_method().upper() == 'POST':
                    r = PostDataRequest(
                        variant.get_action(),
                        variant.get_method(),
                        req_headers,
                        cookie_obj,
                        variant)
                else:
                    # The default is a GET request
                    r = QsRequest(
                        variant.get_action(),
                        headers=req_headers,
                        cookie=cookie_obj
                    )
                    r.set_dc(variant)

                res.append(r)
    return res


def create_fuzzable_request_from_request(request, add_headers=None):
    """
    :return: A fuzzable request with the same info as request
    """
    if not isinstance(request, HTTPRequest):
        raise TypeError('Requires HTTPRequest to create FuzzableRequest.')
    
    url = request.url_object
    post_data = str(request.get_data() or '')
    method = request.get_method()
    headers = Headers(request.headers.items())
    headers.update(request.unredirected_hdrs.items())
    headers.update(add_headers or Headers())

    return create_fuzzable_request_from_parts(url, method=method,
                                              post_data=post_data,
                                              add_headers=headers)

ALL_FUZZABLE_REQUESTS = [QsRequest, MultipartRequest, JSONPostDataRequest,
                         XMLRPCRequest, URLEncPostRequest]


def create_fuzzable_request_from_parts(url, method='GET', post_data='',
                                       add_headers=None):
    """
    Creates a fuzzable request based on the input parameters.

    :param req_url: A URL object
    :param method: A string that represents the method ('GET', 'POST', etc)
    :param post_data: A string that represents the postdata.
    :param add_headers: A Headers object that holds the headers. If `req_url` is a
                        request then this dict will be merged with the request's
                        headers.
    """
    if add_headers is not None and not isinstance(add_headers, Headers):
        raise ValueError('create_fuzzable_request requires Headers object.')
    
    if not isinstance(url, URL):
        raise TypeError('Requires URL to create FuzzableRequest.')

    headers = add_headers or Headers()

    for fr_klass in ALL_FUZZABLE_REQUESTS:
        try:
            return fr_klass.from_parts(url, method, post_data, headers)
        except ValueError:
            continue

    return None


def _create_cookie(http_response):
    """
    Create a cookie object based on a HTTP response.
    """
    cookies = []

    # Get data from RESPONSE
    response_headers = http_response.get_headers()

    for hname, hvalue in response_headers.iteritems():
        if 'cookie' in hname.lower():
            cookies.append(hvalue)

    cookie_inst = Cookie(''.join(cookies))

    #
    # delete everything that the browsers usually keep to themselves, since
    # this cookie object is the one we're going to send to the wire
    #
    for key in ['path', 'expires', 'domain', 'max-age']:
        try:
            del cookie_inst[key]
        except:
            pass

    return cookie_inst
