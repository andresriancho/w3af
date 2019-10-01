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
import re
import os
import ssl
import socket
import OpenSSL

from pprint import pformat
from datetime import date, datetime

import w3af.core.controllers.output_manager as om
import w3af.core.data.constants.severity as severity

from w3af import ROOT_PATH
from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import INPUT_FILE
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.url.openssl.ssl_wrapper import wrap_socket
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

        """
        It is possible to update this file by downloading the latest
        cacert.pem from curl:
        
            wget https://curl.haxx.se/ca/cacert.pem -O w3af/plugins/audit/ssl_certificate/ca.pem
            git commit w3af/plugins/audit/ssl_certificate/ca.pem -m "Update ca.pem"
        
        """
        self._ca_file = os.path.join(ROOT_PATH, 'plugins', 'audit',
                                     'ssl_certificate', 'ca.pem')

    def audit(self, freq, orig_response, debugging_id):
        """
        Get the cert and do some checks against it.

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        url = freq.get_url()
        port = url.get_port()

        # openssl requires the domain to be a string, and does not perform any
        # automatic type casting from unicode
        domain = str(url.get_domain())

        if url.get_protocol().lower() == 'http':
            return
        
        with self._plugin_lock:

            if domain in self._already_tested:
                return

            self._already_tested.add(domain)

            # Now perform the security analysis
            self._allows_ssl_v2(domain, port)
            self._analyze_ssl_cert(domain, port)

    def _analyze_ssl_cert(self, domain, port):
        """
        Analyze the SSL cert and store the information in the KB.
        """
        self._is_trusted_cert(domain, port)

        try:
            cert, cert_der, cipher = self._get_ssl_cert(domain, port)
        except Exception, e:
            om.out.debug('Failed to retrieve SSL certificate: "%s"' % e)
        else:
            self._cert_expiration_analysis(domain, port, cert, cert_der, cipher)
            self._ssl_info_to_kb(domain, port, cert, cert_der, cipher)
        
    def _allows_ssl_v2(self, domain, port):
        """
        Check if the server allows SSLv2 connections

        :param domain: the domain to connect to
        :return: None, save any new vulnerabilities to the KB
        """
        # From OpenSSL lib ver >= 1.0 there is no support for SSLv2, so maybe
        # we want to start a connection using that protocol and it fails from
        # our side
        if getattr(ssl, 'PROTOCOL_SSLv2', None) is None:
            om.out.debug('There is no SSLv2 protocol support in the client.'
                         ' Will not be able to verify if the remote end has'
                         ' SSLv2 support.')
            return

        def on_success(domain, port, ssl_sock, result):
            desc = ('The target host "%s" has SSL version 2 enabled which is'
                    ' known to be insecure.')
            desc %= domain

            v = Vuln('Insecure SSL version',
                     desc,
                     severity.LOW,
                     1,
                     self.get_name())
            v.set_url(self._url_from_parts(domain, port))

            self.kb_append(self, 'ssl_v2', v)

        self._ssl_connect_specific_protocol(domain,
                                            port,
                                            ssl_version=OpenSSL.SSL.SSLv2_METHOD,
                                            on_success=on_success)

    def _url_from_parts(self, domain, port):
        return URL('https://%s:%s/' % (domain, port))

    def _is_trusted_cert(self, domain, port):
        """
        Check if the server uses a trusted certificate

        :param domain: the domain to connect to
        :param port: the port to connect to
        :return: None, save any new vulnerabilities to the KB
        """
        def on_success(_domain, _port, ssl_sock, result):
            """
            OpenSSL's certificate validation was successful, but we still need
            to call match_hostname()
            """
            try:
                peer_cert = ssl_sock.getpeercert()
            except ssl.SSLError, ssl_error:
                om.out.debug('Failed to retrieve the peer certificate: "%s"' % ssl_error)
                return

            if not peer_cert:
                om.out.debug('The peer cert is empty: %r' % peer_cert)
                return

            try:
                match_hostname(peer_cert, _domain)
            except CertificateError, cve:
                self._handle_certificate_validation_error(cve, _domain, _port)

        self._ssl_connect(domain,
                          port,
                          cert_reqs=ssl.CERT_REQUIRED,
                          on_certificate_validation_error=self._handle_certificate_validation_error,
                          on_success=on_success)

    def _get_procotols(self):
        """
        Not all python versions support all SSL protocols.
        :return: The protocol constants that exist in this python version
        """
        return [OpenSSL.SSL.SSLv3_METHOD,
                OpenSSL.SSL.TLSv1_METHOD,
                OpenSSL.SSL.SSLv23_METHOD,
                OpenSSL.SSL.TLSv1_1_METHOD,
                OpenSSL.SSL.TLSv1_2_METHOD,
                OpenSSL.SSL.SSLv2_METHOD]

    def _ssl_connect(self,
                     domain,
                     port,
                     ca_certs=None,
                     cert_reqs=ssl.CERT_NONE,
                     on_certificate_validation_error=None,
                     on_success=None,
                     on_exception=None):
        """
        Connect to domain and port negotiating the SSL / TLS protocol

        :param domain: the domain to connect to
        :param port: the port to connect to
        :param on_certificate_validation_error: Handler for certificate validation errors
        :param on_success: Handler for successful connections
        :param on_exception: Handler for other exceptions
        :return: None if there was an error (handle those with on_*). A Result
                 instance as created by on_success() otherwise.
        """
        connect = self._ssl_connect_specific_protocol
        ca_certs = self._ca_file if ca_certs is None else ca_certs

        for protocol in self._get_procotols():
            om.out.debug('Trying to connect with SSL protocol %s' % protocol)
            
            try:
                result = connect(domain,
                                 port,
                                 ssl_version=protocol,
                                 ca_certs=ca_certs,
                                 cert_reqs=cert_reqs,
                                 on_certificate_validation_error=on_certificate_validation_error,
                                 on_success=on_success,
                                 on_exception=on_exception)
            except (OpenSSL.SSL.Error, ssl.SSLError):
                # The protocol failed, try the next one
                continue
            else:
                if result is not None:
                    return result

    def _ssl_connect_specific_protocol(self,
                                       domain,
                                       port,
                                       ssl_version=OpenSSL.SSL.SSLv23_METHOD,
                                       cert_reqs=ssl.CERT_NONE,
                                       ca_certs=None,
                                       on_certificate_validation_error=None,
                                       on_success=None,
                                       on_exception=None):
        """
        Connect to domain and port using a specific SSL / TLS protocol

        :param domain: the domain to connect to
        :param port: the port to connect to
        :param on_certificate_validation_error: Handler for certificate validation errors
        :param on_success: Handler for successful connections
        :param on_exception: Handler for other exceptions
        :return: An OpenSSL socket instance if the connection was successfully
                 created, if you need to use the ssl_sock do it in on_success
        """
        ca_certs = self._ca_file if ca_certs is None else ca_certs
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            s.connect((domain, port))
        except socket.error, se:
            msg = 'Failed to connect to %s:%s. Socket error: "%s"'
            args = (domain, port, se)
            om.out.debug(msg % args)
            return

        try:
            ssl_sock = wrap_socket(s,
                                   server_hostname=domain,
                                   ca_certs=ca_certs,
                                   cert_reqs=cert_reqs,
                                   ssl_version=ssl_version)
        except (OpenSSL.SSL.Error, ssl.SSLError) as ssl_error:
            # When a certificate validation error is found, call the
            # handler (if any) and return. The other errors, like connection
            # timeouts, SSL protocol handshake errors, etc. should raise
            # an exception
            if self._is_certificate_validation_error(ssl_error):
                if on_certificate_validation_error:
                    on_certificate_validation_error(ssl_error, domain, port)
                return Result()
            else:
                # Raise SSL errors
                raise

        except Exception, e:
            msg = 'Unhandled %s exception in _ssl_connect_specific_protocol(): "%s"'
            args = (e.__class__.__name__, e)
            om.out.debug(msg % args)

            if on_exception:
                on_exception(domain, port, e)
        else:
            result = Result()

            if on_success:
                on_success(domain, port, ssl_sock, result)

            try:
                ssl_sock.close()
            except Exception, e:
                om.out.debug('Exception found while closing SSL socket: "%s"' % e)

            return result

    def _is_certificate_validation_error(self, cve):
        details = self._get_ssl_error_details(cve)
        return 'certificate' in details

    def _get_ssl_error_details(self, cve):
        try:
            return cve.args[0][0][2]
        except:
            return str(cve)

    def _handle_certificate_validation_error(self, cve, domain, port):
        """
        When a certificate validation error occurs this method is called to
        save any interesting information to the KB.

        :param cve: The exception
        :param domain: Where we connected to
        :param port: Where we connected to
        :return: None, save information to the KB
        """
        details = self._get_ssl_error_details(cve)
        args = (domain, details)

        desc = ('"%s" uses an invalid SSL certificate.'
                ' The certificate is not trusted because: "%s".')
        desc %= args

        v = Vuln('Invalid SSL certificate', desc,
                 severity.LOW, 1, self.get_name())

        v.set_url(self._url_from_parts(domain, port))
        self.kb_append(self, 'invalid_ssl_cert', v)

    def _get_ssl_cert(self, domain, port):
        """
        Get the certificate information for this domain:port

        :param domain: Where we connected to
        :param port: Where we connected to
        :return: A tuple with:
                    * cert
                    * cert_der
                    * cipher
        """
        def extract_cert_data(domain, port, ssl_sock, result):
            """
            Extract the cert, cert_der and cipher from an ssl socket connection
            """
            result.cert = ssl_sock.getpeercert()
            result.cert_der = ssl_sock.getpeercert(binary_form=True)
            result.cipher = ssl_sock.get_cipher_name()

            return result

        r = self._ssl_connect(domain,
                              port,
                              on_success=extract_cert_data)

        # pylint: disable=E1101
        return r.cert, r.cert_der, r.cipher

    def _cert_expiration_analysis(self, domain, port, cert, cert_der, cipher):
        not_after = cert['notAfter']

        try:
            exp_date = datetime.strptime(not_after, '%Y%m%d%H%M%SZ')
        except ValueError:
            msg = 'Invalid SSL certificate date format: %s' % not_after
            om.out.debug(msg)
            return
        except KeyError:
            msg = 'SSL certificate does not have an "notAfter" field.'
            om.out.debug(msg)
            return

        exp_date_parsed = date(exp_date.year, exp_date.month, exp_date.day)
        expire_days = (exp_date_parsed - date.today()).days

        if expire_days > self._min_expire_days:
            om.out.debug('Certificate will expire in %s days' % expire_days)
            return

        desc = 'The certificate for "%s" will expire soon.' % domain

        i = Info('Soon to expire SSL certificate', desc, 1, self.get_name())
        i.set_url(self._url_from_parts(domain, port))

        self.kb_append(self, 'ssl_soon_expire', i)

    def _ssl_info_to_kb(self, domain, port, cert, cert_der, cipher):
        args = (domain, self._dump_ssl_info(cert, cert_der, cipher))
        desc = 'SSL certificate used for %s:\n%s'
        desc %= args
        
        i = Info('SSL Certificate dump', desc, 1, self.get_name())
        i.set_url(self._url_from_parts(domain, port))
        
        self.kb_append(self, 'certificate', i)

    def _dump_ssl_info(self, cert, cert_der, cipher):
        """
        Dump X509 certificate.
        """
        res = '\n== Certificate information ==\n\n'
        res += pformat(cert)

        res += '\n\n== Used cipher ==\n\n'
        res += cipher

        res += '\n\n== Certificate dump ==\n\n'
        res += ssl.DER_cert_to_PEM_cert(cert_der)
        
        # Indent
        res = res.replace('\n', '\n    ')
        res = '    ' + res
        return res

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = ('Set minimal amount of days before expiration of the certificate'
             ' for alerting')
        h = ('If the certificate will expire in period of minExpireDays w3af'
             ' will show an alert about it, which is useful for admins to'
             ' remember to renew the certificate.')
        o = opt_factory('min_expire_days', self._min_expire_days, d, 'integer', help=h)
        ol.add(o)
        
        d = 'Path to the ca.pem file containing all root certificates'
        o = opt_factory('ca_file_name', self._ca_file, d, INPUT_FILE)
        ol.add(o)
        
        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._min_expire_days = options_list['min_expire_days'].get_value()
        self._ca_file = options_list['ca_file_name'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin audits SSL certificate parameters.

        One configurable parameter exists:
            - min_expire_days
            - ca_file_name

        Note: This plugin is only useful when testing HTTPS sites.
        """


class Result(object):
    pass

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
    """
    Verify that *cert* (in decoded format as returned by
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
        raise CertificateError("hostname %s doesn't match either of %s"
                               % (hostname, ', '.join(map(str, dnsnames))))
    
    elif len(dnsnames) == 1:
        raise CertificateError("hostname %s doesn't match %s"
                               % (hostname, dnsnames[0]))
    else:
        raise CertificateError("no appropriate commonName or "
                               "subjectAltName fields were found")
