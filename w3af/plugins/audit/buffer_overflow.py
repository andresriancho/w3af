"""
buffer_overflow.py

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
from itertools import repeat
from tblib.decorators import Error

import w3af.core.data.constants.severity as severity

from w3af.core.controllers.threads.decorators import apply_with_return_error
from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.controllers.exceptions import (BaseFrameworkException,
                                              ScanMustStopException)
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.quick_match.multi_in import MultiIn
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.kb.info import Info


class buffer_overflow(AuditPlugin):
    """
    Find buffer overflow vulnerabilities.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    OVERFLOW_ERRORS = (
        '*** stack smashing detected ***:',
        'Backtrace:',
        'Memory map:',
        
        # Note that the lack of commas after the strings is intentional
        '<html><head>\n<title>500 Internal Server Error</title>\n'
        '</head><body>\n<h1>'
        'Internal Server Error</h1>'
    )

    _multi_in = MultiIn(OVERFLOW_ERRORS)

    # TODO: if lengths = [ 65 , 257 , 513 , 1025, 2049, 4097, 8000 ]
    # then i get a BadStatusLine exception from urllib2, is seems to be an
    # internal error. Tested against tomcat 5.5.7
    BUFFER_TESTS = ['A' * payload_len for payload_len in [65, 257, 513, 1025, 2049]]

    def __init__(self):
        """
        Some notes:
            On Apache, when an overflow happends on a cgic script, this is
            written to the log:
                *** stack smashing detected ***:

                    /var/www/.../buffer_overflow.cgi terminated,
                    referer: http://localhost/w3af/buffer_overflow.cgi

                    Premature end of script headers: buffer_overflow.cgi,
                    referer: ...

            On Apache, when an overflow happens on a cgic script, this is
            returned to the user:
                <!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
                <html><head>
                <title>500 Internal Server Error</title>
                </head><body>
                <h1>Internal Server Error</h1>
                <p>The server encountered an internal error or
                misconfiguration and was unable to complete
                your request.</p>
                <p>Please contact the server administrator,
                 webmaster@localhost and inform them of the time the error
                 occurred,
                and anything you might have done that may have
                caused the error.</p>
                <p>More information about this error may be available
                in the server error log.</p>
                <hr>
                <address>Apache/2.0.55 (Ubuntu) mod_python/3.2.8 Python/2.4.4c1
                PHP/5.1.6 Server at localhost Port 80</address>
                </body></html>

            Note that this is an Apache error 500, not the more common PHP error
            500.
        """
        AuditPlugin.__init__(self)

    def audit(self, freq, orig_response, debugging_id):
        """
        Tests an URL for buffer overflow vulnerabilities.

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        mutants = create_mutants(freq, self.BUFFER_TESTS, orig_resp=orig_response)
        args = zip(repeat(self._send_request), mutants, repeat(debugging_id))

        for result in self.worker_pool.imap_unordered(apply_with_return_error, args):
            # re-raise the thread exception in the main thread with this method
            # so we get a nice traceback instead of things like the ones we see
            # in https://github.com/andresriancho/w3af/issues/7287
            if isinstance(result, Error):
                result.reraise()

    def _send_request(self, mutant, debugging_id):
        """
        Sends a mutant to the remote web server. I wrap urllib's _send_mutant
        just to handle errors in a different way.
        """
        # Only grep the request which sends the larger payload
        grep = mutant.get_token_value() == self.BUFFER_TESTS[-1]

        try:
            response = self._uri_opener.send_mutant(mutant,
                                                    debugging_id=debugging_id,
                                                    grep=grep)
        except (BaseFrameworkException, ScanMustStopException):
            desc = ('A potential (most probably a false positive than a bug)'
                    ' buffer-overflow was found when requesting: "%s", using'
                    ' HTTP method %s. The data sent was: "%s".')
            desc %= (mutant.get_url(), mutant.get_method(), mutant.get_dc())

            i = Info.from_mutant('Potential buffer overflow vulnerability',
                                 desc, [], self.get_name(), mutant)
            
            self.kb_append_uniq(self, 'buffer_overflow', i)
        else:
            self._analyze_result(mutant, response)

    def _analyze_result(self, mutant, response):
        """
        Analyze results of the _send_mutant method.
        """
        for error_str in self._multi_in.query(response.body):

            if error_str in mutant.get_original_response_body():
                continue

            if self._has_bug(mutant):
                continue

            desc = ('A potential buffer overflow (accurate detection is'
                    ' hard) was found at: %s')
            desc %= mutant.found_at()

            v = Vuln.from_mutant('Buffer overflow vulnerability', desc,
                                 severity.MEDIUM, response.id,
                                 self.get_name(), mutant)
            v.add_to_highlight(error_str)

            self.kb_append_uniq(self, 'buffer_overflow', v)

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins that should be run before
                 the current one.
        """
        return ['grep.error_500']

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds buffer overflow vulnerabilities.

        Users have to know that detecting a buffer overflow vulnerability will
        be only possible if the server is configured to return errors, and the
        application is developed in cgi-c or some other language that allows
        the programmer to do their own memory management.
        """
