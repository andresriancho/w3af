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
from w3af.core.controllers.csp.utils import (unsafe_inline_enabled,
                                             retrieve_csp_report_uri,
                                             provides_csp_features,
                                             retrieve_csp_policies,
                                             find_vulns,
                                             site_protected_against_xss_by_csp,
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
                                             CSP_DIRECTIVE_STYLE,
                                             CSP_DIRECTIVE_FORM,
                                             CSP_DIRECTIVE_SANDBOX,
                                             CSP_DIRECTIVE_SCRIPT_NONCE,
                                             CSP_DIRECTIVE_PLUGIN_TYPES,
                                             CSP_DIRECTIVE_XSS,
                                             CSP_DIRECTIVE_MEDIA,
                                             CSP_DIRECTIVE_FRAME,
                                             CSP_DIRECTIVE_FONT,
                                             CSP_MISSPELLED_DIRECTIVES)


class TestUtils(unittest.TestCase):

    def setUp(self):
        self.url = URL('http://moth/')

    def test_unsafe_inline_enabled_no_case01(self):
        """
        Test case in which site do not provides "unsafe-inline" related CSP
        (no directive value "unsafe-inline").
        """
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
        """
        Test case in which site do not provides "unsafe-inline" related CSP
        (directive value "unsafe-inline" for a directive other than Script or
        Style).
        """
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
        """
        Test case in which site provides "unsafe-inline" related CSP for
        script.
        """
        hrds = {}
        hrds[CSP_HEADER_FIREFOX] = CSP_DIRECTIVE_SCRIPT + " '" + \
            CSP_DIRECTIVE_VALUE_UNSAFE_INLINE + "'"
        hrds[CSP_HEADER_W3C] = CSP_DIRECTIVE_SCRIPT + " 'self';" + \
            CSP_DIRECTIVE_REPORT_URI + " /myrelativeuri"
        
        csp_headers = Headers(hrds.items())
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        
        self.assertTrue(unsafe_inline_enabled(http_response))

    def test_unsafe_inline_enabled_yes_case02(self):
        """
        Test case in which site provides "unsafe-inline" related CSP for
        Style.
        """
        hrds = {}
        hrds[CSP_HEADER_FIREFOX] = CSP_DIRECTIVE_STYLE + " '" + \
            CSP_DIRECTIVE_VALUE_UNSAFE_INLINE + "'"
        hrds[CSP_HEADER_W3C] = CSP_DIRECTIVE_SCRIPT + " 'self';" + \
            CSP_DIRECTIVE_REPORT_URI + " /myrelativeuri"
        
        csp_headers = Headers(hrds.items())
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        
        self.assertTrue(unsafe_inline_enabled(http_response))

    def test_retrieve_csp_report_uri_no(self):
        """
        Test case in which site do not provides CSP report uri.
        """
        hrds = {}.items()
        csp_headers = Headers(hrds)
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        uri_set = retrieve_csp_report_uri(http_response)
        self.assertEqual(len(uri_set), 0)

    def test_retrieve_csp_report_uri_yes(self):
        """
        Test case in which site provides CSP report uri.
        """
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
        """
        Test case in which site do not provides CSP features.
        """
        hrds = {}.items()
        csp_headers = Headers(hrds)
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        self.assertFalse(provides_csp_features(http_response))

    def test_provides_csp_features_no_case02(self):
        """
        Test case in which site provides broken CSP.
        """
        # Note the errors in the directive:
        #     default-src -> default-source
        #     img-src -> image-src
        header_value = "default-source 'self'; image-src *"
        hrds = {CSP_HEADER_W3C: header_value}.items()
        csp_headers = Headers(hrds)
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        
        self.assertFalse(provides_csp_features(http_response))

    def test_provides_csp_features_no_case03(self):
        """
        Test case in which site provides broken CSP.
        """
        # Note the errors in the directive:
        #     default-src -> default-source
        #     img-src -> image-src
        header_value = "default-src ' '; img-src ' '"
        hrds = {CSP_HEADER_W3C: header_value}.items()
        csp_headers = Headers(hrds)
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
                
        self.assertFalse(provides_csp_features(http_response))
        
    def test_provides_csp_features_yes_case01(self):
        """
        Test case in which site provides CSP features using only mandatory
        policies.
        """
        header_value = "default-src 'self'; img-src *;"\
                       " object-src media1.example.com media2.example.com"\
                       " *.cdn.example.com; script-src"\
                       " trustedscripts.example.com"
        hrds = {CSP_HEADER_W3C: header_value}.items()
        csp_headers = Headers(hrds)
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        
        self.assertTrue(provides_csp_features(http_response))
        
    def test_provides_csp_features_yes_case02(self):
        """
        Test case in which site provides CSP features using only report-only
        policies.
        """
        header_value = "default-src 'self'; img-src *; object-src"\
                       " media1.example.com media2.example.com"\
                       " *.cdn.example.com; script-src"\
                       " trustedscripts.example.com"
        hrds = {CSP_HEADER_W3C_REPORT_ONLY: header_value}.items()
        csp_headers = Headers(hrds)
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        
        self.assertTrue(provides_csp_features(http_response))

    def test_provides_csp_features_yes_case03(self):
        """
        Test case in which site provides CSP features using report-only +
        mandatory policies.
        """
        hrds = {}
        hrds[CSP_HEADER_W3C] = CSP_DIRECTIVE_OBJECT + " 'self'"
        hrds[CSP_HEADER_W3C_REPORT_ONLY] = CSP_DIRECTIVE_CONNECTION + " *"
        csp_headers = Headers(hrds.items())
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        
        self.assertTrue(provides_csp_features(http_response))

    def test_retrieve_csp_policies_without_policies(self):
        """
        Test case in which no policies are specified into HTTP response.
        """
        hrds = {}.items()
        csp_headers = Headers(hrds)
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        policies = retrieve_csp_policies(http_response)
        self.assertEqual(len(policies), 0)

    def test_retrieve_csp_policies_with_policies_case01(self):
        """
        Test case in which 1 same policy is specified using 3 differents CSP
        headers.
        """
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
        """
        Test case in which several policies are specified using only 1 CSP
        header but with 7 differents directives.
        """
        header_value = "default-src 'self'; img-src *;"\
                       " object-src media1.example.com media2.example.com"\
                       " *.cdn.example.com; script-src trustedscripts.example.com;"\
                       " form-action /ctxroot/action1 /ctxroot/action2;"\
                       " plugin-types application/pdf application/x-java-applet;"\
                       " reflected-xss block"
        hrds = {CSP_HEADER_W3C: header_value}.items()
        csp_headers = Headers(hrds)
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        policies = retrieve_csp_policies(http_response)
        
        self.assertEqual(len(policies), 7)
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
        self.assertEqual(len(policies[CSP_DIRECTIVE_FORM]), 2)
        self.assertTrue("/ctxroot/action1" in policies[CSP_DIRECTIVE_FORM])
        self.assertTrue("/ctxroot/action2" in policies[CSP_DIRECTIVE_FORM])
        self.assertEqual(len(policies[CSP_DIRECTIVE_PLUGIN_TYPES]), 2)
        self.assertTrue(
            "application/pdf" in policies[CSP_DIRECTIVE_PLUGIN_TYPES])
        self.assertTrue(
            "application/x-java-applet" in policies[CSP_DIRECTIVE_PLUGIN_TYPES])
        self.assertEqual(len(policies[CSP_DIRECTIVE_XSS]), 1)
        self.assertTrue("block" in policies[CSP_DIRECTIVE_XSS])                        

    def test_retrieve_csp_policies_with_policies_case03(self):
        """
        Test case in which 3 policies are specified using 3 differents CSP headers.
        """
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
        """
        Test case in which 4 policies are specified using 4 differents CSP
        headers and in which 1 is specified using report only CSP header.
        Test in which we want only mandatory policies.
        """
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
        """
        Test case in which 4 policies are specified using 4 differents CSP
        headers and in which 1 is specified using report only CSP header.
        Test in which we want only report-only policies.
        """
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
        
    def test_retrieve_csp_policies_with_special_policies_case01(self):
        """
        Test case in which 2 policies are specified using special directives
        with empty value.
        """
        header_value = "sandbox ; script-nonce "
        hrds = {CSP_HEADER_W3C: header_value}.items()
        csp_headers = Headers(hrds)
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        policies = retrieve_csp_policies(http_response)
        
        self.assertEqual(len(policies), 2)
        self.assertEqual(len(policies[CSP_DIRECTIVE_SANDBOX]), 1)
        self.assertEqual(policies[CSP_DIRECTIVE_SANDBOX][0], "")
        self.assertEqual(len(policies[CSP_DIRECTIVE_SCRIPT_NONCE]), 1)        
        self.assertEqual(policies[CSP_DIRECTIVE_SCRIPT_NONCE][0], "")     
        
    def test_retrieve_csp_policies_with_special_policies_case02(self):
        """
        Test case in which 2 policies are specified using special directives
        with explicit values.
        """
        header_value = "sandbox allow-forms allow-scripts ;"\
                       " script-nonce AABBCCDDEE"
        hrds = {CSP_HEADER_W3C: header_value}.items()
        csp_headers = Headers(hrds)
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        policies = retrieve_csp_policies(http_response)
        
        self.assertEqual(len(policies), 2)
        self.assertEqual(len(policies[CSP_DIRECTIVE_SANDBOX]), 2)
        self.assertTrue("allow-forms" in policies[CSP_DIRECTIVE_SANDBOX])
        self.assertTrue("allow-scripts" in policies[CSP_DIRECTIVE_SANDBOX])
        self.assertEqual(len(policies[CSP_DIRECTIVE_SCRIPT_NONCE]), 1)        
        self.assertEqual(policies[CSP_DIRECTIVE_SCRIPT_NONCE][0], "AABBCCDDEE") 
        
    def test_find_vulns_case01(self):
        """
        Test case in which we set vulnerables policies using "*" as source  
        for all directives that allow this value.
        """ 
        header_value = "default-src '*';script-src '*';object-src '*';" \
                       "style-src '*';img-src '*';media-src '*';" \
                       "frame-src '*';font-src '*';" \
                       "form-action '*';connect-src '*';plugin-types '*';"
        hrds = {CSP_HEADER_W3C: header_value}.items()
        csp_headers = Headers(hrds)  
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        vulns = find_vulns(http_response)  
        
        self.assertEqual(len(vulns), 11)
        #>>>"default-src"
        self.assertEqual(len(vulns[CSP_DIRECTIVE_DEFAULT]), 1)
        self.assertTrue(self._vuln_exists("Directive 'default-src' allows all sources.",
                        vulns[CSP_DIRECTIVE_DEFAULT]))  
        #>>>"script-src"
        self.assertEqual(len(vulns[CSP_DIRECTIVE_SCRIPT]), 2)
        self.assertTrue(self._vuln_exists("Directive 'script-src' allows all javascript sources.",
                        vulns[CSP_DIRECTIVE_SCRIPT]))   
        warn_msg = "Directive 'script-src' is defined but no directive " \
        "'script-nonce' is defined to protect javascript resources."                                                                                              
        self.assertTrue(self._vuln_exists(warn_msg, vulns[CSP_DIRECTIVE_SCRIPT]))
        #>>>"object-src"
        self.assertEqual(len(vulns[CSP_DIRECTIVE_OBJECT]), 1)
        self.assertTrue(self._vuln_exists("Directive 'object-src' allows all plugin sources.",
                        vulns[CSP_DIRECTIVE_OBJECT]))
        #>>>"style-src"
        self.assertEqual(len(vulns[CSP_DIRECTIVE_STYLE]), 1)
        self.assertTrue(self._vuln_exists("Directive 'style-src' allows all CSS sources.",
                        vulns[CSP_DIRECTIVE_STYLE]))
        #>>>"img-src"
        self.assertEqual(len(vulns[CSP_DIRECTIVE_IMAGE]), 1)
        self.assertTrue(self._vuln_exists("Directive 'img-src' allows all image sources.",
                        vulns[CSP_DIRECTIVE_IMAGE]))
        #>>>"media-src"
        self.assertEqual(len(vulns[CSP_DIRECTIVE_MEDIA]), 1)
        self.assertTrue(self._vuln_exists("Directive 'media-src' allows all audio/video sources.",
                        vulns[CSP_DIRECTIVE_MEDIA]))
        #>>>"frame-src"
        self.assertEqual(len(vulns[CSP_DIRECTIVE_FRAME]), 2)
        self.assertTrue(self._vuln_exists("Directive 'frame-src' allows all sources.",
                        vulns[CSP_DIRECTIVE_FRAME]))
        warn_msg = "Directive 'frame-src' is defined but no directive " \
        "'sandbox' is defined to protect resources. Perhaps sandboxing " \
        "is defined at html attribute level ?"  
        self.assertTrue(self._vuln_exists(warn_msg, vulns[CSP_DIRECTIVE_FRAME]))              
        #>>>"font-src"
        self.assertEqual(len(vulns[CSP_DIRECTIVE_FONT]), 1)
        self.assertTrue(self._vuln_exists("Directive 'font-src' allows all font sources.",
                        vulns[CSP_DIRECTIVE_FONT]))
        #>>>"connect-src"
        self.assertEqual(len(vulns[CSP_DIRECTIVE_CONNECTION]), 1)
        self.assertTrue(self._vuln_exists("Directive 'connect-src' allows all connection sources.",
                        vulns[CSP_DIRECTIVE_CONNECTION]))                                                                                 
        #>>>"form-action"
        self.assertEqual(len(vulns[CSP_DIRECTIVE_FORM]), 1)
        self.assertTrue(self._vuln_exists("Directive 'form-action' allows all action target.",
                        vulns[CSP_DIRECTIVE_FORM]))
        #>>>"plugin-types"
        self.assertEqual(len(vulns[CSP_DIRECTIVE_PLUGIN_TYPES]), 1)
        self.assertTrue(self._vuln_exists("Directive 'plugin-types' allows all plugins types.",
                        vulns[CSP_DIRECTIVE_PLUGIN_TYPES]))                      

    def test_find_vulns_case02(self):
        """
        Test case in which we set vulnerables policies for "sandbox",
        "script-nonce","plugin-types","reflected-xss" directives 
        using invalid values.
        """ 
        header_value = "sandbox allow-invalid; script-nonce aaa,bbb;"\
        "plugin-types app/titi application/pdf; reflected-xss disallow;"
        hrds = {CSP_HEADER_W3C: header_value}.items()
        csp_headers = Headers(hrds)  
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        vulns = find_vulns(http_response)  
        
        self.assertEqual(len(vulns), 4)
        #>>>"sandbox"        
        self.assertEqual(len(vulns[CSP_DIRECTIVE_SANDBOX]), 1)
        warn_msg = "Directive 'sandbox' specify invalid value: 'allow-invalid'."
        self.assertTrue(self._vuln_exists(warn_msg, vulns[CSP_DIRECTIVE_SANDBOX]))
        #>>>"script-nonce"        
        self.assertEqual(len(vulns[CSP_DIRECTIVE_SCRIPT_NONCE]), 1)
        warn_msg = "Directive 'script-nonce' is defined "\
                   "but nonce contains invalid character (','|';')."
        self.assertTrue(self._vuln_exists(warn_msg, vulns[CSP_DIRECTIVE_SCRIPT_NONCE]))
        #>>>"reflected-xss"        
        self.assertEqual(len(vulns[CSP_DIRECTIVE_XSS]), 1)
        warn_msg = "Directive 'reflected-xss' specify invalid value: 'disallow'."
        self.assertTrue(self._vuln_exists(warn_msg, vulns[CSP_DIRECTIVE_XSS]))
        #>>>"plugins-types"
        self.assertEqual(len(vulns[CSP_DIRECTIVE_PLUGIN_TYPES]), 1)  
        warn_msg = "Directive 'plugin-types' specify invalid mime type: 'app/titi'."
        self.assertTrue(self._vuln_exists(warn_msg, vulns[CSP_DIRECTIVE_PLUGIN_TYPES]))                                                
        
        
    def test_find_vulns_case03(self):
        """
        Test case in which we set vulnerables policies for 
        "sandbox","reflected-xss" directives using valid values.
        """ 
        header_value = "sandbox allow-* allow-forms allow-same-origin " \
                       "allow-scripts allow-top-navigation;"\
                       "reflected-xss allow;"
        hrds = {CSP_HEADER_W3C: header_value}.items()
        csp_headers = Headers(hrds)  
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        vulns = find_vulns(http_response)  
        
        self.assertEqual(len(vulns), 2)
        #>>>"sandbox"        
        self.assertEqual(len(vulns[CSP_DIRECTIVE_SANDBOX]), 2)
        warn_msg = "Directive 'sandbox' apply no restrictions."
        self.assertTrue(vulns[CSP_DIRECTIVE_SANDBOX][0].desc, warn_msg)
        self.assertTrue(vulns[CSP_DIRECTIVE_SANDBOX][1].desc, warn_msg)    
        #>>>"reflected-xss"        
        self.assertEqual(len(vulns[CSP_DIRECTIVE_XSS]), 1)
        warn_msg = "Directive 'reflected-xss' instruct user agent to "\
                   "disable its active protections against reflected XSS."
        self.assertTrue(self._vuln_exists(warn_msg, vulns[CSP_DIRECTIVE_XSS]))  
        
    def test_find_vulns_case04(self):
        """
        Test case in which we configure correctly policies for all directives.
        """  
        header_value = "default-src 'self';script-src 'self';object-src 'self';" \
                       "style-src 'self';img-src 'self';media-src 'self';" \
                       "frame-src 'self';font-src 'self';sandbox;" \
                       "form-action '/myCtx/act';connect-src 'self';"\
                       "plugin-types application/pdf;reflected-xss filter;"\
                       "script-nonce AABBCCDDEE;"
        hrds = {CSP_HEADER_W3C: header_value}.items()
        csp_headers = Headers(hrds)  
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        vulns = find_vulns(http_response)  
        self.assertEqual(len(vulns), 0)     
        
    def test_find_vulns_case05(self):
        """
        Test case in which we misspell somes policies.
        """  
        header_value = "defauld-src 'self';script-src 'self';object-src 'self';" \
                       "style-src 'self';image-src 'self';media-src 'self';" \
                       "frame-src 'self';font-src 'self';sandbox;" \
                       "form-src '/myCtx/act';connect-src 'self';"\
                       "plugin-types application/pdf;reflected-xss filter;"\
                       "script-nonce AABBCCDDEE;"
        hrds = {CSP_HEADER_W3C: header_value}.items()
        csp_headers = Headers(hrds)  
        
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        vulns = find_vulns(http_response)  
        self.assertEqual(len(vulns), 1)  
        self.assertEqual(len(vulns[CSP_MISSPELLED_DIRECTIVES]), 1) 
        warn_msg = "Some directives are misspelled: "\
        "defauld-src, image-src, form-src"
        self.assertTrue(self._vuln_exists(warn_msg, vulns[CSP_MISSPELLED_DIRECTIVES]))
        
    def test_site_protected_against_xss_by_csp_case01(self):
        """
        Test case in witch site do not provide CSP features.
        """
        hrds = {}.items()
        csp_headers = Headers(hrds)          
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        site_protected = site_protected_against_xss_by_csp(http_response)
        self.assertFalse(site_protected)
              
    def test_site_protected_against_xss_by_csp_case02(self):
        """
        Test case in witch site provide CSP features and have a vuln 
        on Script policies.
        """
        header_value = "script-src *;"
        hrds = {CSP_HEADER_W3C: header_value}.items()
        csp_headers = Headers(hrds)          
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        site_protected = site_protected_against_xss_by_csp(http_response)
        self.assertFalse(site_protected)
        
    def test_site_protected_against_xss_by_csp_case03(self):
        """
        Test case in witch site provide CSP features and enable unsafe inline
        script into is CSP Script policies BUT we do not 
        accept theses configurations.
        """
        header_value = "script-src 'self' unsafe-inline; script-nonce 'AADD'"
        hrds = {CSP_HEADER_W3C: header_value}.items()
        csp_headers = Headers(hrds)          
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        site_protected = site_protected_against_xss_by_csp(http_response)
        self.assertFalse(site_protected) 
        
    def test_site_protected_against_xss_by_csp_case04(self):
        """
        Test case in witch site provide CSP features and enable use of the
        javascript "eval()" function into is CSP Script policies BUT we do not 
        accept theses configurations.
        """
        header_value = "script-src 'self' unsafe-eval; script-nonce 'AADD'"
        hrds = {CSP_HEADER_W3C: header_value}.items()
        csp_headers = Headers(hrds)          
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        site_protected = site_protected_against_xss_by_csp(http_response)
        self.assertFalse(site_protected)   
        
    def test_site_protected_against_xss_by_csp_case05(self):
        """
        Test case in witch site provide CSP features and enable unsafe inline
        script + use of the javascript "eval()" function into is CSP Script 
        policies BUT we accept theses configurations.
        """
        header_value = "script-src 'self' unsafe-eval unsafe-inline; "\
                       "script-nonce 'AADD'"
        hrds = {CSP_HEADER_W3C: header_value}.items()
        csp_headers = Headers(hrds)          
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        site_protected = site_protected_against_xss_by_csp(http_response,
                                                           True,
                                                           True)
        self.assertTrue(site_protected)                                        

    def test_site_protected_against_xss_by_csp_case06(self):
        """
        Test case in witch site is secure
        """
        header_value = "default-src 'self'"
        hrds = {CSP_HEADER_W3C: header_value}.items()
        csp_headers = Headers(hrds)          
        http_response = HTTPResponse(200, '', csp_headers, self.url, self.url)
        site_protected = site_protected_against_xss_by_csp(http_response)
        self.assertTrue(site_protected)
        
    def _vuln_exists(self, vuln_desc, vulns_list):
        """
        Internal method to check if a vuln is present into a vulns list
        coming from method "find_vulns()".
        
        :param vuln_desc: Vuln description.
        :param vulns_list: vulns list coming from method "find_vulns()".
        :return: True only if vuln is found. 
        """        
        for v in vulns_list:
            if v.desc == vuln_desc:
                return True
        
        return False
