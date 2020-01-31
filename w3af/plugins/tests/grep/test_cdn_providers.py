import unittest

from w3af.core.data.dc.headers import Headers
from w3af.core.data.kb.knowledge_base import kb
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.plugins.grep.cdn_providers import cdn_providers


class TestCDNProviders(unittest.TestCase):
    def setUp(self):
        self.plugin = cdn_providers()
        kb.clear('cdn_providers', 'cdn_providers')

    def tearDown(self):
        self.plugin.end()

    def test_if_cdn_can_be_detected(self):
        url = URL('https://example.com/')
        headers = Headers([('server', 'Netlify')])
        response = HTTPResponse(200, '', headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(len(kb.get('cdn_providers', 'cdn_providers')), 1)

    def test_if_cdns_are_grouped_by_provider_name(self):
        netlify_header = Headers([('server', 'Netlify')])
        cloudflare_header = Headers([('server', 'cloudflare')])

        url = URL('https://example.com/')
        request = FuzzableRequest(url, method='GET')
        response = HTTPResponse(200, '', netlify_header, url, url, _id=1)
        self.plugin.grep(request, response)

        # this request should be grouped with the request above
        url = URL('https://example.com/another-netflify/')
        request = FuzzableRequest(url, method='GET')
        response = HTTPResponse(200, '', netlify_header, url, url, _id=2)
        self.plugin.grep(request, response)

        # this request should be stored separately in kb as it comes from another provider
        url = URL('https://example.com/cloudflare/')
        request = FuzzableRequest(url, method='GET')
        response = HTTPResponse(200, '', cloudflare_header, url, url, _id=3)
        self.plugin.grep(request, response)

        self.assertEqual(len(kb.get('cdn_providers', 'cdn_providers')), 2)
