"""
ssl_certificate.py

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
import socket
import ssl
import re
import os

from time import gmtime
from datetime import date
from pprint import pformat

import w3af.core.controllers.output_manager as om
import w3af.core.data.constants.severity as severity

from w3af import ROOT_PATH
from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import INPUT_FILE
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.kb.info import Info
from w3af.core.data.kb.vuln import Vuln


class ssl_certificate(AuditPlugin):
    """
    Check the SSL certificate validity (if https is being used).

    :author: Andres Riancho (andres.riancho@gmail.com)
    :author: Taras ( oxdef@oxdef.info )
    """

    def __init__(self):
        AuditPlugin.__init__(self)

        self._already_tested = set()
        self._min_expire_days = 30
        self._ca_file = os.path.join(ROOT_PATH, 'plugins', 'audit',
                                     'ssl_certificate', 'ca.pem')

    def audit(self, freq, orig_response):
        """
        Get the cert and do some checks against it.

        :param freq: A FuzzableRequest
        """
        url = freq.get_url()
        domain = url.get_domain()

        if 'http' == url.get_protocol().lower():
            return
        
        with self._plugin_lock:

            if not domain in self._already_tested:
                self._already_tested.add(domain)
                
                self._analyze_ssl_cert(url, domain)

    def _analyze_ssl_cert(self, url, domain):
        """
        Analyze the SSL cert and store the information in the KB.
        """
        self._is_ssl_v2(url, domain)
        self._is_trusted_cert(url, domain)
        self._cert_expiration_analysis(url, domain)
        self._ssl_info_to_kb(url, domain)
        
    def _is_ssl_v2(self, url, domain):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # SSLv2 check
        # NB! From OpenSSL lib ver >= 1.0 there is no support for SSLv2
        try:
            # pylint: disable=E1101
            ssl_sock = ssl.wrap_socket(s,
                                       cert_reqs=ssl.CERT_NONE,
                                       ssl_version=ssl.PROTOCOL_SSLv2)
            ssl_sock.connect((domain, url.get_port()))
            # pylint: enable=E1101
        except Exception, e:
            pass
        else:
            desc = 'The target host "%s" has SSL version 2 enabled which is'\
                   ' known to be insecure.'
            desc = desc % domain
            
            v = Vuln('Insecure SSL version', desc,
                     severity.LOW, 1, self.get_name())

            v.set_url(url)

            self.kb_append(self, 'ssl_v2', v)

    def _is_trusted_cert(self, url, domain):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            ssl_sock = ssl.wrap_socket(s,
                                       ca_certs=self._ca_file,
                                       cert_reqs=ssl.CERT_REQUIRED,
                                       ssl_version=ssl.PROTOCOL_SSLv23)
            ssl_sock.connect((domain, url.get_port()))
            match_hostname(ssl_sock.getpeercert(), domain)
        except (ssl.SSLError, CertificateError), e:
            invalid_cert = isinstance(e, CertificateError)
            details = str(e)

            if isinstance(e, ssl.SSLError):
                err_chunks = details.split(':')
                if len(err_chunks) == 7:
                    details = err_chunks[5] + ':' + err_chunks[6]
                if 'CERTIFICATE' in details:
                    invalid_cert = True

            if invalid_cert:
                desc = ('"%s" uses an invalid security certificate.'
                        ' The certificate is not trusted because: "%s".')
                desc %= (domain, details)
                
                v = Vuln('Self-signed SSL certificate', desc,
                         severity.LOW, 1, self.get_name())

                tag = 'invalid_ssl_cert'
            else:
                # We use here Info instead of Vuln because it is too common case
                desc = ('"%s" has an invalid SSL configuration.'
                        ' Technical details: "%s"')
                desc %= (domain, details)
                
                v = Info('Invalid SSL connection', desc, 1, self.get_name())

                tag = 'invalid_ssl_connect'

            v.set_url(url)
            
            self.kb_append(self, tag, v)

        except Exception, e:
            om.out.debug(str(e))

    def _get_cert(self, url, domain):
        """
        Get the certificate information for this domain:port

        :param url: The URL we want to query (we get the port from here)
        :param domain: The domain to connect to
        :return: A tuple with:
                    * cert
                    * cert_der
                    * cipher
        """
        for extract_method in (self._get_ca_signed_cert,
                               self._self_signed_cert):
            try:
                return extract_method(url, domain)
            except RuntimeError, rte:
                om.out.debug(str(rte))

        # If all fails raise rte
        raise rte

    def _self_signed_cert(self, url, domain):
        """
        Helper method to get a certificate when it is self signed

        :param url: The URL we want to query (we get the port from here)
        :param domain: The domain to connect to
        :return: A tuple with:
                    * cert
                    * cert_der
                    * cipher
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            ssl_sock = ssl.wrap_socket(s, ssl_version=ssl.PROTOCOL_SSLv23)
            ssl_sock.connect((domain, url.get_port()))
        except Exception:
            msg = 'Failed to connect to %s with PROTOCOL_SSLv23.'
            raise RuntimeError(msg % domain)
        else:
            return self._extract_cert_data(ssl_sock)

    def _get_ca_signed_cert(self, url, domain):
        """
        Helper method to get a certificate when it is properly signed.

        :param url: The URL we want to query (we get the port from here)
        :param domain: The domain to connect to
        :return: A tuple with:
                    * cert
                    * cert_der
                    * cipher
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # When we use CERT_REQUIRED certificate is required and *validated*
            ssl_sock = ssl.wrap_socket(s, ca_certs=self._ca_file,
                                       cert_reqs=ssl.CERT_REQUIRED,
                                       ssl_version=ssl.PROTOCOL_SSLv23)
            ssl_sock.connect((domain, url.get_port()))
        except Exception:
            msg = 'Failed to connect to %s with CERT_REQUIRED.'
            raise RuntimeError(msg % domain)
        else:
            return self._extract_cert_data(ssl_sock)

    def _extract_cert_data(self, ssl_sock):
        """
        Extract the cert, cert_der and cipher from a ssl socket connection.

        :param ssl_sock: The SSL socket connection
        :return: A tuple with:
                    * cert
                    * cert_der
                    * cipher
        """
        cert = ssl_sock.getpeercert()
        cert_der = ssl_sock.getpeercert(binary_form=True)
        cipher = ssl_sock.cipher()

        ssl_sock.close()

        return cert, cert_der, cipher

    def _cert_expiration_analysis(self, url, domain):
        try:
            cert, cert_der, cipher = self._get_cert(url, domain)
        except RuntimeError, rte:
            msg = 'Failed to analyze certificate expiration due to an error in'\
                  ' the get_cert method: "%s".'
            om.out.debug(msg % rte)
            return

        try:
            exp_date = gmtime(ssl.cert_time_to_seconds(cert['notAfter']))
        except ValueError:
            msg = 'Invalid SSL certificate date format.'
            om.out.debug(msg)
            return
        except KeyError:
            msg = 'SSL certificate does not have notAfter field.'
            om.out.debug(msg)
            return

        expire_days = (date(exp_date.tm_year, exp_date.tm_mon,
                       exp_date.tm_mday) - date.today()).days

        if expire_days < self._min_expire_days:
            desc = 'The certificate for "%s" will expire soon.' % domain

            i = Info('Soon to expire SSL certificate', desc, 1, self.get_name())
            i.set_url(url)

            self.kb_append(self, 'ssl_soon_expire', i)

    def _ssl_info_to_kb(self, url, domain):
        try:
            cert, cert_der, cipher = self._get_cert(url, domain)
        except RuntimeError, rte:
            msg = 'Failed to store SSL information to KB due to an error in'\
                  ' the get_cert method: "%s".'
            om.out.debug(msg % rte)
            return
        
        # Print the SSL information to the log
        desc = 'This is the information about the SSL certificate used for'\
               ' %s site:\n%s' % (domain,
                                  self._dump_ssl_info(cert, cert_der, cipher))
        om.out.information(desc)
        i = Info('SSL Certificate dump', desc, 1, self.get_name())
        i.set_url(url)
        
        self.kb_append(self, 'certificate', i)

    def _dump_ssl_info(self, cert, cert_der, cipher):
        """
        Dump X509 certificate.
        """
        res = '\n== Certificate information ==\n'
        res += pformat(cert)
        res += '\n\n== Used cipher ==\n' + pformat(cipher)
        res += '\n\n== Certificate dump ==\n' + \
            ssl.DER_cert_to_PEM_cert(cert_der)
        # Indent
        res = res.replace('\n', '\n    ')
        res = '    ' + res
        return res

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Set minimal amount of days before expiration of the certificate'\
            ' for alerting'
        h = 'If the certificate will expire in period of minExpireDays w3af'\
            ' will show an alert about it, which is useful for admins to'\
            ' remember to renew the certificate.'
        o = opt_factory('minExpireDays', self._min_expire_days, d, 'integer',
                        help=h)
        ol.add(o)

        d = 'CA PEM file path'
        o = opt_factory('caFileName', self._ca_file, d, INPUT_FILE)
        ol.add(o)

        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param OptionList: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._min_expire_days = options_list['minExpireDays'].get_value()
        self._ca_file = options_list['caFileName'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin audits SSL certificate parameters.

        One configurable parameter exists:
            - minExpireDays
            - CA PEM file path

        Note: It's only useful when testing HTTPS sites.
        """

