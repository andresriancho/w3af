# -*- encoding: utf-8 -*-
'''
test_utils.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''
import unittest

from core.data.url.HTTPResponse import HTTPResponse
from core.data.parsers.url import URL
from core.data.dc.headers import Headers

from core.controllers.csp.utils import (unsafe_inline_enabled,
                                        retrieve_csp_report_uri,
                                        provides_csp_features,
                                        retrieve_csp_policies,
                                        CSP_HEADER_CHROME,
                                        CSP_HEADER_FIREFOX,
                                        CSP_HEADER_W3C,
                                        CSP_DIRECTIVE_OBJECT,
                                        CSP_DIRECTIVE_DEFAULT,
                                        CSP_DIRECTIVE_IMAGE,
                                        CSP_DIRECTIVE_SCRIPT,
                                        CSP_DIRECTIVE_CONNECTION,
                                        CSP_HEADER_W3C_REPORT_ONLY,
                                        CSP_DIRECTIVE_REPORT_URI,
                                        CSP_DIRECTIVE_VALUE_UNSAFE_INLINE,
                                        CSP_DIRECTIVE_STYLE)


class TestUtils(unittest.TestCase):

    def setUp(self):
        self.url = URL('http://moth/')

    def test_unsafe_inline_enabled_no_case01(self):
        '''
        Test case in which site do not provides "unsafe-inline" related CSP
        (no directive value "unsafe-inline").
        '''
        hrds = {}
        hrds[CSP_HEADER_FIREFOX] = CSP_DIRECTIVE_SCRIPT + " 'self'"
        hrds[CSP_HEADER_W3C_REPORT_ONLY] = CSP_DIRECTIVE_DEFAULT + \
            " 'self';" + CSP_DIRECTIVE_REPORT_URI + " http://example.com"
        hrds[CSP_HEADER_W3C] = CSP_DIRECTIVE_SCRIPT + " 'self';" + \
            CSP_DIRECTIVE_REPORT_URI + " /myrelativeuri"
        
        csp_headers = Headers(hrds.items())
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        
        self.assertFalse(unsafe_inline_enabled(http_response))

    def test_unsafe_inline_enabled_no_case02(self):
        '''
        Test case in which site do not provides "unsafe-inline" related CSP
        (directive value "unsafe-inline" for a directive other than Script or
        Style).
        '''
        hrds = {}
        hrds[CSP_HEADER_FIREFOX] = CSP_DIRECTIVE_IMAGE + " '" + \
            CSP_DIRECTIVE_VALUE_UNSAFE_INLINE + "'"
        hrds[CSP_HEADER_W3C_REPORT_ONLY] = CSP_DIRECTIVE_DEFAULT + \
            " 'self';" + CSP_DIRECTIVE_REPORT_URI + " http://example.com"
        hrds[CSP_HEADER_W3C] = CSP_DIRECTIVE_SCRIPT + " 'self';" + \
            CSP_DIRECTIVE_REPORT_URI + " /myrelativeuri"
        
        csp_headers = Headers(hrds.items())
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        
        self.assertFalse(unsafe_inline_enabled(http_response))

    def test_unsafe_inline_enabled_yes_case01(self):
        '''
        Test case in which site provides "unsafe-inline" related CSP for
        script.
        '''
        hrds = {}
        hrds[CSP_HEADER_FIREFOX] = CSP_DIRECTIVE_SCRIPT + " '" + \
            CSP_DIRECTIVE_VALUE_UNSAFE_INLINE + "'"
        hrds[CSP_HEADER_W3C] = CSP_DIRECTIVE_SCRIPT + " 'self';" + \
            CSP_DIRECTIVE_REPORT_URI + " /myrelativeuri"
        
        csp_headers = Headers(hrds.items())
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        
        self.assertTrue(unsafe_inline_enabled(http_response))

    def test_unsafe_inline_enabled_yes_case02(self):
        '''
        Test case in which site provides "unsafe-inline" related CSP for
        Style.
        '''
        hrds = {}
        hrds[CSP_HEADER_FIREFOX] = CSP_DIRECTIVE_STYLE + " '" + \
            CSP_DIRECTIVE_VALUE_UNSAFE_INLINE + "'"
        hrds[CSP_HEADER_W3C] = CSP_DIRECTIVE_SCRIPT + " 'self';" + \
            CSP_DIRECTIVE_REPORT_URI + " /myrelativeuri"
        
        csp_headers = Headers(hrds.items())
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        
        self.assertTrue(unsafe_inline_enabled(http_response))

    def test_retrieve_csp_report_uri_no(self):
        '''
        Test case in which site do not provides CSP report uri.
        '''
        hrds = {}.items()
        csp_headers = Headers(hrds)
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        uri_set = retrieve_csp_report_uri(http_response)
        self.assertEqual(len(uri_set), 0)

    def test_retrieve_csp_report_uri_yes(self):
        '''
        Test case in which site provides CSP report uri.
        '''
        hrds = {}
        hrds[CSP_HEADER_FIREFOX] = CSP_DIRECTIVE_OBJECT + " 'self'"
        hrds[CSP_HEADER_W3C_REPORT_ONLY] = CSP_DIRECTIVE_DEFAULT + \
            " 'self';" + CSP_DIRECTIVE_REPORT_URI + " http://example.com"
        hrds[CSP_HEADER_W3C] = CSP_DIRECTIVE_SCRIPT + " 'self';" + \
            CSP_DIRECTIVE_REPORT_URI + " /myrelativeuri"
        
        csp_headers = Headers(hrds.items())
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        uri_set = retrieve_csp_report_uri(http_response)
        
        self.assertEqual(len(uri_set), 2)
        self.assertTrue("http://example.com" in uri_set)
        self.assertTrue("/myrelativeuri" in uri_set)

    def test_provides_csp_features_no_case01(self):
        '''
        Test case in which site do not provides CSP features.
        '''
        hrds = {}.items()
        csp_headers = Headers(hrds)
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        self.assertFalse(provides_csp_features(http_response))

    def test_provides_csp_features_no_case02(self):
        '''
        Test case in which site provides broken CSP.
        '''
        # Note the errors in the directive:
        #     default-src -> default-source
        #     img-src -> image-src
        header_value = "default-source 'self'; image-src *"
        hrds = {CSP_HEADER_W3C: header_value}.items()
        csp_headers = Headers(hrds)
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        
        self.assertFalse(provides_csp_features(http_response))

    def test_provides_csp_features_no_case03(self):
        '''
        Test case in which site provides broken CSP.
        '''
        # Note the errors in the directive:
        #     default-src -> default-source
        #     img-src -> image-src
        header_value = "default-src ' '; img-src ' '"
        hrds = {CSP_HEADER_W3C: header_value}.items()
        csp_headers = Headers(hrds)
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        
        self.assertFalse(provides_csp_features(http_response))
        
    def test_provides_csp_features_yes_case01(self):
        '''
        Test case in which site provides CSP features using only mandatory
        policies.
        '''
        header_value = "default-src 'self'; img-src *;"\
                       " object-src media1.example.com media2.example.com"\
                       " *.cdn.example.com; script-src"\
                       " trustedscripts.example.com"
        hrds = {CSP_HEADER_W3C: header_value}.items()
        csp_headers = Headers(hrds)
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        
        self.assertTrue(provides_csp_features(http_response))
        
    def test_provides_csp_features_yes_case02(self):
        '''
        Test case in which site provides CSP features using only report-only
        policies.
        '''
        header_value = "default-src 'self'; img-src *; object-src"\
                       " media1.example.com media2.example.com"\
                       " *.cdn.example.com; script-src"\
                       " trustedscripts.example.com"
        hrds = {CSP_HEADER_W3C_REPORT_ONLY: header_value}.items()
        csp_headers = Headers(hrds)
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        
        self.assertTrue(provides_csp_features(http_response))

    def test_provides_csp_features_yes_case03(self):
        '''
        Test case in which site provides CSP features using report-only +
        mandatory policies.
        '''
        hrds = {}
        hrds[CSP_HEADER_W3C] = CSP_DIRECTIVE_OBJECT + " 'self'"
        hrds[CSP_HEADER_W3C_REPORT_ONLY] = CSP_DIRECTIVE_CONNECTION + " *"
        csp_headers = Headers(hrds.items())
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        
        self.assertTrue(provides_csp_features(http_response))

    def test_retrieve_csp_policies_without_policies(self):
        '''
        Test case in which no policies are specified into HTTP response.
        '''
        hrds = {}.items()
        csp_headers = Headers(hrds)
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        policies = retrieve_csp_policies(http_response)
        self.assertEqual(len(policies), 0)

    def test_retrieve_csp_policies_with_policies_case01(self):
        '''
        Test case in which 1 same policy is specified using 3 differents CSP
        headers.
        '''
        hrds = {}
        hrds[CSP_HEADER_W3C] = CSP_DIRECTIVE_OBJECT + " 'self'"
        hrds[CSP_HEADER_FIREFOX] = CSP_DIRECTIVE_OBJECT + " *"
        hrds[CSP_HEADER_CHROME] = CSP_DIRECTIVE_OBJECT + " *.sample.com"
        csp_headers = Headers(hrds.items())
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        
        policies = retrieve_csp_policies(http_response)
        
        self.assertEqual(len(policies), 1)
        self.assertEqual(len(policies[CSP_DIRECTIVE_OBJECT]), 3)
        self.assertTrue("self" in policies[CSP_DIRECTIVE_OBJECT])
        self.assertTrue("*" in policies[CSP_DIRECTIVE_OBJECT])
        self.assertTrue("*.sample.com" in policies[CSP_DIRECTIVE_OBJECT])

    def test_retrieve_csp_policies_with_policies_case02(self):
        '''
        Test case in which several policies are specified using only 1 CSP
        header but with 3 differents directives.
        '''
        header_value = "default-src 'self'; img-src *; object-src"\
                       " media1.example.com media2.example.com"\
                       " *.cdn.example.com; script-src trustedscripts.example.com"
        hrds = {CSP_HEADER_W3C: header_value}.items()
        csp_headers = Headers(hrds)
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        policies = retrieve_csp_policies(http_response)
        
        self.assertEqual(len(policies), 4)
        self.assertEqual(len(policies[CSP_DIRECTIVE_DEFAULT]), 1)
        self.assertEqual(policies[CSP_DIRECTIVE_DEFAULT][0], "self")
        self.assertEqual(len(policies[CSP_DIRECTIVE_IMAGE]), 1)
        self.assertEqual(policies[CSP_DIRECTIVE_IMAGE][0], "*")
        self.assertEqual(len(policies[CSP_DIRECTIVE_SCRIPT]), 1)
        self.assertEqual(
            policies[CSP_DIRECTIVE_SCRIPT][0], "trustedscripts.example.com")
        self.assertEqual(len(policies[CSP_DIRECTIVE_OBJECT]), 3)
        self.assertTrue("media1.example.com" in policies[CSP_DIRECTIVE_OBJECT])
        self.assertTrue("media2.example.com" in policies[CSP_DIRECTIVE_OBJECT])
        self.assertTrue("*.cdn.example.com" in policies[CSP_DIRECTIVE_OBJECT])

    def test_retrieve_csp_policies_with_policies_case03(self):
        '''
        Test case in which 3 policies are specified using 3 differents CSP headers.
        '''
        hrds = {}
        hrds[CSP_HEADER_W3C] = CSP_DIRECTIVE_OBJECT + " 'none'"
        hrds[CSP_HEADER_FIREFOX] = CSP_DIRECTIVE_IMAGE + " *"
        hrds[CSP_HEADER_CHROME] = CSP_DIRECTIVE_CONNECTION + \
            " trust.sample.com"
        csp_headers = Headers(hrds.items())
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        policies = retrieve_csp_policies(http_response)
        
        self.assertEqual(len(policies), 3)
        self.assertEqual(len(policies[CSP_DIRECTIVE_OBJECT]), 1)
        self.assertEqual(policies[CSP_DIRECTIVE_OBJECT][0], "none")
        self.assertEqual(len(policies[CSP_DIRECTIVE_IMAGE]), 1)
        self.assertEqual(policies[CSP_DIRECTIVE_IMAGE][0], "*")
        self.assertEqual(len(policies[CSP_DIRECTIVE_CONNECTION]), 1)
        self.assertEqual(
            policies[CSP_DIRECTIVE_CONNECTION][0], "trust.sample.com")

    def test_retrieve_csp_policies_with_policies_case04(self):
        '''
        Test case in which 4 policies are specified using 4 differents CSP
        headers and in which 1 is specified using report only CSP header.
        Test in which we want only mandatory policies.
        '''
        hrds = {}
        hrds[CSP_HEADER_W3C] = CSP_DIRECTIVE_OBJECT + " 'none'"
        hrds[CSP_HEADER_FIREFOX] = CSP_DIRECTIVE_IMAGE + " *"
        hrds[CSP_HEADER_CHROME] = CSP_DIRECTIVE_CONNECTION + \
            " trust.sample.com"
        hrds[CSP_HEADER_W3C_REPORT_ONLY] = CSP_DIRECTIVE_SCRIPT + \
            " report.sample.com"
        csp_headers = Headers(hrds.items())
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        policies = retrieve_csp_policies(http_response)
        
        self.assertEqual(len(policies), 3)
        self.assertEqual(len(policies[CSP_DIRECTIVE_OBJECT]), 1)
        self.assertEqual(policies[CSP_DIRECTIVE_OBJECT][0], "none")
        self.assertEqual(len(policies[CSP_DIRECTIVE_IMAGE]), 1)
        self.assertEqual(policies[CSP_DIRECTIVE_IMAGE][0], "*")
        self.assertEqual(len(policies[CSP_DIRECTIVE_CONNECTION]), 1)
        self.assertEqual(
            policies[CSP_DIRECTIVE_CONNECTION][0], "trust.sample.com")

    def test_retrieve_csp_policies_with_policies_case05(self):
        '''
        Test case in which 4 policies are specified using 4 differents CSP
        headers and in which 1 is specified using report only CSP header.
        Test in which we want only report-only policies.
        '''
        hrds = {}
        hrds[CSP_HEADER_W3C] = CSP_DIRECTIVE_OBJECT + " 'none'"
        hrds[CSP_HEADER_FIREFOX] = CSP_DIRECTIVE_IMAGE + " *"
        hrds[CSP_HEADER_CHROME] = CSP_DIRECTIVE_CONNECTION + \
            " trust.sample.com"
        hrds[CSP_HEADER_W3C_REPORT_ONLY] = CSP_DIRECTIVE_SCRIPT + \
            " report.sample.com"
        csp_headers = Headers(hrds.items())
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        policies = retrieve_csp_policies(http_response, True)
        
        self.assertEqual(len(policies), 1)
        self.assertEqual(len(policies[CSP_DIRECTIVE_SCRIPT]), 1)
        self.assertEqual(
            policies[CSP_DIRECTIVE_SCRIPT][0], "report.sample.com")
