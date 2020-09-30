import pytest

from w3af.core.data.dc.headers import Headers
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.core.data.url.HTTPResponse import HTTPResponse


@pytest.fixture
def http_response():
    url = URL('http://example.com/')
    headers = Headers([('content-type', 'text/html')])
    return HTTPResponse(
        200,
        '<body></body>',
        headers,
        url,
        url,
    )


@pytest.fixture
def http_request():
    url = URL('http://example.com/')
    headers = Headers([('content-type', 'text/html')])
    return HTTPRequest(
        url,
        headers,
        method='GET',
    )
