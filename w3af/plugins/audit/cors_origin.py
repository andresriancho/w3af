"""
cors_origin.py

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
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
"""
import w3af.core.data.constants.severity as severity

from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.kb.info_set import InfoSet
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.cors.utils import (build_cors_request,
                                              provides_cors_features,
                                              retrieve_cors_header,
                                              ACCESS_CONTROL_ALLOW_ORIGIN,
                                              ACCESS_CONTROL_ALLOW_METHODS,
                                              ACCESS_CONTROL_ALLOW_CREDENTIALS)

ACAO = ACCESS_CONTROL_ALLOW_ORIGIN
ACAM = ACCESS_CONTROL_ALLOW_METHODS
ACAC = ACCESS_CONTROL_ALLOW_CREDENTIALS
METHODS = 'methods'
DOMAIN = 'domain'


class cors_origin(AuditPlugin):
    """
    Inspect if application checks that the value of the "Origin" HTTP header is
    consistent with the value of the remote IP address/Host of the sender of
    the incoming HTTP request.

    :author: Dominique RIGHETTO (dominique.righetto@owasp.org)
    """
    SENSITIVE_METHODS = ('PUT', 'DELETE')
    COMMON_METHODS = ('POST', 'GET', 'OPTIONS', 'PUT', 'DELETE')

    def __init__(self):
        AuditPlugin.__init__(self)

        # Define plugin options configuration variables
        self.origin_header_value = "http://w3af.org/"

        # Internal variables
        self._reported_global = set()

    def audit(self, freq, orig_response, debugging_id):
        """
        Plugin entry point.

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        # Detect if current url provides CORS features
        if not provides_cors_features(freq, self._uri_opener, debugging_id):
            return

        url = freq.get_url()
        self.analyze_cors_security(url, debugging_id)

    def analyze_cors_security(self, url, debugging_id):
        """
        Send forged HTTP requests in order to test target application behavior.

        :param debugging_id: A unique identifier for this call to audit()
        """
        origin_list = [self.origin_header_value, ]

        # TODO: Does it make any sense to add these Origins? If so, how will it
        #       affect our tests? And which vulnerabilities are we going to
        #       detect with them?
        #origin_list.append("http://www.google.com/")
        #origin_list.append("null")
        #origin_list.append("*")
        #origin_list.append("")
        #origin_list.append( url.url_string )

        # Perform check(s)
        for origin in origin_list:

            # Build request
            forged_req = build_cors_request(url, origin)

            # Send forged request and retrieve response information
            response = self._uri_opener.send_mutant(forged_req, debugging_id=debugging_id)

            allow_origin = retrieve_cors_header(response, ACAO)
            allow_credentials = retrieve_cors_header(response, ACAC)
            allow_methods = retrieve_cors_header(response, ACAM)

            self._analyze_server_response(forged_req, url, origin, response,
                                          allow_origin, allow_credentials,
                                          allow_methods)

    def _analyze_server_response(self, forged_req, url, origin, response,
                                 allow_origin, allow_credentials,
                                 allow_methods):
        """Analyze the server response and identify vulnerabilities which are'
        then saved to the KB.

        :return: A list of vulnerability objects with the identified vulns
                 (if any).
        """
        for analysis_method in [self._universal_allow, self._origin_echo,
                                self._universal_origin_allow_creds,
                                self._allow_methods]:

            analysis_method(forged_req, url, origin, response, allow_origin,
                            allow_credentials, allow_methods)

    def _allow_methods(self, forged_req, url, origin, response,
                       allow_origin, allow_credentials, allow_methods):
        """
        Report if we have sensitive methods enabled via CORS.

        :return: A list of vulnerability objects with the identified vulns
                 (if any).
        """
        if allow_methods is None:
            return

        # Access-Control-Allow-Methods: POST, GET, OPTIONS
        allow_methods_list = allow_methods.split(',')
        allow_methods_list = [m.strip() for m in allow_methods_list]
        allow_methods_list = [m.upper() for m in allow_methods_list]
        allow_methods_set = set(allow_methods_list)

        report_sensitive = set()

        for sensitive_method in self.SENSITIVE_METHODS:
            if sensitive_method in allow_methods_set:
                report_sensitive.add(sensitive_method)

        report_strange = set()

        for allowed_method in allow_methods_set:
            if allowed_method not in self.COMMON_METHODS:
                report_strange.add(allowed_method)

        if not (len(report_sensitive) or len(report_strange)):
            return

        if report_sensitive:
            name = 'Sensitive CORS methods enabled'

            msg = ('The remote Web application, specifically "%s", returned'
                   ' a "%s" header with the value set to "%s" which is'
                   ' insecure since it allows the following sensitive HTTP'
                   ' methods: %s.')
            msg %= (url, ACCESS_CONTROL_ALLOW_METHODS,
                    allow_methods, ', '.join(report_sensitive))

            v = Vuln(name, msg, severity.LOW, response.get_id(), self.get_name())
            v.set_url(forged_req.get_url())
            v[METHODS] = allow_methods_set

            self.kb_append_uniq_group(self, 'cors_origin', v,
                                      group_klass=SensitiveMethodsInfoSet)

        if report_strange:
            name = 'Uncommon CORS methods enabled'

            msg = ('The remote Web application, specifically "%s", returned'
                   ' a "%s" header with the value set to "%s" which is'
                   ' insecure since it allows the following uncommon HTTP'
                   ' methods: %s.')
            msg %= (url, ACCESS_CONTROL_ALLOW_METHODS,
                    allow_methods, ', '.join(report_strange))

            v = Vuln(name, msg, severity.LOW, response.get_id(), self.get_name())
            v.set_url(forged_req.get_url())
            v[METHODS] = allow_methods_set

            self.kb_append_uniq_group(self, 'cors_origin', v,
                                      group_klass=StrangeMethodsInfoSet)

    def _universal_allow(self, forged_req, url, origin, response,
                         allow_origin, allow_credentials, allow_methods):
        """
        Check if the allow_origin is set to *.

        :return: A list of vulnerability objects with the identified vulns
                 (if any).
        """
        if allow_origin == '*':
            msg = 'The remote Web application, specifically "%s", returned' \
                  ' an %s header with the value set to "*" which is insecure'\
                  ' and leaves the application open to Cross-domain attacks.'
            msg %= (forged_req.get_url(), ACCESS_CONTROL_ALLOW_ORIGIN)
            
            v = Vuln('Access-Control-Allow-Origin set to "*"', msg,
                     severity.LOW, response.get_id(), self.get_name())
            v.set_url(forged_req.get_url())
            v[DOMAIN] = forged_req.get_url().get_domain()

            self.kb_append_uniq_group(self, 'cors_origin', v,
                                      group_klass=UniversalAllowInfoSet)

    def _origin_echo(self, forged_req, url, origin, response,
                     allow_origin, allow_credentials_str, allow_methods):
        """
        First check if the @allow_origin is set to the value we sent
        (@origin) and if the allow_credentials is set to True. If this test
        is successful (most important vulnerability) then do not check for
        the @allow_origin is set to the value we sent.

        :return: A list of vulnerability objects with the identified vulns
                 (if any).
        """
        if allow_origin is None:
            return

        allow_origin = allow_origin.lower()

        allow_credentials = False
        if allow_credentials_str is not None:
            allow_credentials = 'true' in allow_credentials_str.lower()

        if origin not in allow_origin:
            return

        if allow_credentials:
            sev = severity.HIGH
            name = 'Insecure Access-Control-Allow-Origin with credentials'
            msg = ('The remote Web application, specifically "%s", returned'
                   ' a "%s" header with the value set to the value sent in the'
                   ' request\'s Origin header and a %s header with the value'
                   ' set to "true", which is insecure and leaves the'
                   ' application open to Cross-domain attacks which can'
                   ' affect logged-in users.')
            msg = msg % (forged_req.get_url(),
                         ACCESS_CONTROL_ALLOW_ORIGIN,
                         ACCESS_CONTROL_ALLOW_CREDENTIALS)

            v = Vuln(name, msg, sev, response.get_id(), self.get_name())
            v.set_url(forged_req.get_url())
            v[DOMAIN] = forged_req.get_url().get_domain()

            self.kb_append_uniq_group(self, 'cors_origin', v,
                                      group_klass=OriginEchoWithCredsInfoSet)

        else:
            sev = severity.LOW
            name = 'Insecure Access-Control-Allow-Origin'
            msg = ('The remote Web application, specifically "%s", returned'
                   ' a "%s" header with the value set to the value sent in the'
                   ' request\'s Origin header, which is insecure and leaves'
                   ' the application open to Cross-domain attacks.')
            msg = msg % (forged_req.get_url(),
                         ACCESS_CONTROL_ALLOW_ORIGIN)

            v = Vuln(name, msg, sev, response.get_id(), self.get_name())
            v.set_url(forged_req.get_url())
            v[DOMAIN] = forged_req.get_url().get_domain()

            self.kb_append_uniq_group(self, 'cors_origin', v,
                                      group_klass=OriginEchoInfoSet)

    def _universal_origin_allow_creds(self, forged_req, url, origin, response,
                                      allow_origin, allow_credentials_str,
                                      allow_methods):
        """
        Quote: "The above example would fail if the header was wildcarded as:
        Access-Control-Allow-Origin: *.  Since the Access-Control-Allow-Origin
        explicitly mentions http://foo.example, the credential-cognizant content
        is returned to the invoking web content.  Note that in line 23, a
        further cookie is set."

        https://developer.mozilla.org/en-US/docs/HTTP_access_control

        This method detects this bad implementation, which this is not a vuln
        it might be interesting for the developers and/or security admins.

        :return: Any implementation errors (as vuln objects) that might be found
        """
        allow_credentials = False
        if allow_credentials_str is not None:
            allow_credentials = 'true' in allow_credentials_str.lower()

        if allow_credentials and allow_origin == '*':

            msg = ('The remote Web application, specifically "%s", returned'
                   ' a "%s" header with the value set to "*"  and an %s header'
                   ' with the value set to "true" which according to Mozilla\'s'
                   ' documentation is invalid. This implementation error might'
                   ' affect the application behavior.')
            msg = msg % (forged_req.get_url(),
                         ACCESS_CONTROL_ALLOW_ORIGIN,
                         ACCESS_CONTROL_ALLOW_CREDENTIALS)
            
            v = Vuln('Incorrect withCredentials implementation', msg,
                     severity.INFORMATION, response.get_id(), self.get_name())
            v.set_url(forged_req.get_url())
            v[DOMAIN] = forged_req.get_url().get_domain()
            
            self.kb_append_uniq_group(self, 'cors_origin', v,
                                      group_klass=IncorrectWithCredsInfoSet)

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        opt_list = OptionList()

        desc = 'Origin HTTP header value'
        _help = ("Define value used to specify the 'Origin' HTTP header for"
                 " HTTP request sent to test application behavior")
        opt = opt_factory('origin_header_value', self.origin_header_value,
                          desc, 'string', help=_help)
        opt_list.add(opt)

        return opt_list

    def set_options(self, options_list):
        origin_header_value = options_list['origin_header_value']
        self.origin_header_value = origin_header_value.get_value()

        # Check set options
        if self.origin_header_value is None or \
        len(self.origin_header_value.strip()) == 0:
            msg = 'Please enter a valid value for the "Origin" HTTP header.'
            raise BaseFrameworkException(msg)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        Inspect if application check that the value of the "Origin" HTTP header
        is consistent with the value of the remote IP address/Host of the sender
        of the incoming HTTP request.

        Configurable parameters are:
            - origin_header_value

        Note: This plugin is useful to test "Cross Origin Resource Sharing"
              (CORS) application behaviors.
        CORS: http://developer.mozilla.org/en-US/docs/HTTP_access_control
              http://www.w3.org/TR/cors
        """


