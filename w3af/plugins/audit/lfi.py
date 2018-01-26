"""
lfi.py

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
from __future__ import with_statement

import w3af.core.controllers.output_manager as om

import w3af.core.data.constants.severity as severity
import w3af.core.data.kb.config as cf

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.controllers.misc.contains_source_code import contains_source_code
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.quick_match.multi_in import MultiIn
from w3af.core.data.quick_match.multi_re import MultiRE
from w3af.core.data.constants.file_patterns import FILE_PATTERNS
from w3af.core.data.misc.encoding import smart_str_ignore
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.kb.info import Info


FILE_OPEN_ERRORS = [# Java
                    'java.io.FileNotFoundException:',
                    'java.lang.Exception:',
                    'java.lang.IllegalArgumentException:',
                    'java.net.MalformedURLException:',

                    # PHP
                    'fread\\(\\):',
                    'for inclusion \'\\(include_path=',
                    'Failed opening required',
                    '<b>Warning</b>:  file\\(',
                    '<b>Warning</b>:  file_get_contents\\(',
                    'open_basedir restriction in effect']


class lfi(AuditPlugin):
    """
    Find local file inclusion vulnerabilities.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    file_pattern_multi_in = MultiIn(FILE_PATTERNS)
    file_read_error_multi_re = MultiRE(FILE_OPEN_ERRORS)

    def audit(self, freq, orig_response, debugging_id):
        """
        Tests an URL for local file inclusion vulnerabilities.

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        mutants = create_mutants(freq,
                                 self.get_lfi_tests(freq),
                                 orig_resp=orig_response)

        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      mutants,
                                      self._analyze_result,
                                      grep=False,
                                      debugging_id=debugging_id)

    def get_lfi_tests(self, freq):
        """
        :param freq: The fuzzable request we're analyzing
        :return: The paths to test
        """
        #
        #   Add some tests which try to read "self"
        #   http://host.tld/show_user.php?id=show_user.php
        #
        lfi_tests = [freq.get_url().get_file_name(),
                     '/%s' % freq.get_url().get_file_name()]

        #
        #   Add some tests which try to read common/known files
        #
        lfi_tests.extend(self._get_common_file_list(freq.get_url()))

        return lfi_tests

    def _get_common_file_list(self, orig_url):
        """
        This method returns a list of local files to try to include.

        :return: A string list, see above.
        """
        local_files = []

        extension = orig_url.get_extension()

        # I will only try to open these files, they are easy to identify of they
        # echoed by a vulnerable web app and they are on all unix or windows
        # default installs. Feel free to mail me (Andres Riancho) if you know
        # about other default files that could be installed on AIX ? Solaris ?
        # and are not /etc/passwd
        if cf.cf.get('target_os') in {'unix', 'unknown'}:
            local_files.append('/../' * 15 + 'etc/passwd')
            local_files.append('../' * 15 + 'etc/passwd')

            local_files.append('/../' * 15 + 'etc/passwd\0')
            local_files.append('/../' * 15 + 'etc/passwd\0.html')
            local_files.append('/etc/passwd')

            # This test adds support for finding vulnerabilities like this one
            # http://website/zen-cart/extras/curltest.php?url=file:///etc/passwd
            local_files.append('file:///etc/passwd')

            local_files.append('/etc/passwd\0')
            local_files.append('/etc/passwd\0.html')

            if extension != '':
                local_files.append('/etc/passwd%00.' + extension)
                local_files.append('/../' * 15 + 'etc/passwd%00.' + extension)

        if cf.cf.get('target_os') in {'windows', 'unknown'}:
            local_files.append('/../' * 15 + 'boot.ini')
            local_files.append('../' * 15 + 'boot.ini')

            local_files.append('/../' * 15 + 'boot.ini\0')
            local_files.append('/../' * 15 + 'boot.ini\0.html')

            local_files.append('C:\\boot.ini')
            local_files.append('C:\\boot.ini\0')
            local_files.append('C:\\boot.ini\0.html')

            local_files.append('%SYSTEMROOT%\\win.ini')
            local_files.append('%SYSTEMROOT%\\win.ini\0')
            local_files.append('%SYSTEMROOT%\\win.ini\0.html')

            # file:// URIs for windows , docs here: http://goo.gl/A9Mvux
            local_files.append('file:///C:/boot.ini')
            local_files.append('file:///C:/win.ini')

            if extension != '':
                local_files.append('C:\\boot.ini%00.' + extension)
                local_files.append('%SYSTEMROOT%\\win.ini%00.' + extension)

        return local_files

    def _analyze_result(self, mutant, response):
        """
        Analyze results of the _send_mutant method.
        Try to find the local file inclusions.
        """
        #
        #   I will only report the vulnerability once.
        #
        if self._has_bug(mutant):
            return

        #
        #   Identify the vulnerability
        #
        for file_pattern_match in self._find_common_file_fragments(response):
            if file_pattern_match not in mutant.get_original_response_body():
                
                desc = 'Local File Inclusion was found at: %s'
                desc %= mutant.found_at()
                
                v = Vuln.from_mutant('Local file inclusion vulnerability',
                                     desc, severity.MEDIUM, response.id,
                                     self.get_name(), mutant)

                v['file_pattern'] = file_pattern_match
                
                v.add_to_highlight(file_pattern_match)
                self.kb_append_uniq(self, 'lfi', v)
                return

        #
        # If the vulnerability could not be identified by matching strings that
        # commonly appear in "/etc/passwd", then I'll check one more thing...
        # (note that this is run if no vulns were identified)
        #
        # http://host.tld/show_user.php?id=show_user.php
        #
        # The calls to smart_str_ignore fix a UnicodeDecoreError which appears when
        # the token value is a binary string which can't be converted to unicode.
        # This happens, for example, when trying to upload JPG files to a multipart form
        #
        # >>> u'' in '\x80'
        # ...
        # UnicodeDecodeError: 'ascii' codec can't decode byte 0x80 in position 0: ordinal not in range(128)
        #
        filename = smart_str_ignore(mutant.get_url().get_file_name())
        token_value = smart_str_ignore(mutant.get_token_value())

        if filename in token_value:
            match, lang = contains_source_code(response)
            if match:
                # We were able to read the source code of the file that is
                # vulnerable to local file read
                desc = ('An arbitrary local file read vulnerability was'
                        ' found at: %s')
                desc %= mutant.found_at()
                
                v = Vuln.from_mutant('Local file inclusion vulnerability',
                                     desc, severity.MEDIUM, response.id,
                                     self.get_name(), mutant)

                #
                #    Set which part of the source code to match
                #
                match_source_code = match.group(0)
                v['file_pattern'] = match_source_code

                self.kb_append_uniq(self, 'lfi', v)
                return

        #
        #   Check for interesting errors (note that this is run if no vulns were
        #   identified)
        #
        body = response.get_body()
        for _, error_str, _ in self.file_read_error_multi_re.query(body):
            if error_str not in mutant.get_original_response_body():
                desc = 'A file read error was found at: %s'
                desc %= mutant.found_at()
                
                i = Info.from_mutant('File read error', desc, response.id,
                                     self.get_name(), mutant)
                i.add_to_highlight(error_str)
                
                self.kb_append_uniq(self, 'error', i)

    def _find_common_file_fragments(self, response):
        """
        This method finds out if the local file has been successfully included
        in the resulting HTML.

        :param response: The HTTP response object
        :return: A list of errors found on the page
        """
        res = set()
        body = response.get_body()

        for file_pattern_match in self.file_pattern_multi_in.query(body):
            res.add(file_pattern_match)

        if len(res) == 1:
            msg = ('A file fragment was found. The section where the file is'
                   ' included is (only a fragment is shown): "%s". This is'
                   ' just an informational message, which might be related'
                   '  to a vulnerability and was found on response with id %s.')
            om.out.debug(msg % (list(res)[0], response.id))
            
        if len(res) > 1:
            msg = ('File fragments have been found. The following is a list'
                   ' of file fragments that were returned by the web'
                   ' application while testing for local file inclusion: \n')
            
            for file_pattern_match in res:
                msg += '- "%s" \n' % file_pattern_match
                
            msg += ('This is just an informational message, which might be'
                    ' related to a vulnerability and was found in response'
                    ' with id %s.' % response.id)
                    
            om.out.debug(msg)
        
        return res

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin will find local file include vulnerabilities.

        Detection is performed by sending specific strings which represent
        common file system paths such as "../../etc/passwd" to all injectable
        parameters and matching strings like "root:x:0:0:" in the response.
        """
