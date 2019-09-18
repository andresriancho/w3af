"""
fingerprint_WAF.py

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

from itertools import izip, repeat

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.data.fuzzer.utils import rand_alpha
from w3af.core.data.kb.info import Info


class fingerprint_WAF(InfrastructurePlugin):
    """
    Identify if a Web Application Firewall is present and if possible identify
    the vendor and version.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    """
    CHANGELOG:
    Feb/17/2009- Added Signatures by Aung Khant (aungkhant[at]yehg.net):
    - Old version F5 Traffic Shield, NetContinuum, TEROS, BinarySec
    """

    """
    Currently (09/2014) most cookie names are matched case insensitive using
    python's re.IGNORECASE . This should be configurable.
    """

    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request, debugging_id):
        """
        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        methods = [self._fingerprint_URLScan,
                   self._fingerprint_ModSecurity,
                   self._fingerprint_SecureIIS,
                   self._fingerprint_Airlock,
                   self._fingerprint_Barracuda,
                   self._fingerprint_CloudFlare,
                   self._fingerprint_DenyAll,
                   self._fingerprint_dotDefender,
                   self._fingerprint_F5ASM,
                   self._fingerprint_F5TrafficShield,
                   self._fingerprint_FortiWeb,
                   self._fingerprint_IBMWebSphere,
                   self._fingerprint_Incapsula,
                   self._fingerprint_Profense,
                   self._fingerprint_TEROS,
                   self._fingerprint_NetContinuum,
                   self._fingerprint_BinarySec,
                   self._fingerprint_HyperGuard]

        args_iter = izip(methods, repeat(fuzzable_request))
        self.worker_pool.map_multi_args(self._worker, args_iter)

    def _worker(self, func, fuzzable_request):
        return func(fuzzable_request)

    def _fingerprint_SecureIIS(self, fuzzable_request):
        """
        Try to verify if SecureIIS is installed or not.
        """
        # And now a final check for SecureIIS
        headers = fuzzable_request.get_headers()
        headers['Transfer-Encoding'] = rand_alpha(1024 + 1)
        try:
            lock_response2 = self._uri_opener.GET(fuzzable_request.get_url(),
                                                  headers=headers, cache=True)
        except BaseFrameworkException, w3:
            om.out.debug(
                'Failed to identify secure IIS, exception: ' + str(w3))
        else:
            if lock_response2.get_code() == 404:
                self._report_finding('SecureIIS', lock_response2)

    def _fingerprint_ModSecurity(self, fuzzable_request):
        """
        Try to verify if mod_security is installed or not AND try to get the
        installed version.
        """
        pass

    def _fingerprint_Airlock(self, fuzzable_request):
        """
        Try to verify if Airlock is present.
        """
        om.out.debug('detect Airlock')
        response = self._uri_opener.GET(fuzzable_request.get_url(), cache=True)
        for header_name in response.get_headers().keys():
            if header_name.lower() == 'set-cookie':
                protected_by = response.get_headers()[header_name]
                if re.match('^AL[_-]?(SESS|LB)(-S)?=', protected_by, re.IGNORECASE):
                    self._report_finding('Airlock', response, protected_by)
                    return
            # else
                # more checks, like path /error_path or encrypted URL in response

    def _fingerprint_Barracuda(self, fuzzable_request):
        """
        Try to verify if Barracuda is present.
        """
        om.out.debug('detect Barracuda')
        response = self._uri_opener.GET(fuzzable_request.get_url(), cache=True)
        for header_name in response.get_headers().keys():
            if header_name.lower() == 'set-cookie':
                # ToDo: not sure if this is always there (08jul08 Achim)
                protected_by = response.get_headers()[header_name]
                if re.match('^barra_counter_session=', protected_by, re.IGNORECASE):
                    self._report_finding('Barracuda', protected_by)
                    return
            # else
                # don't know ...

    def _fingerprint_CloudFlare(self, fuzzable_request):
        """
        Try to verify if CloudFlare Web Application Firewall is present.
        """
        om.out.debug('detect CloudFlare')
        response = self._uri_opener.GET(fuzzable_request.get_url(), cache=True)
        for header_name in response.get_headers().keys():
            if header_name.lower() == 'set-cookie':
                protected_by = response.get_headers()[header_name]
                if re.match('^(cloudflare(-nginx)?|__cfduid)=', protected_by):
                    self._report_finding(
                        'CloudFlare', response, protected_by)
                    return
            # else
                # don't know ...

    def _fingerprint_dotDefender(self, fuzzable_request):
        """
        Try to verify if dotDefender is present.
        """
        om.out.debug('detect dotDefender')
        response = self._uri_opener.GET(fuzzable_request.get_url(), cache=True)
        for header_name in response.get_headers().keys():
            if header_name.lower() == 'set-cookie':
                protected_by = response.get_headers()[header_name]
                if re.match('^X-dotDefender-denied=', protected_by):
                    self._report_finding(
                        'dotDefender', response, protected_by)
                    return
            # else
                # don't know ...

    def _fingerprint_DenyAll(self, fuzzable_request):
        """
        Try to verify if Deny All rWeb is present.
        """
        om.out.debug('detect Deny All')
        response = self._uri_opener.GET(fuzzable_request.get_url(), cache=True)
        for header_name in response.get_headers().keys():
            if header_name.lower() == 'set-cookie':
                protected_by = response.get_headers()[header_name]
                if re.match('^sessioncookie=', protected_by):
                    self._report_finding(
                        'Deny All rWeb', response, protected_by)
                    return
            # else
                # more checks like detection=detected cookie
                # or  200 Condition Intercepted

    def _fingerprint_F5ASM(self, fuzzable_request):
        """
        Try to verify if F5 ASM (also TrafficShield) is present.
        """
        om.out.debug('detect F5 ASM or TrafficShield')
        response = self._uri_opener.GET(fuzzable_request.get_url(), cache=True)
        for header_name in response.get_headers().keys():
            if header_name.lower() == 'set-cookie':
                protected_by = response.get_headers()[header_name]
                if re.match('^TS[a-zA-Z0-9]{3,6}=', protected_by):
                    self._report_finding('F5 ASM', response, protected_by)
                    return
            elif header_name.lower() == 'X-Cnection':
                if re.match('^close', response.get_headers()[header_name]):
                    self._report_finding('F5 ASM', response, protected_by)
                    return

    def _fingerprint_F5TrafficShield(self, fuzzable_request):
        """
        Try to verify if the older version F5 TrafficShield is present.
        Ref: Hacking Exposed - Web Application

        """
        om.out.debug('detect the older version F5 TrafficShield')
        response = self._uri_opener.GET(fuzzable_request.get_url(), cache=True)
        for header_name in response.get_headers().keys():
            if header_name.lower() == 'set-cookie':
                protected_by = response.get_headers()[header_name]
                if re.match('^ASINFO=', protected_by, re.IGNORECASE):
                    self._report_finding(
                        'F5 TrafficShield', response, protected_by)
                    return
            # else
                # more checks like special string in response

    def _fingerprint_FortiWeb(self, fuzzable_request):
        """
        Try to verify if FortiWeb is present.
        """
        om.out.debug('detect FortiWeb')
        response = self._uri_opener.GET(fuzzable_request.get_url(), cache=True)
        for header_name in response.get_headers().keys():
            if header_name.lower() == 'set-cookie':
                protected_by = response.get_headers()[header_name]
                if re.match('^FORTIWAFSID=', protected_by, re.IGNORECASE):
                    self._report_finding(
                        'FortiWeb', response, protected_by)
                    return
            # else
                # don't know ...

    def _fingerprint_Incapsula(self, fuzzable_request):
        """
        Try to verify if Incapsula is present.
        """
        om.out.debug('detect FortiWeb')
        response = self._uri_opener.GET(fuzzable_request.get_url(), cache=True)
        for header_name in response.get_headers().keys():
            if header_name.lower() == 'set-cookie':
                protected_by = response.get_headers()[header_name]
                if re.match('^(incap_ses|visid_incap)=', protected_by, re.IGNORECASE):
                    self._report_finding('Incapsula', response, protected_by)
                    return
            # else
                # don't know ...

    def _fingerprint_IBMWebSphere(self, fuzzable_request):
        """
        Try to verify if IBM WebSphere DataPower is present.
        """
        om.out.debug('detect IBM WebSphere')
        response = self._uri_opener.GET(fuzzable_request.get_url(), cache=True)
        for header_name in response.get_headers().keys():
            if header_name.lower() == 'set-cookie':
                protected_by = response.get_headers()[header_name]
                if re.match('^X-Backside-Transport=', protected_by, re.IGNORECASE):
                    self._report_finding('IBM WebSphere', response, protected_by)
                    return
            # else
                # don't know ...

    def _fingerprint_Profense(self, fuzzable_request):
        """
        Try to verify if Profense is present.
        """
        om.out.debug('detect Profense')
        response = self._uri_opener.GET(fuzzable_request.get_url(), cache=True)
        for header_name in response.get_headers().keys():
            if header_name.lower() == 'set-cookie':
                protected_by = response.get_headers()[header_name]
                if re.match('^PLBSID==', protected_by, re.IGNORECASE):
                    self._report_finding('Profense', response, protected_by)
                    return
            elif header_name.lower() == 'Server':
                if re.match('^Profense', response.get_headers()[header_name], re.IGNORECASE):
                    self._report_finding('Profense', response, protected_by)
                    return

    def _fingerprint_TEROS(self, fuzzable_request):
        """
        Try to verify if TEROS is present.
        Ref: Hacking Exposed - Web Application

        """
        om.out.debug('detect TEROS')
        response = self._uri_opener.GET(fuzzable_request.get_url(), cache=True)
        for header_name in response.get_headers().keys():
            if header_name.lower() == 'set-cookie':
                protected_by = response.get_headers()[header_name]
                if re.match('^st8id=', protected_by):
                    self._report_finding('TEROS', response, protected_by)
                    return
            # else
                # more checks like special string in response

    def _fingerprint_NetContinuum(self, fuzzable_request):
        """
        Try to verify if NetContinuum is present.
        Ref: Hacking Exposed - Web Application

        """
        om.out.debug('detect NetContinuum')
        response = self._uri_opener.GET(fuzzable_request.get_url(), cache=True)
        for header_name in response.get_headers().keys():
            if header_name.lower() == 'set-cookie':
                protected_by = response.get_headers()[header_name]
                if re.match('^NCI__SessionId=', protected_by, re.IGNORECASE):
                    self._report_finding(
                        'NetContinuum', response, protected_by)
                    return
            # else
                # more checks like special string in response

    def _fingerprint_BinarySec(self, fuzzable_request):
        """
        Try to verify if BinarySec is present.
        """
        om.out.debug('detect BinarySec')
        response = self._uri_opener.GET(fuzzable_request.get_url(), cache=True)
        for header_name in response.get_headers().keys():
            if header_name.lower() == 'server':
                protected_by = response.get_headers()[header_name]
                if re.match('BinarySec', protected_by, re.IGNORECASE):
                    self._report_finding('BinarySec', response, protected_by)
                    return
            # else
                # more checks like special string in response

    def _fingerprint_HyperGuard(self, fuzzable_request):
        """
        Try to verify if HyperGuard is present.
        """
        om.out.debug('detect HyperGuard')
        response = self._uri_opener.GET(fuzzable_request.get_url(), cache=True)
        for header_name in response.get_headers().keys():
            if header_name.lower() == 'set-cookie':
                protected_by = response.get_headers()[header_name]
                if re.match('^WODSESSION=', protected_by, re.IGNORECASE):
                    self._report_finding('HyperGuard', response, protected_by)
                    return
            # else
                # more checks like special string in response

    def _fingerprint_URLScan(self, fuzzable_request):
        """
        Try to verify if URLScan is installed or not.
        """
        # detect using GET
        # Get the original response
        orig_response = self._uri_opener.GET(
            fuzzable_request.get_url(), cache=True)
        if orig_response.get_code() != 404:
            # Now add the if header and try again
            headers = fuzzable_request.get_headers()
            headers['If'] = rand_alpha(8)
            if_response = self._uri_opener.GET(fuzzable_request.get_url(),
                                               headers=headers,
                                               cache=True)
            headers = fuzzable_request.get_headers()
            headers['Translate'] = rand_alpha(8)
            translate_response = self._uri_opener.GET(
                fuzzable_request.get_url(),
                headers=headers,
                cache=True)

            headers = fuzzable_request.get_headers()
            headers['Lock-Token'] = rand_alpha(8)
            lock_response = self._uri_opener.GET(fuzzable_request.get_url(),
                                                 headers=headers,
                                                 cache=True)

            headers = fuzzable_request.get_headers()
            headers['Transfer-Encoding'] = rand_alpha(8)
            transfer_enc_response = self._uri_opener.GET(
                fuzzable_request.get_url(),
                headers=headers,
                cache=True)

            if if_response.get_code() == 404 or translate_response.get_code() == 404 or\
                    lock_response.get_code() == 404 or transfer_enc_response.get_code() == 404:
                self._report_finding('URLScan', lock_response)

    def _report_finding(self, name, response, protected_by=None):
        """
        Creates a information object based on the name and the response
        parameter and saves the data in the kb.

        :param name: The name of the WAF
        :param response: The HTTP response object that was used to identify the WAF
        :param protected_by: A more detailed description/version of the WAF
        """
        desc = 'The remote network seems to have a "%s" WAF deployed to' \
               ' protect access to the web server.'
        desc = desc % name
        
        if protected_by:
            desc += ' The following is the WAF\'s version: "%s".' % protected_by
        
        i = Info('Web Application Firewall fingerprint', desc, response.id,
                 self.get_name())
        i.set_url(response.get_url())
        i.set_id(response.id)

        kb.kb.append(self, name, i)
        om.out.information(i.get_desc())

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins that should be run before
                 the current one.
        """
        return ['infrastructure.afd']

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        Try to fingerprint the Web Application Firewall that is running on the
        remote end.

        Please note that the detection of the WAF is performed by the
        infrastructure.afd plugin (afd stands for Active Filter Detection).
        """
