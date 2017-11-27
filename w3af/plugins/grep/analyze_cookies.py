"""
analyze_cookies.py

Copyright 2006 Andres Riancho

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
import Cookie
import re

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity
from w3af.core.data.kb.info import Info
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.kb.info_set import InfoSet
from w3af.core.data.parsers.doc.cookie_parser import parse_cookie, COOKIE_HEADERS
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.constants.cookies import COOKIE_FINGERPRINT
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin


COOKIE_KEYS = 'cookie_keys'
COOKIE_OBJECT = 'cookie_object'
COOKIE_STRING = 'cookie_string'


class analyze_cookies(GrepPlugin):
    """
    Grep every response for session cookies sent by the web application.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    SECURE_RE = re.compile('; *?secure([\s;, ]|$)', re.I)
    HTTPONLY_RE = re.compile('; *?httponly([\s;, ]|$)', re.I)

    def __init__(self):
        GrepPlugin.__init__(self)

        self._cookie_key_failed_fingerprint = set()
        self._already_reported_fingerprint = set()
        self._already_reported_cookies = ScalableBloomFilter()

    def grep(self, request, response):
        """
        Plugin entry point, search for cookies.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        # do this check every time
        self._ssl_cookie_via_http(request, response)

        #
        # Analyze the response headers and find cookies
        #
        headers = response.get_headers()

        for header_name in headers:
            if header_name.lower() not in COOKIE_HEADERS:
                continue

            cookie_header_value = headers[header_name].strip()
            cookie_object = self._parse_cookie(request, response,
                                               cookie_header_value)

            if cookie_object is None:
                continue

            self._collect_cookies(request,
                                  response,
                                  cookie_object,
                                  cookie_header_value)

            # Find if the cookie introduces any vulnerability,
            # or discloses information
            self._analyze_cookie_security(request,
                                          response,
                                          cookie_object,
                                          cookie_header_value)

    def _collect_cookies(self, request, response, cookie_object,
                         cookie_header_value):
        """
        Store (unique) cookies in the KB for later analysis.
        """
        # Cookie class has an __eq__ which compares Cookies' keys for
        # equality, not the values, so these two cookies are equal:
        #        a=1;
        #        a=2;
        # And these two are not:
        #        a=1;
        #        b=1;
        cookie_keys = tuple(cookie_object.keys())
        uniq_id = (cookie_keys, response.get_url())
        if uniq_id in self._already_reported_cookies:
            return

        # No duplicates
        self._already_reported_cookies.add(uniq_id)

        # Create the info and store it in the KB
        cstr = cookie_object.output(header='').strip()
        desc = 'The URL: "%s" sent the cookie: "%s".'
        desc = desc % (response.get_url(), cstr)

        i = CookieInfo('Cookie', desc, response.id, self.get_name())
        i.set_url(response.get_url())
        i.set_cookie_object(cookie_object)

        """
        The expiration date tells the browser when to delete the
        cookie. If no expiration date is provided, the cookie is
        deleted at the end of the user session, that is, when the
        user quits the browser. As a result, specifying an expiration
        date is a means for making cookies to survive across
        browser sessions. For this reason, cookies that have an
        expiration date are called persistent.
        """
        i['persistent'] = 'expires' in cookie_object

        self.kb_append_uniq_group(self, 'cookies', i,
                                  group_klass=CollectedCookieInfoSet)

    def _parse_cookie(self, request, response, cookie_header_value):
        """
        If the response sets more than one Cookie, this method will
        be called once for each "Set-Cookie" header.

        BUGBUG: The urllib2 library concatenates , values of repeated headers.
                See HTTPMessage.addheader() in httplib.py

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :param cookie_header_value: The cookie, as sent in the HTTP response

        :return: The cookie object or None if the parsing failed
        """
        try:
            # Note to self: This line may print some chars to the console
            return parse_cookie(cookie_header_value)
        except Cookie.CookieError:
            desc = 'The remote Web application sent a cookie with an' \
                   ' incorrect format: "%s" that does NOT respect the RFC.'
            desc = desc % cookie_header_value

            i = CookieInfo('Invalid cookie', desc, response.id, self.get_name())
            i.set_url(response.get_url())
            i.set_cookie_string(cookie_header_value)

            # The cookie is invalid, this is worth mentioning ;)
            kb.kb.append(self, 'invalid-cookies', i)
            return None

    def _analyze_cookie_security(self, request, response, cookie_obj,
                                 cookie_header_value):
        """
        In this method I call all the other methods that perform a specific
        analysis of the already caught cookie.
        """
        self._secure_over_http(request, response, cookie_obj,
                               cookie_header_value)
        self._not_secure_over_https(request, response, cookie_obj,
                                    cookie_header_value)

        fingerprinted = self._match_cookie_fingerprint(request, response,
                                                       cookie_obj)
        self._http_only(request, response, cookie_obj,
                        cookie_header_value, fingerprinted)

    def _http_only(self, request, response, cookie_obj,
                   cookie_header_value, fingerprinted):
        """
        Verify if the cookie has the httpOnly parameter set

        Reference:
            http://www.owasp.org/index.php/HTTPOnly
            http://en.wikipedia.org/wiki/HTTP_cookie

        :param request: The http request object
        :param response: The http response object
        :param cookie_obj: The cookie object to analyze
        :param cookie_header_value: The cookie, as sent in the HTTP response
        :param fingerprinted: True if the cookie was fingerprinted
        :return: None
        """
        if not self.HTTPONLY_RE.search(cookie_header_value):

            vuln_severity = severity.MEDIUM if fingerprinted else severity.LOW
            desc = 'A cookie without the HttpOnly flag was sent when ' \
                   ' requesting "%s". The HttpOnly flag prevents potential' \
                   ' intruders from accessing the cookie value through' \
                   ' Cross-Site Scripting attacks.'
            desc = desc % response.get_url()

            v = CookieVuln('Cookie without HttpOnly', desc, vuln_severity,
                           response.id, self.get_name())
            v.set_url(response.get_url())
            v.set_cookie_object(cookie_obj)

            self.kb_append_uniq_group(self, 'http_only', v,
                                      group_klass=HttpOnlyCookieInfoSet)

    def _ssl_cookie_via_http(self, request, response):
        """
        Analyze if a cookie value, sent in a HTTPS request, is now used for
        identifying the user in an insecure page. Example:
            Login is done over SSL
            The rest of the page is HTTP
        """
        if request.get_url().get_protocol().lower() == 'https':
            return

        # Pre-calculate to avoid CPU usage
        request_dump = request.dump()

        for info_set in kb.kb.get(self, 'cookies'):
            for info in info_set.infos:
                if info.get_url().get_protocol().lower() != 'https':
                    continue

                if request.get_url().get_domain() != info.get_url().get_domain():
                    continue

                # The cookie was sent using SSL, I'll check if the current
                # request, is using these values in the POSTDATA / QS / COOKIE
                for cookie_key in info[COOKIE_KEYS]:

                    cookie_value = info.get_cookie_object()[cookie_key].value

                    # This if is to create less false positives
                    if len(cookie_value) > 6 and cookie_value in request_dump:

                        desc = ('The cookie "%s" with value "%s" which was'
                                ' set over HTTPS, was then sent over an'
                                ' insecure channel in a request to "%s".')
                        desc %= (cookie_key, cookie_value, request.get_url())

                        v = CookieVuln('Secure cookies over insecure channel',
                                       desc, severity.HIGH, response.id,
                                       self.get_name())
                        v.set_url(response.get_url())
                        v.set_cookie_object(info.get_cookie_object())

                        kb.kb.append(self, 'secure_via_http', v)

    def _match_cookie_fingerprint(self, request, response, cookie_obj):
        """
        Now we analyze the cookie and try to guess the remote web server or
        programming framework based on the cookie that was sent.

        :return: True if the cookie was fingerprinted
        """
        cookie_keys = cookie_obj.keys()
        for cookie_key in cookie_keys:
            if cookie_key in self._cookie_key_failed_fingerprint:
                cookie_keys.remove(cookie_key)
                continue

            if cookie_key in self._already_reported_fingerprint:
                cookie_keys.remove(cookie_key)

        for cookie_key in cookie_keys:
            for cookie_str_db, system_name in COOKIE_FINGERPRINT:
                if cookie_str_db not in cookie_key:
                    continue

                if cookie_key in self._already_reported_fingerprint:
                    continue

                # Unreported match!
                self._already_reported_fingerprint.add(cookie_key)

                desc = 'A cookie matching the cookie fingerprint DB'\
                       ' has been found when requesting "%s".'\
                       ' The remote platform is: "%s".'
                desc = desc % (response.get_url(), system_name)

                i = CookieInfo('Identified cookie', desc, response.id,
                               self.get_name())
                i.set_cookie_object(cookie_obj)
                i.set_url(response.get_url())
                i['httpd'] = system_name

                kb.kb.append(self, 'fingerprint', i)
                return True
        else:
            # No match was found, we store the keys so we don't try to match
            # them again against the COOKIE_FINGERPRINT
            for cookie_key in cookie_keys:
                self._cookie_key_failed_fingerprint.add(cookie_key)

        return False

    def _secure_over_http(self, request, response, cookie_obj,
                          cookie_header_value):
        """
        Checks if a cookie marked as secure is sent over http.

        Reference:
            http://en.wikipedia.org/wiki/HTTP_cookie

        :param request: The http request object
        :param response: The http response object
        :param cookie_obj: The cookie object to analyze
        :param cookie_header_value: The cookie, as sent in the HTTP response
        :return: None
        """
        if self.SECURE_RE.search(cookie_header_value) and \
        response.get_url().get_protocol().lower() == 'http':

            desc = 'A cookie marked with the secure flag was sent over' \
                   ' an insecure channel (HTTP) when requesting the URL:'\
                   ' "%s", this usually means that the Web application was'\
                   ' designed to run over SSL and was deployed without'\
                   ' security or that the developer does not understand the'\
                   ' "secure" flag.'
            desc = desc % response.get_url()

            v = CookieVuln('Secure cookie over HTTP', desc, severity.HIGH,
                           response.id, self.get_name())
            v.set_url(response.get_url())
            v.set_cookie_object(cookie_obj)

            kb.kb.append(self, 'false_secure', v)

    def _not_secure_over_https(self, request, response, cookie_obj,
                               cookie_header_value):
        """
        Checks if a cookie that does NOT have a secure flag is sent over https.

        :param request: The http request object
        :param response: The http response object
        :param cookie_obj: The cookie object to analyze
        :param cookie_header_value: The cookie, as sent in the HTTP response
        :return: None
        """
        if response.get_url().get_protocol().lower() == 'https' and \
        not self.SECURE_RE.search(cookie_header_value):
            desc = 'A cookie without the secure flag was sent in an HTTPS' \
                   ' response at "%s". The secure flag prevents the browser' \
                   ' from sending a "secure" cookie over an insecure HTTP' \
                   ' channel, thus preventing potential session hijacking' \
                   ' attacks.'
            desc = desc % response.get_url()

            v = CookieVuln('Secure flag missing in HTTPS cookie', desc,
                           severity.MEDIUM, response.id, self.get_name())
            v.set_url(response.get_url())
            v.set_cookie_object(cookie_obj)

            self.kb_append_uniq_group(self, 'secure', v,
                                      group_klass=NotSecureFlagCookieInfoSet)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every response for session cookies that the web
        application sends to the client, and analyzes them in order to identify
        potential vulnerabilities, the remote web application framework and
        other interesting information.
        """


