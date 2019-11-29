"""
blacklist.py

Copyright 2013 Andres Riancho

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
import urllib
import urllib2
import mimetools
import cStringIO

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.config as cf

from w3af.core.data.url.helpers import new_no_content_resp


class BlacklistHandler(urllib2.BaseHandler):
    """
    If the user blacklisted a URL, this handler will know about it and
    return an empty HTTP response.
    
    This feature was in the extended_urllib.py module before, but the problem
    there was that any HTTP responses created and returned at that level did
    not pass through all the other configured handlers and in some cases
    this triggered bugs and errors.
    """

    handler_order = urllib2.HTTPErrorProcessor.handler_order - 1

    def __init__(self):
        self._blacklist_urls = None
        self._compiled_ignore_re = None

    def _read_configuration_settings(self):
        #
        # Read the compiled regular expression to use to ignore URLs, this
        # might be None (when the user doesn't configure an ignore_regex)
        #
        self._compiled_ignore_re = cf.cf.get('ignore_regex')

        #
        # Read the list of URLs to blacklist
        #
        blacklist_http_request = cf.cf.get('blacklist_http_request') or []
        self._blacklist_urls = {url.uri2url() for url in blacklist_http_request}

    def default_open(self, req):
        """
        If blacklisted return an empty response, else return None, which means
        that this handler was unable to handle the request and the next one
        needs to be called. With this we want to indicate that the keepalive
        handler will be called.
        """
        if self._blacklist_urls is None:
            # This happens only during the first HTTP request
            self._read_configuration_settings()

        uri = req.url_object

        if not self._is_blacklisted(uri):
            # This means: I don't know how to handle this, call the next opener
            return None

        msg = ('%s was included in the HTTP request blacklist, the scan'
               ' engine is NOT sending the HTTP request and is instead'
               ' returning an empty response to the plugin.')
        om.out.debug(msg % uri)

        # Return a 204 response
        no_content = new_no_content_resp(req.url_object)
        no_content = http_response_to_httplib(no_content)
        return no_content

    def _is_blacklisted(self, uri):
        """
        If the user configured w3af to ignore a URL, we are going to be applying
        that configuration here. This is the lowest layer inside w3af.
        """
        if uri.uri2url() in self._blacklist_urls:
            return True

        if self._compiled_ignore_re is not None:
            if self._compiled_ignore_re.match(uri.url_string):
                return True

        return False


def http_response_to_httplib(no_content):
    header_string = cStringIO.StringIO(str(no_content.get_headers()))
    headers = mimetools.Message(header_string)
    
    no_content = urllib.addinfourl(cStringIO.StringIO(no_content.get_body()),
                                   headers,
                                   no_content.get_url().url_string,
                                   code=no_content.get_code())
    no_content.msg = 'No content'
    return no_content
