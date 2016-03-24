# -*- encoding: utf-8 -*-
"""
test_utils.py

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
import unittest

from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.controllers.csp.utils import CSP, CSPPolicy

class TestUtils(unittest.TestCase):
    header = 'Content-Security-Policy'
    header_report_only = 'Content-Security-Policy-Report-Only'

    def setUp(self):
        self.url = URL('http://moth/')

    def test_unsafe_inline_enabled_no_case01(self):
        """
        Test case in which site do not provides "unsafe-inline" related CSP
        (no directive value "unsafe-inline").
        """
        csp_value = "script-src 'self'; report-uri /myrelativeuri"
        csp = CSPPolicy()
        csp.init_value(csp_value)
        self.assertFalse(csp.unsafe_inline_enabled())

    def test_unsafe_inline_enabled_no_case02(self):
        """
        Test case in which site do not provides "unsafe-inline" related CSP
        (directive value "unsafe-inline" for a directive other than Script or
        Style).
        """
        csp_value = "default-src 'none'; img-src 'unsafe-inline'"
        csp = CSPPolicy()
        csp.init_value(csp_value)
        self.assertFalse(csp.unsafe_inline_enabled())

    def test_unsafe_inline_enabled_yes_case01(self):
        """
        Test case in which site provides "unsafe-inline" related CSP for
        script.
        """
        csp_value =  "script-src 'unsafe-inline'"
        csp = CSPPolicy()
        csp.init_value(csp_value)
        self.assertTrue(csp.unsafe_inline_enabled())

    def test_unsafe_inline_enabled_yes_case02(self):
        """
        Test case in which site provides "unsafe-inline" related CSP for
        Style.
        """
        csp_value =  "style-src 'unsafe-inline'"
        csp = CSPPolicy()
        csp.init_value(csp_value)
        self.assertTrue(csp.unsafe_inline_enabled())

    def test_retrieve_csp_report_uri_no(self):
        """
        Test case in which site do not provides CSP report uri.
        """
        csp = CSPPolicy()
        csp.init_value('')
        uri_set = csp.get_report_uri()
        self.assertIsNone(uri_set)

    def test_retrieve_csp_report_uri_yes(self):
        """
        Test case in which site provides CSP report uri.
        """
        csp_value =  "default-src 'self'; report-uri foo.com/myrelativeuri"
        csp = CSPPolicy()
        csp.init_value(csp_value)
        uri_set = csp.get_report_uri()
        self.assertEqual("foo.com/myrelativeuri", uri_set)

    def test_provides_csp_features_no_case01(self):
        """
        Test case in which site do not provides CSP features.
        """
        csp = CSPPolicy()
        self.assertFalse(csp.init_from_header('', ''))

    def test_provides_csp_features_no_case02(self):
        """
        Test case in which site provides broken CSP.
        """
        # Note the errors in the directive:
        #     default-src -> default-source
        #     img-src -> image-src
        header_value = "default-source 'self'; image-src *"
        csp = CSPPolicy()
        self.assertFalse(csp.init_value(header_value))

    def test_provides_csp_features_no_case03(self):
        """
        Test case in which site provides broken CSP 2.
        """
        header_value = "default-src ' '; img-src ' '"
        csp = CSPPolicy()
        print csp.init_value(header_value), csp.directives
        self.assertFalse(csp.init_value(header_value))
        
    def test_provides_csp_features_yes_case01(self):
        """
        Test case in which site provides CSP features using only mandatory
        policies.
        """
        header_value = "default-src 'self'; img-src *;"\
                       " object-src media1.example.com media2.example.com"\
                       " *.cdn.example.com; script-src"\
                       " trustedscripts.example.com"
        csp = CSPPolicy()
        self.assertTrue(csp.init_value(header_value))
        
    def test_provides_csp_features_yes_case02(self):
        """
        Test case in which site provides CSP features using only report-only
        policies.
        """
        header_value = "default-src 'self'; img-src *; object-src"\
                       " media1.example.com media2.example.com"\
                       " *.cdn.example.com; script-src"\
                       " trustedscripts.example.com"
        csp = CSPPolicy()
        self.assertTrue(csp.init_from_header('Content-Security-Policy-Report-Only', header_value))

    def test_retrieve_csp_policies_without_policies(self):
        """
        Test case in which no policies are specified into HTTP response.
        """
        csp_headers = Headers({}.items())
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        csp = CSP()
        self.assertFalse(csp.init_from_response(http_response))

    def test_retrieve_csp_policies_with_directives_case02(self):
        """
        Test case in which several directives are specified using only 1 CSP
        header but with 6 differents directives.
        """
        header_value = "default-src 'self'; img-src *;"\
                       " object-src media1.example.com media2.example.com"\
                       " *.cdn.example.com; script-src trustedscripts.example.com;"\
                       " form-action foo.com/ctxroot/action1 foo.com/ctxroot/action2;"\
                       " plugin-types application/pdf audio/ogg;"
        csp = CSPPolicy()
        csp.init_value(header_value)
        
        self.assertEqual(len(csp.directives), 6)
        d = csp.get_directive_by_name("default-src")
        self.assertIsNotNone(d)
        self.assertEqual(d.source_list[0], "'self'")
        d = csp.get_directive_by_name("img-src")
        self.assertIsNotNone(d)
        self.assertEqual(d.source_list[0], "*")
        d = csp.get_directive_by_name("script-src")
        self.assertIsNotNone(d)
        self.assertEqual(d.source_list[0], "trustedscripts.example.com")
        d = csp.get_directive_by_name("object-src")
        self.assertIsNotNone(d)
        self.assertTrue("media1.example.com" in d.source_list)
        self.assertTrue("media2.example.com" in d.source_list)
        self.assertTrue("*.cdn.example.com" in d.source_list)
        d = csp.get_directive_by_name("form-action")
        self.assertEqual(len(d.source_list), 2)
        self.assertTrue("foo.com/ctxroot/action1" in d.source_list)
        self.assertTrue("foo.com/ctxroot/action2" in d.source_list)
        d = csp.get_directive_by_name("plugin-types")
        self.assertEqual(len(d.media_type_list), 2)
        self.assertTrue("application/pdf" in d.media_type_list)
        self.assertTrue("audio/ogg" in d.media_type_list)

    def test_retrieve_csp_policies_with_special_policies_case02(self):
        """
        Test case in which 2 directives are specified using special directives
        with explicit values.
        """
        header_value = "sandbox allow-forms allow-scripts ;"\
                       " script-src 'nonce-AABBCCDDEE'"
        csp = CSPPolicy()
        csp.init_value(header_value)
        self.assertEqual(len(csp.directives), 2)
        d = csp.get_directive_by_name("sandbox")
        self.assertEqual(len(d.flags), 2)
        self.assertTrue("allow-forms" in d.flags)
        self.assertTrue("allow-scripts" in d.flags)
        d = csp.get_directive_by_name("script-src")
        self.assertIsNotNone(d)
        self.assertEqual(d.source_list[0], "'nonce-AABBCCDDEE'") 
        
    def test_find_vulns_case01(self):
        """
        Test case in which we set vulnerables policies using "*" as source  
        for all directives that allow this value.
        """ 
        header_value = "default-src *;script-src *;object-src *;" \
                       "style-src *;img-src *;media-src *;" \
                       "frame-src *;font-src *;" \
                       "form-action *;connect-src *;"
        csp = CSPPolicy()
        csp.init_value(header_value)
        vulns = csp.find_vulns()
        self.assertEqual(len(vulns), 10)
        vulns = csp.find_vulns_by_directive("default-src")
        self.assertEqual(len(vulns), 1)
        vulns = csp.find_vulns_by_directive("script-src")
        self.assertEqual(len(vulns), 1)
        vulns = csp.find_vulns_by_directive("object-src")
        self.assertEqual(len(vulns), 1)
        vulns = csp.find_vulns_by_directive("style-src")
        self.assertEqual(len(vulns), 1)
        vulns = csp.find_vulns_by_directive("img-src")
        self.assertEqual(len(vulns), 1)
        vulns = csp.find_vulns_by_directive("media-src")
        self.assertEqual(len(vulns), 1)
        vulns = csp.find_vulns_by_directive("frame-src")
        self.assertEqual(len(vulns), 1)
        vulns = csp.find_vulns_by_directive("font-src")
        self.assertEqual(len(vulns), 1)
        vulns = csp.find_vulns_by_directive("connect-src")
        self.assertEqual(len(vulns), 1)
        vulns = csp.find_vulns_by_directive("form-action")
        self.assertEqual(len(vulns), 1)

    def test_find_vulns_case04(self):
        """
        Test case in which we configure correctly policies for all directives.
        """  
        header_value = "default-src 'self';script-src 'self'; object-src 'self';" \
                       "style-src 'self'; img-src 'self'; media-src 'self';" \
                       "frame-src 'self'; font-src 'self'; sandbox;" \
                       "form-action foo.com/myCtx/act; connect-src 'self';"\
                       "plugin-types application/pdf;"
        csp = CSPPolicy()
        csp.init_value(header_value)
        vulns = csp.find_vulns()
        self.assertEqual(len(vulns), 0)     
        
    def test_find_vulns_case05(self):
        """
        Test case in which we misspell somes policies.
        """  
        header_value = "defauld-src 'self';script-src 'self';object-src 'self';" \
                       "style-src 'self';image-src 'self';media-src 'self';"
        csp = CSPPolicy()
        csp.init_value(header_value)
        vulns = csp.find_vulns()
        self.assertEqual(len(vulns), 1)
        
    def test_site_protected_against_xss_by_csp_case01(self):
        """
        Test case in witch site do not provide CSP features.
        """
        csp = CSPPolicy()
        csp.init_value('')
        self.assertFalse(csp.protects_against_xss())
              
    def test_site_protected_against_xss_by_csp_case02(self):
        """
        Test case in witch site provide CSP features and have a vuln 
        on Script policies.
        """
        header_value = "script-src *;"
        csp = CSPPolicy()
        csp.init_value(header_value)
        self.assertFalse(csp.protects_against_xss())
        
    def test_site_protected_against_xss_by_csp_case03(self):
        """
        Test case in witch site provides CSP features and enable unsafe inline
        script into is CSP Script policies. Browsers switches off 'unsafe-inline' 
        when finds nonses/hashes in sources of script-src
        """
        header_value = "default-src 'self'; script-src 'self' unsafe-inline 'nonce-AADD';"
        csp = CSPPolicy()
        csp.init_value(header_value)
        self.assertTrue(csp.protects_against_xss())

    def test_site_protected_against_xss_by_csp_case04(self):
        """
        Test case in witch site provide CSP features and enable use of the
        javascript "eval()" function into is CSP Script policies BUT we do 
        accept theses configurations.
        """
        header_value = "default-src 'self'; script-src 'self' 'unsafe-eval' 'nonce-AADD'"
        csp = CSPPolicy()
        csp.init_value(header_value)
        self.assertTrue(csp.protects_against_xss())
        
    def test_site_protected_against_xss_by_csp_case06(self):
        """
        Test case in witch site is secure
        """
        header_value = "default-src 'self'"
        csp = CSPPolicy()
        csp.init_value(header_value)
        self.assertTrue(csp.protects_against_xss())


    def test_site_protected_against_xss_by_csp_case07(self):
        """
        Test case in we check for protects_against_xss() high level CSP object
        """
        header_value = "default-src 'self'; script-src 'self' trust.com;"
        headers = Headers({'Content-Security-Policy': header_value}.items())
        http_response = HTTPResponse(200, '', headers, self.url, self.url)
        csp = CSP()
        csp.init_from_response(http_response)
        self.assertTrue(csp.protects_against_xss())
 
    def test_retrieve_csp_policies_from_meta(self):
        """
        Test case in which no policies are specified into HTTP response.
        """
        html_data =  """<html><head>
        <meta http-equiv="Content-Security-Policy" content="script-src 'self'">
        </head><body></body></html>"""
        headers = Headers({'Content-Type':'text/html; charset=UTF-8'}.items())
        http_response = HTTPResponse(200, html_data, headers, self.url, self.url)
        csp = CSP()
        csp.init_from_response(http_response)
        self.assertEqual(len(csp.policies), 1)

    def test_find_vulns_untrusted(self):
        """
        Test case in which we add untrusted hosts into somes policies.
        """  
        header_value = "default-src 'self'; script-src blob: data: 'self' trust.com evil.com;"
        csp = CSPPolicy()
        csp.trusted_hosts = ['trust.com']
        csp.init_value(header_value)
        vulns = csp.find_vulns()
        self.assertEqual(len(vulns), 1)