class SensitiveMethodsInfoSet(InfoSet):
    ITAG = METHODS
    TEMPLATE = (
        'The application sent the CORS response header'
        ' Access-Control-Allow-Methods with a value which enables these'
        ' HTTP methods: "{{ methods|join(\', \') }}". The enabled methods are'
        ' considered sensitive and should be reviewed. The first ten URLs which'
        ' sent the insecure header are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )


class StrangeMethodsInfoSet(InfoSet):
    ITAG = METHODS
    TEMPLATE = (
        'The application sent the CORS response header'
        ' Access-Control-Allow-Methods with a value which enables these'
        ' HTTP methods: "{{ methods|join(\', \') }}". The enabled methods are'
        ' considered uncommon and should be reviewed. The first ten URLs which'
        ' sent the insecure header are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )


class UniversalAllowInfoSet(InfoSet):
    ITAG = DOMAIN
    TEMPLATE = (
        'The application sent the CORS response header'
        ' Access-Control-Allow-Origin with the value set to "*" which is'
        ' considered insecure and leaves the application open to Cross-domain'
        ' attacks. The first ten URLs which sent the insecure header are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )


class OriginEchoInfoSet(InfoSet):
    ITAG = DOMAIN
    TEMPLATE = (
        'The application sent the CORS response header'
        ' Access-Control-Allow-Origin with it\'s value set to the domain sent'
        ' in the HTTP request\'s Origin header which is insecure and leaves'
        ' the application open to Cross-domain attacks that can affect'
        ' logged-in users. The first ten URLs which sent the insecure headers'
        ' are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )


class OriginEchoWithCredsInfoSet(InfoSet):
    ITAG = DOMAIN
    TEMPLATE = (
        'The application sent the CORS response header'
        ' Access-Control-Allow-Origin with it\'s value set to the domain sent'
        ' in the HTTP request\'s Origin header and an'
        ' Access-Control-Allow-Credentials header with the value set to "true",'
        ' which is insecure and leaves the application open to Cross-domain'
        ' attacks that can affect logged-in users. The first ten URLs which'
        ' sent the insecure headers are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )


class IncorrectWithCredsInfoSet(InfoSet):
    ITAG = DOMAIN
    TEMPLATE = (
        'The application sent the CORS response header'
        ' Access-Control-Allow-Origin with it\'s value set to "*" and an'
        ' Access-Control-Allow-Credentials header with the value set to "true",'
        ' which according to Mozilla\'s documentation is invalid. This'
        ' implementation error might affect the application behavior'
        ' The first ten URLs which sent the incorrect headers are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )
