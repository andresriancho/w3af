import pytest
from mock import MagicMock, patch

from w3af.core.data.dc.headers import Headers
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers.doc.wsdl import ZeepTransport, WSDLParser
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.url.extended_urllib import ExtendedUrllib
from w3af.plugins.tests.plugin_testing_tools import NetworkPatcher


@pytest.fixture
def mocked_http_client():
    return MagicMock()


@pytest.fixture
def zeep_transport(mocked_http_client):
    transport = ZeepTransport()
    transport.uri_opener = mocked_http_client
    return transport


@pytest.fixture
def zeep_transport_from_class(zeep_transport):
    return lambda *args, **kwargs: zeep_transport


@pytest.fixture
def http_response():
    return HTTPResponse(
        200,
        '<div></div>',
        Headers(),
        URL('https://example.com/'),
        URL('https://example.com/'),
    )


class TestZeepTransport:
    def test_it_implements_all_needed_methods(self):
        zeep_transport = ZeepTransport()
        required_methods = [
            'get',
            'load',
            'post',
            'post_xml',
        ]
        for method in required_methods:
            assert hasattr(zeep_transport, method)

    def test_it_calls_http_client_on_get_method(self, zeep_transport, mocked_http_client):
        zeep_transport.get('https://example.com/', '', {})
        assert mocked_http_client.GET.called

    def test_it_calls_http_client_on_post_method(self, zeep_transport, mocked_http_client):
        zeep_transport.post('https://example.com/', 'some data', {})
        assert mocked_http_client.POST.called

    def test_it_calls_http_client_on_post_xml_method(self, zeep_transport, mocked_http_client):
        from lxml import etree  # feeding Zeep dependencies
        zeep_transport.post_xml('https://example.com/', etree.Element('test'), {})
        assert mocked_http_client.POST.called

    def test_it_loads_the_response_content(self, zeep_transport, mocked_http_client):
        mocked_response = MagicMock(name='mocked_response')
        mocked_response.body = 'test'
        mocked_http_client.GET = MagicMock(return_value=mocked_response)

        result = zeep_transport.load('http://example.com/')
        assert result == 'test'


class TestZeepTransportIntegration:
    def test_it_can_perform_get_request(self):
        url = 'http://example.com/'
        with NetworkPatcher() as network_patcher:
            zeep_transport = ZeepTransport()
            zeep_transport.get(url, {}, {})
        assert url in network_patcher.mocked_server.urls_requested

    def test_it_can_perform_post_request(self):
        url = 'http://example.com/'
        with NetworkPatcher() as network_patcher:
            zeep_transport = ZeepTransport()
            zeep_transport.post(url, 'some data', {})
        assert url in network_patcher.mocked_server.urls_requested

    def test_it_can_load_url(self):
        url = 'http://example.com/'
        with NetworkPatcher() as network_patcher:
            zeep_transport = ZeepTransport()
            zeep_transport.load('http://example.com/')
        assert url in network_patcher.mocked_server.urls_requested


class TestWSDLParserIntegration:
    def test_wsdl_zeep_transport_uses_extended_urllib(self):
        zeep_transport = ZeepTransport()
        assert isinstance(zeep_transport.uri_opener, ExtendedUrllib)

    def test_it_uses_extended_urllib_for_performing_requests(
        self,
        mocked_http_client,
        zeep_transport_from_class,
        http_response,
    ):
        mocked_http_client.GET = MagicMock(return_value=http_response)
        with patch('w3af.core.data.parsers.doc.wsdl.ZeepTransport', zeep_transport_from_class):
            WSDLParser(http_response=http_response)
        assert mocked_http_client.GET.called