class CookieMixIn(object):
    def set_cookie_keys(self, keys):
        self[COOKIE_KEYS] = keys

    def set_cookie_string(self, cookie_string):
        self[COOKIE_STRING] = cookie_string
        self.add_to_highlight(cookie_string)

    def set_cookie_object(self, cookie_object):
        self[COOKIE_OBJECT] = cookie_object
        self.set_cookie_string(cookie_object.output(header='').strip())
        self.set_cookie_keys(cookie_object.keys())

    def get_cookie_object(self):
        return self[COOKIE_OBJECT]
    

class CookieInfo(Info, CookieMixIn):
    pass


class CookieVuln(Vuln, CookieMixIn):
    pass


class CollectedCookieInfoSet(InfoSet):
    ITAG = COOKIE_KEYS
    TEMPLATE = (
        'The application sent the "{{ cookie_keys|join(\', \') }}" cookie in'
        ' {{ uris|length }} different URLs. The first ten URLs are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )


class HttpOnlyCookieInfoSet(InfoSet):
    ITAG = COOKIE_KEYS
    TEMPLATE = (
        'The application sent the "{{ cookie_keys|join(\', \') }}" cookie'
        ' without the HttpOnly flag in {{ uris|length }} different responses.'
        ' The HttpOnly flag prevents potential intruders from accessing the'
        ' cookie value through Cross-Site Scripting attacks. The first ten'
        ' URLs which sent the insecure cookie are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )


class NotSecureFlagCookieInfoSet(InfoSet):
    ITAG = COOKIE_KEYS
    TEMPLATE = (
        'The application sent the "{{ cookie_keys|join(\', \') }}" cookie'
        ' without the Secure flag set in {{ uris|length }} different URLs.'
        ' The Secure flag prevents the browser from sending cookies over'
        ' insecure HTTP connections, thus preventing potential session'
        ' hijacking attacks. The first ten URLs which sent the insecure'
        ' cookie are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )
