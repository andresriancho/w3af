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

import re

import w3af.core.controllers.output_manager as om

import w3af.core.data.constants.severity as severity
import w3af.core.data.kb.config as cf

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.controllers.misc.is_source_file import is_source_file
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.esmre.multi_in import multi_in
from w3af.core.data.constants.file_patterns import FILE_PATTERNS
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.kb.info import Info


class lfi(AuditPlugin):
    """
    Find local file inclusion vulnerabilities.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    FILE_PATTERNS = FILE_PATTERNS
    _multi_in = multi_in(FILE_PATTERNS)

    def __init__(self):
        AuditPlugin.__init__(self)

        # Internal variables
        self._file_compiled_regex = []
        self._error_compiled_regex = []
        self._open_basedir = False

    def audit(self, freq, orig_response):
        """
        Tests an URL for local file inclusion vulnerabilities.

        :param freq: A FuzzableRequest
        """
        # Which payloads do I want to send to the remote end?
        local_files = []
        local_files.append(freq.get_url().get_file_name())
        if not self._open_basedir:
            local_files.extend(self._get_local_file_list(freq.get_url()))

        mutants = create_mutants(freq, local_files, orig_resp=orig_response)

        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      mutants,
                                      self._analyze_result,
                                      grep=False)

    def _get_local_file_list(self, orig_url):
        """
        This method returns a list of local files to try to include.

        :return: A string list, see above.
        """
        local_files = []

        extension = orig_url.get_extension()

        # I will only try to open these files, they are easy to identify of they
        # echoed by a vulnerable web app and they are on all unix or windows default installs.
        # Feel free to mail me ( Andres Riancho ) if you know about other default files that
        # could be installed on AIX ? Solaris ? and are not /etc/passwd
        if cf.cf.get('target_os') in ['unix', 'unknown']:
            local_files.append("../" * 15 + "etc/passwd")
            local_files.append("../" * 15 + "etc/passwd\0")
            local_files.append("../" * 15 + "etc/passwd\0.html")
            local_files.append("/etc/passwd")

            # This test adds support for finding vulnerabilities like this one
            # http://website/zen-cart/extras/curltest.php?url=file:///etc/passwd
            #local_files.append("file:///etc/passwd")

            local_files.append("/etc/passwd\0")
            local_files.append("/etc/passwd\0.html")
            if extension != '':
                local_files.append("/etc/passwd%00." + extension)
                local_files.append("../" * 15 + "etc/passwd%00." + extension)

        if cf.cf.get('target_os') in ['windows', 'unknown']:
            local_files.append("../" * 15 + "boot.ini\0")
            local_files.append("../" * 15 + "boot.ini\0.html")
            local_files.append("C:\\boot.ini")
            local_files.append("C:\\boot.ini\0")
            local_files.append("C:\\boot.ini\0.html")
            local_files.append("%SYSTEMROOT%\\win.ini")
            local_files.append("%SYSTEMROOT%\\win.ini\0")
            local_files.append("%SYSTEMROOT%\\win.ini\0.html")
            if extension != '':
                local_files.append("C:\\boot.ini%00." + extension)
                local_files.append("%SYSTEMROOT%\\win.ini%00." + extension)

        return local_files

    def _analyze_result(self, mutant, response):
        """
        Analyze results of the _send_mutant method.
        Try to find the local file inclusions.
        """
        # I analyze the response searching for a specific PHP error string
        # that tells me that open_basedir is enabled, and our request triggered
        # the restriction. If open_basedir is in use, it makes no sense to keep
        # trying to read "/etc/passwd", that is why this variable is used to
        # determine which tests to send if it was possible to detect the usage
        # of this security feature.
        if not self._open_basedir:
            
            basedir_warning = 'open_basedir restriction in effect'
            
            if basedir_warning in response and \
            basedir_warning not in mutant.get_original_response_body():
                self._open_basedir = True

        #
        #   I will only report the vulnerability once.
        #
        if self._has_bug(mutant):
            return

        #
        #   Identify the vulnerability
        #
        file_content_list = self._find_file(response)
        for file_pattern_match in file_content_list:
            if file_pattern_match not in mutant.get_original_response_body():
                
                desc = 'Local File Inclusion was found at: %s'
                desc = desc % mutant.found_at()
                
                v = Vuln.from_mutant('Local file inclusion vulnerability',
                                     desc, severity.MEDIUM, response.id,
                                     self.get_name(), mutant)

                v['file_pattern'] = file_pattern_match
                
                v.add_to_highlight(file_pattern_match)
                self.kb_append_uniq(self, 'lfi', v)
                return

        #
        #   If the vulnerability could not be identified by matching strings that commonly
        #   appear in "/etc/passwd", then I'll check one more thing...
        #   (note that this is run if no vulns were identified)
        #
        #   http://host.tld/show_user.php?id=show_user.php
        if mutant.get_mod_value() == mutant.get_url().get_file_name():
            match, lang = is_source_file(response.get_body())
            if match:
                # We were able to read the source code of the file that is
                # vulnerable to local file read
                desc = 'An arbitrary local file read vulnerability was'\
                       ' found at: %s' % mutant.found_at()
                
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
        for regex in self.get_include_errors():

            match = regex.search(response.get_body())

            if match and not regex.search(mutant.get_original_response_body()):
                desc = 'A file read error was found at: %s'
                desc = desc % mutant.found_at()
                
                i = Info.from_mutant('File read error', desc, response.id,
                                     self.get_name(), mutant)
                
                self.kb_append_uniq(self, 'error', i)

    def _find_file(self, response):
        """
        This method finds out if the local file has been successfully included in
        the resulting HTML.

        :param response: The HTTP response object
        :return: A list of errors found on the page
        """
        res = set()
        for file_pattern_match in self._multi_in.query(response.get_body()):
            res.add(file_pattern_match)

        if len(res) == 1:
            msg = 'A file fragment was found. The section where the file is'\
                  ' included is (only a fragment is shown): "%s". This is' \
                  ' just an informational message, which might be related' \
                  '  to a vulnerability and was found on response with id %s.'
            om.out.debug(msg % (list(res)[0], response.id))
            
        if len(res) > 1:
            msg = 'File fragments have been found. The following is a list' \
                  ' of file fragments that were returned by the web application' \
                  ' while testing for local file inclusion: \n'
            
            for file_pattern_match in res:
                msg += '- "%s" \n' % file_pattern_match
                
            msg += 'This is just an informational message, which might be' \
                   ' related to a vulnerability and was found in response' \
                   ' with id %s.' % response.id
                    
            om.out.debug(msg)
        
        return res

    def get_include_errors(self):
        """
        :return: A list of file inclusion / file read errors generated by the web application.
        """
        #
        #   In previous versions of the plugin the "Inclusion errors" listed in the _get_file_patterns
        #   method made sense... but... it seems that they trigger false positives...
        #   So I moved them here and report them as something "interesting" if the actual file
        #   inclusion is not possible
        #
        if self._error_compiled_regex:
            return self._error_compiled_regex
        else:
            read_errors = ["java.io.FileNotFoundException:",
                           'java.lang.Exception:',
                           'java.lang.IllegalArgumentException:',
                           'java.net.MalformedURLException:',
                           'The server encountered an internal error \\(.*\\) that prevented it from fulfilling this request.',
                           'The requested resource \\(.*\\) is not available.',
                           "fread\\(\\):",
                           "for inclusion '\\(include_path=",
                           "Failed opening required",
                           "<b>Warning</b>:  file\\(",
                           "<b>Warning</b>:  file_get_contents\\("]

            self._error_compiled_regex = [re.compile(i, re.IGNORECASE) for i in read_errors]
            return self._error_compiled_regex

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin will find local file include vulnerabilities. This is done by
        sending to all injectable parameters file paths like "../../../../../etc/passwd"
        and searching in the response for strings like "root:x:0:0:".
        """
