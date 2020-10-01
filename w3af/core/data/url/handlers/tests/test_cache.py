# -*- coding: utf-8 -*-
"""
test_cache.py

Copyright 2012 Andres Riancho

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
import urllib2
import unittest

import pytest
from mock import patch, Mock, _Call, MagicMock

from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.core.data.url.handlers.cache import CacheHandler
from w3af.core.data.url import opener_settings
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers


class TestCacheHandler:
    def setup_method(self):
        self.url = URL('http://www.w3af.org')
        self.request = HTTPRequest(self.url, cache=True)
        self.response = FakeHttplibHTTPResponse(
            200, 'OK', 'spameggs', Headers(), self.url.url_string
        )

    def teardown_method(self):
        CacheHandler().clear()

    def test_basic(self):

        cache = CacheHandler()
        assert cache.default_open(self.request) is None

        cc_mock = MagicMock()
        cache._cache_class = cc_mock
        store_in_cache = Mock()
        cc_mock.attach_mock(store_in_cache, 'store_in_cache')

        # This stores the response
        cache.http_response(self.request, self.response)

        # Make sure the right call was made
        _call = _Call(('store_in_cache', (self.request, self.response)))
        assert cc_mock.mock_calls == [_call]
        cc_mock.reset_mock()

        exists_in_cache = Mock()
        cc_mock.return_value = self.response
        cc_mock.attach_mock(exists_in_cache, 'exists_in_cache')

        # This retrieves the response from the "cache"
        cached_response = cache.default_open(self.request)

        # Make sure the right call was made
        _exists_call = _Call(('exists_in_cache', (self.request,)))
        _retrieve_call = _Call(((self.request,), {}))
        assert cc_mock.mock_calls == [_exists_call, _retrieve_call]

        assert cached_response is not None
        
        assert cached_response.code == self.response.code
        assert cached_response.msg == self.response.msg
        assert cached_response.read() == self.response.read()
        assert Headers(cached_response.info().items()) == self.response.info()
        assert cached_response.geturl() == self.response.geturl()

    def test_no_cache(self):
        url = URL('http://www.w3af.org')
        request = HTTPRequest(url, cache=False)

        cache = CacheHandler()
        assert cache.default_open(request) is None

        response = FakeHttplibHTTPResponse(200, 'OK', 'spameggs', Headers(),
                                           url.url_string)
        cache.http_response(request, response)
        assert cache.default_open(request) is None


class TestCacheIntegration:
    def setup_method(self):
        self.http_response = FakeHttplibHTTPResponse(
            200,
            'OK',
            '<body></body>',
            Headers(),
            'http://example.com/'
        )

    @pytest.mark.skip('uses internet')
    def test_cache_http_errors(self):
        settings = opener_settings.OpenerSettings()
        settings.build_openers()
        opener = settings.get_custom_opener()

        url = URL('http://w3af.org/foo-bar-not-exists.htm')
        request = HTTPRequest(url, cache=False)

        with patch('w3af.core.data.url.handlers.cache.DefaultCacheClass') as cc_mock:
            store_in_cache = Mock()
            cc_mock.attach_mock(store_in_cache, 'store_in_cache')

            # If there is a response we should store it, even if it is a 404
            try:
                response = opener.open(request)
            except urllib2.HTTPError:
                pass

            # Make sure the right call was made
            _call = _Call(('store_in_cache', (request, response)))
            assert cc_mock.mock_calls == [_call]
            cc_mock.reset_mock()

            # And make sure the response was a 404
            assert response.status == 404

    def test_cache_handler_with_enabled_cache(self, http_request):
        http_request.get_from_cache = True
        cache_handler = CacheHandler(disable_cache=False)
        cache_handler.http_response(http_request, self.http_response)
        assert cache_handler.default_open(http_request)

    def test_cache_handler_with_disabled_cache(self, http_request):
        http_request.get_from_cache = True
        cache_handler = CacheHandler(disable_cache=True)
        cache_handler.http_response(http_request, self.http_response)
        assert not cache_handler.default_open(http_request)


class FakeHttplibHTTPResponse(object):
    def __init__(self, code, msg, body, headers, url):
        self.code = code
        self.msg = msg
        self.body = body
        self.headers = headers
        self.url = url
    
    def geturl(self):
        return self.url
    
    def read(self):
        return self.body
    
    def info(self):
        return self.headers
