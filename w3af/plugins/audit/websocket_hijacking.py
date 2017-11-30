"""
websocket_hijacking.py

Copyright 2015 Andres Riancho

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
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity

from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.kb.vuln import Vuln
from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.controllers.websocket.utils import (build_ws_upgrade_request,
                                                   negotiate_websocket_version,
                                                   is_successful_upgrade)


class websocket_hijacking(AuditPlugin):
    """
    Detect Cross-Site WebSocket hijacking vulnerabilities.
    :author: Dmitry Roshchin (nixwizard@gmail.com)
    """
    W3AF_DOMAIN = 'w3af.org'
    W3AF_ORIGIN = 'http://www.w3af.org/'

    def __init__(self):
        super(websocket_hijacking, self).__init__()
        self.already_tested_websockets = ScalableBloomFilter()

    def audit(self, freq, orig_response, debugging_id):
        """
        Detect websockets for Cross-Site WebSocket hijacking vulnerabilities.

        This plugin works really well and can be improved in two different ways:

            * Add new check_* methods to this class which detect websocket
              vulnerabilities and then add them to known_checks

            * Extend the websocket link detection in grep.websockets_links,
              which is the weak part of the process, this is because we're doing
              a very trivial regular expression match to find WS links, which
              will most likely fail in "complex" web applications

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        # We can only work if there are known web sockets
        ws_links = kb.kb.get('websockets_links', 'websockets_links')

        for web_socket_info_set in ws_links:
            web_socket_url = web_socket_info_set['ws_link']

            # Checking if we already tested this web socket URL
            if web_socket_url in self.already_tested_websockets:
                continue

            self.already_tested_websockets.add(web_socket_url)

            web_socket_url = URL(web_socket_url)
            web_socket_version = negotiate_websocket_version(self._uri_opener,
                                                             web_socket_url)
            self.check_websocket_security(web_socket_url,
                                          web_socket_version)

    def check_websocket_security(self, web_socket_url, web_socket_version):
        """
        Analyze the security of a web socket

        :param web_socket_url: The URL of the web socket
        :param web_socket_version: The protocol version
        :return: None, results (if any) are stored to the KB
        """
        known_checks = (self.check_is_open_web_socket,
                        self.check_is_restricted_by_origin_with_match_bug,
                        self.check_is_restricted_by_origin,
                        self.check_need_basic_auth_origin_not_restricted,
                        self.check_need_cookie_origin_not_restricted)

        for check in known_checks:
            if check(web_socket_url, web_socket_version):
                break

    def check_is_open_web_socket(self, web_socket_url, web_socket_version):
        """
        Note that this method only makes sense if called in a loop with the
        other check_* methods.

        :param web_socket_url: The URL of the web socket
        :param web_socket_version: The protocol version

        :return: True if the web socket is open:
                    * Any Origin can connect
                    * No cookies required for authentication
                    * No basic auth required for authentication
        """
        upgrade_request = build_ws_upgrade_request(web_socket_url,
                                                   web_socket_version=web_socket_version,
                                                   origin=self.W3AF_ORIGIN)
        upgrade_response = self._uri_opener.send_mutant(upgrade_request,
                                                        cookies=False,
                                                        use_basic_auth=False)

        if not is_successful_upgrade(upgrade_response):
            return False

        msg = ('An HTML5 WebSocket which allows connections from any origin'
               ' without authentication was found at "%s"')
        msg %= web_socket_url

        v = Vuln.from_fr('Open WebSocket', msg, severity.LOW,
                         upgrade_response.id, self.get_name(), upgrade_request)
        self.kb_append_uniq(self, 'websocket_hijacking', v)
        return True

    def check_is_restricted_by_origin_with_match_bug(self, web_socket_url,
                                                     web_socket_version):
        """
        Note that this method only makes sense if called in a loop with the
        other check_* methods.

        :param web_socket_url: The URL of the web socket
        :param web_socket_version: The protocol version

        :return: True if the web socket checks the origin for connections but
                 there is a bug in the matching process
        """
        #
        # Keep in mind that we get here only if the websocket is NOT an open
        # (accepts any origin) socket. So we're in a situation where the socket
        # is either verifying by Origin+Cookies, Origin+Basic Auth or just
        # Origin.
        #
        # We want to check for the "just Origin" now, with a twist, we're
        # checking if there is a mistake in the Origin domain match process
        #
        # This is the trick:
        origin_domain = web_socket_url.get_domain()
        origin_domain += '.%s' % self.W3AF_DOMAIN

        for scheme in {'http', 'https'}:
            origin = '%s://%s' % (scheme, origin_domain)
            upgrade_request = build_ws_upgrade_request(web_socket_url,
                                                       web_socket_version=web_socket_version,
                                                       origin=origin)
            upgrade_response = self._uri_opener.send_mutant(upgrade_request,
                                                            cookies=False,
                                                            use_basic_auth=False)

            if not is_successful_upgrade(upgrade_response):
                continue

            msg = ('An HTML5 WebSocket which restricts connections based on the'
                   ' Origin header was found to be vulnerable because of an'
                   ' incorrect matching algorithm. The "%s" Origin was allowed'
                   ' to connect to "%s".')
            msg %= (origin_domain, web_socket_url)

            v = Vuln.from_fr('Insecure WebSocket Origin filter', msg,
                             severity.MEDIUM, upgrade_response.id,
                             self.get_name(), upgrade_request)
            self.kb_append_uniq(self, 'websocket_hijacking', v)
            return True

        return False

    def check_is_restricted_by_origin(self, web_socket_url, web_socket_version):
        """
        Note that this method only makes sense if called in a loop with the
        other check_* methods.

        :param web_socket_url: The URL of the web socket
        :param web_socket_version: The protocol version

        :return: True if the web socket checks the origin for connections:
                    * Only the same origin can connect
                    * Send any cookie/basic auth known to the scanner
        """
        #
        # Keep in mind that we get here only if the websocket is NOT an open
        # (accepts any origin) socket. So we're in a situation where the socket
        # is either verifying by Origin+Cookies, Origin+Basic Auth or just
        # Origin.
        #
        # We want to check for the "just Origin" now
        #
        origin_domain = web_socket_url.get_domain()

        for scheme in {'http', 'https'}:
            origin = '%s://%s' % (scheme, origin_domain)
            upgrade_request = build_ws_upgrade_request(web_socket_url,
                                                       web_socket_version=web_socket_version,
                                                       origin=origin)
            upgrade_response = self._uri_opener.send_mutant(upgrade_request,
                                                            cookies=False,
                                                            use_basic_auth=False)

            if not is_successful_upgrade(upgrade_response):
                continue

            msg = ('An HTML5 WebSocket which allows connections only when the'
                   ' origin is set to "%s" was found at "%s"')
            msg %= (origin_domain, web_socket_url)

            v = Vuln.from_fr('Origin restricted WebSocket', msg, severity.LOW,
                             upgrade_response.id, self.get_name(),
                             upgrade_request)
            self.kb_append_uniq(self, 'websocket_hijacking', v)
            return True

        return False

    def check_need_basic_auth_origin_not_restricted(self, web_socket_url,
                                                    web_socket_version):
        """
        Note that this method only makes sense if called in a loop with the
        other check_* methods.

        :param web_socket_url: The URL of the web socket
        :param web_socket_version: The protocol version

        :return: True if the web socket does NOT check the origin for
                 connections but DOES require basic authentication to connect
        """
        #
        # Keep in mind that we get here only if:
        #   * The websocket is NOT an open (accepts any origin) socket
        #   * The websocket is NOT verifying by Origin
        #
        # So we're in one of these cases:
        #   * The websocket authenticates by cookie
        #   * The websocket authenticates by basic auth
        #
        # We want to check for the "authenticates by basic auth"
        #
        upgrade_request = build_ws_upgrade_request(web_socket_url,
                                                   web_socket_version=web_socket_version,
                                                   origin=self.W3AF_ORIGIN)
        upgrade_response = self._uri_opener.send_mutant(upgrade_request,
                                                        cookies=False,
                                                        # Note the True here!
                                                        use_basic_auth=True)

        if not is_successful_upgrade(upgrade_response):
            return False

        msg = 'Cross-Site WebSocket Hijacking has been found at "%s"'
        msg %= web_socket_url

        v = Vuln.from_fr('Websockets CSRF vulnerability', msg,
                         severity.HIGH, upgrade_response.id,
                         self.get_name(), upgrade_request)
        self.kb_append_uniq(self, 'websocket_hijacking', v)
        return True

    def check_need_cookie_origin_not_restricted(self, web_socket_url,
                                                web_socket_version):
        """
        Note that this method only makes sense if called in a loop with the
        other check_* methods.

        :param web_socket_url: The URL of the web socket
        :param web_socket_version: The protocol version

        :return: True if the web socket does NOT check the origin for
                 connections but DOES require cookies to connect
        """
        #
        # Keep in mind that we get here only if:
        #   * The websocket is NOT an open (accepts any origin) socket
        #   * The websocket is NOT verifying by Origin
        #
        # So we're in one of these cases:
        #   * The websocket authenticates by cookie
        #   * The websocket authenticates by basic auth
        #
        # We want to check for the "authenticates by cookie"
        #
        upgrade_request = build_ws_upgrade_request(web_socket_url,
                                                   web_socket_version=web_socket_version,
                                                   origin=self.W3AF_ORIGIN)
        upgrade_response = self._uri_opener.send_mutant(upgrade_request,
                                                        # Note the True here!
                                                        cookies=True,
                                                        use_basic_auth=False)

        if not is_successful_upgrade(upgrade_response):
            return False

        msg = 'Cross-Site WebSocket Hijacking has been found at "%s"'
        msg %= web_socket_url

        v = Vuln.from_fr('Websockets CSRF vulnerability', msg,
                         severity.HIGH, upgrade_response.id,
                         self.get_name(), upgrade_request)
        self.kb_append_uniq(self, 'websocket_hijacking', v)
        return True

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin sends websockets upgrade HTTP requests to detect
        Cross-Site WebSocket hijacking vulnerabilities using the "Origin"
        check detection method.

        https://www.christian-schneider.net/CrossSiteWebSocketHijacking.html
        """