#
# This code taken from
# http://pypi.python.org/pypi/backports.ssl_match_hostname/
#


class CertificateError(Exception):
    pass


def _dnsname_to_pat(dn, max_wildcards=2):
    pats = []
    for frag in dn.split(r'.'):
        if frag.count('*') > max_wildcards:
            raise CertificateError("too many wildcards in certificate name: "
                                   + repr(dn))
        if frag == '*':
            # When '*' is a fragment by itself, it matches a non-empty dotless
            # fragment.
            pats.append('[^.]+')
        else:
            # Otherwise, '*' matches any dotless fragment.
            frag = re.escape(frag)
            pats.append(frag.replace(r'\*', '[^.]*'))
    return re.compile(r'\A' + r'\.'.join(pats) + r'\Z', re.IGNORECASE)


def match_hostname(cert, hostname):
    """Verify that *cert* (in decoded format as returned by
    SSLSocket.getpeercert()) matches the *hostname*.  RFC 2818 rules
    are mostly followed, but IP addresses are not accepted for *hostname*.

    CertificateError is raised on failure. On success, the function
    returns nothing.
    """
    if not cert:
        raise ValueError("empty or no certificate")
    
    dnsnames = []
    san = cert.get('subjectAltName', ())
    
    for key, value in san:
        if key == 'DNS':
            if _dnsname_to_pat(value).match(hostname):
                return
            dnsnames.append(value)
    
    if not dnsnames:
        # The subject is only checked when there is no dNSName entry
        # in subjectAltName
        for sub in cert.get('subject', ()):
            for key, value in sub:
                # XXX according to RFC 2818, the most specific Common Name
                # must be used.
                if key == 'commonName':
                    if _dnsname_to_pat(value).match(hostname):
                        return
                    dnsnames.append(value)
    
    if len(dnsnames) > 1:
        raise CertificateError("hostname %s "
                               "doesn't match either of %s"
                               % (hostname, ', '.join(map(str, dnsnames))))
    
    elif len(dnsnames) == 1:
        raise CertificateError("hostname %s "
                               "doesn't match %s"
                               % (hostname, dnsnames[0]))
    else:
        raise CertificateError("no appropriate commonName or "
                               "subjectAltName fields were found")
