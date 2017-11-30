"""
rfd.py
 
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
import w3af.core.controllers.output_manager as om
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.fuzzer.mutants.querystring_mutant import QSMutant


PATH_PARAM = '%3B/w3af.cmd%3B/w3af.cmd'
EXEC_TOKEN = 'w3afExecToken'
ESCAPE_CHARS = ('"', '&', '|', '\n')
SHELL_CHARS = ('&', '|')
NOT_VULNERABLE_TYPES = ('application/xml', 'text/xml', 'text/html')


class rfd(AuditPlugin):
    """
    Identify reflected file download vulnerabilities.
    :author: Dmitry (nixwzard@gmail.com)
    """
    def audit(self, freq, orig_response, debugging_id):
        """
        Tests an URL for RFD vulnerabilities.
 
        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        orig_headers = orig_response.headers

        ct, _ = orig_headers.iget('content-type', None)
        cd, _ = orig_headers.iget('content-disposition', None)

        if ct is not None:
            ct = ct.split(';')[0]

        if cd is not None:
            cd = orig_headers['content-disposition']
            # we have the header, but is it was set correctly?

            if 'filename' in cd.lower():
                # yes filename exists
                om.out.debug(u'URL "%s" is not vulnerable to RFD because of'
                             u' explicit filename in content-disposition header'
                             u', response id %s' %
                             (freq.get_url(), orig_response.id))
                return
            else:
                self._test(freq)

        elif ct in NOT_VULNERABLE_TYPES:
            om.out.debug(u'URL "%s" is not vulnerable to RFD because'
                         u' response content-type is "%s" and'
                         u' content-disposition header is missing,'
                         u' response id %s' %
                         (freq.get_url(), ct, orig_response.id))
            return
        else:
            self._test(freq)

    def _report_vuln(self, debug_msg, freq, rid):
        debug_msg = debug_msg % (freq.get_uri(), rid)
        om.out.debug(debug_msg)
        desc = u'Reflected File Download has been ' \
               u'found at: %s'
        desc = desc % freq.get_url()
        v = Vuln.from_fr(u'Reflected File Download vulnerability',
                         desc, severity.HIGH,
                         rid, self.get_name(), freq)
        self.kb_append_uniq(self, 'rfd', v)

    def _test(self, freq):
        uri = freq.get_uri()
        new_path = uri.get_path()+PATH_PARAM
        uri.set_path(new_path)
        freq.set_uri(uri)
        freq.set_querystring(uri.get_querystring())

        payload1 = EXEC_TOKEN
        payload2 = EXEC_TOKEN+''.join(ESCAPE_CHARS)
        payloads = payload1, payload2

        mutants = create_mutants(freq, payloads, mutant_tuple=(QSMutant,))

        for mutant in mutants:
            response = self._uri_opener.send_mutant(mutant)
            body = response.body.decode('unicode-escape')
            if not response.get_code() == 200:
                # no need to seek reflection if it is not OK
                continue

            rpos = body.find(payloads[0])
            if rpos == -1:
                # the input is not reflected
                continue

            # is it JSONP?
            if body[rpos+len(EXEC_TOKEN)] == '(' and not '\"' in body[:rpos]:
                # we've reflected as JSONP callback
                self._report_vuln(u'%s is vulnerable, to RFD because even if'
                                  u' escape chars are filtered, JSONP callback'
                                  u' comes first, response id %s',
                                  freq, response.id)
                break

            # now we need to figure out what escape chars were filtered
            if body[rpos:rpos+len(payloads[1])] == payloads[1]:
                # nothing was filtered or escaped
                self._report_vuln(u'%s is vulnerable to RFD because nothing is'
                                  u' filtered or escaped, response id %s',
                                  freq, response.id)
                return

            filtered, escaped = self._find_escaped_or_filtered(body,
                                                               rpos+len(EXEC_TOKEN),
                                                               ESCAPE_CHARS)

            if '\n' not in filtered:
                self._report_vuln(u'%s is vulnerable to RFD because with'
                                  u' newline we don\'t need any escaping,'
                                  u' response id %s ',
                                  freq, response.id)
                return

            fne = filtered + escaped

            if not '\"' in filtered:
                if not all(char in fne for char in SHELL_CHARS):
                        self._report_vuln(u'%s is vulnerable to RFD because'
                                          u' double quotes are not filtered,'
                                          u' response id %s',
                                          freq, response.id)
                        return

            else:
                #should find out if we have preceding double quotes
                if '\"' in body[:rpos]:
                    continue

                if not all(char in fne for char in SHELL_CHARS):
                        self._report_vuln(u'uri %s is vulnerable to RFD because'
                                          u' we don\'t need to escape double'
                                          u' quotes ,response id %s',
                                          freq, response.id)
                        return

    def _find_escaped_or_filtered(self, body, pos, chars):
        filtered = []
        escaped = []
        for c in chars:
            try:
                if body[pos] == c:
                    pos += 1
                    continue

                elif body[pos] == '\\' and body[pos+1] == c:
                    escaped += [c]
                    pos += 2

                else:
                    filtered += [c]
                    pos += 1

            except IndexError:
                filtered += [c]
                continue

        return filtered, escaped

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin detects Reflected File Download vulnerabilities and is based
        on Oren Hafif's research.
        """
