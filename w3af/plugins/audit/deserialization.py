"""
deserialization.py

Copyright 2018 Andres Riancho

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
import os
import base64

import w3af.core.data.constants.severity as severity

from w3af import ROOT_PATH
from w3af.core.controllers.delay_detection.exact_delay_controller import ExactDelayController
from w3af.core.controllers.delay_detection.exact_delay import ExactDelay
from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.data.misc.base64_nopadding import decode_base64
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.kb.vuln import Vuln


class deserialization(AuditPlugin):
    """
    Identify deserialization vulnerabilities.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    PAYLOADS = os.path.join(ROOT_PATH, 'plugins/audit/deserialization/')
    PAYLOAD_EXTENSION = '.payload'

    def audit(self, freq, orig_response, debugging_id):
        """
        Tests an URL for deserialization vulnerabilities.

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        self._send_mutants_in_threads(func=self._find_delay_in_mutant,
                                      iterable=self._generate_delay_tests(freq),
                                      callback=lambda x, y: None,
                                      debugging_id=debugging_id)

    def _should_inject(self, mutant):
        """
        Should we inject into this mutant? This method will return True only if:

            * Always inject if the parameter is base64 encoded (use a base64 decoder
              that doesn't care about padding to check if a string is base64 encoded!)

            * Always inject if the parameter is similar to one of our payloads (try
              to identify common strings / magic chars used by payloads)

            * Inject if the parameter is empty

            * If the parameter was found in an HTML form, only inject if the type
              is hidden

        :param mutant:
        :return:
        """
        return True

    def _generate_delay_tests(self, freq):
        """
        Generate the ExactDelay instances for each mutant

        :param freq: The fuzzable request
        :yield: Tuples with mutants and ExactDelay instances
        """
        for mutant in create_mutants(freq, ['', ]):

            if not self._should_inject(mutant):
                continue

            for delay_obj in self._get_time_delay_payloads():
                yield mutant, delay_obj

    def _get_time_delay_payloads(self):
        """
        :return: This method yields payloads that when deserialized will introduce
                 a time delay
        """
        for payload in self._get_payloads():
            yield B64DeserializationExactDelay(payload)
            yield DeserializationExactDelay(payload)

    def _get_payloads(self):
        """
        :yield: all payloads from the audit/deserialization/ directory

        Remember that all payloads are base64 encoded!
        """
        for root, dirs, files in os.walk(self.PAYLOADS):
            for file_name in files:
                if file_name.endswith(self.PAYLOAD_EXTENSION):
                    yield file(os.path.join(root, file_name)).read().strip()

    def _find_delay_in_mutant(self, (mutant, delay_obj), debugging_id=None):
        """
        Try to delay the response and save a vulnerability if successful

        :param mutant: The mutant to modify and test
        :param delay_obj: The delay to use
        :param debugging_id: The debugging ID for logging
        """
        if self._has_bug(mutant):
            return

        ed = ExactDelayController(mutant, delay_obj, self._uri_opener)
        ed.set_debugging_id(debugging_id)
        success, responses = ed.delay_is_controlled()

        if not success:
            return

        desc = 'Insecure deserialization vulnerability was found at: %s' % mutant.found_at()

        v = Vuln.from_mutant('Insecure deserialization',
                             desc,
                             severity.HIGH,
                             [r.id for r in responses],
                             self.get_name(),
                             mutant)

        self.kb_append_uniq(self, 'deserialization', v)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds vulnerabilities in the deserialization of untrusted
        data.
        
        These vulnerabilities are found when the application loads an untrusted,
        user-controlled, binary blob into an instance using methods such as
        pickle (Python) or unserialize (PHP and Node JS).
        
        The plugin will send various payloads to identify vulnerabilities in
        different languages and programming frameworks, all payloads use time
        delays to confirm the vulnerability. 
        """


class DeserializationExactDelay(ExactDelay):
    """
    Subclass in order to provide binary data as a result of get_string_for_delay().

    The delay_fmt is provided base64 encoded

    Instead of using string formatting to replace the delay we do a string replace
    of __DELAY_HERE__. This change is to make sure that we don't break the payload
    in any way, or crash because the payload has a %s we never expected.
    """
    REPLACE_TOKEN = '__DELAY_HERE__'

    def __init__(self, delay_fmt, delta=0, mult=1):
        super(DeserializationExactDelay, self).__init__(delay_fmt,
                                                        delta=delta,
                                                        mult=mult)
        self._delay_fmt = decode_base64(delay_fmt)

    def get_string_for_delay(self, seconds):
        """
        Applies :param seconds to self._delay_fmt and returns a base64 encoded
        string.
        """
        real_delay = ((seconds * self._delay_multiplier) + self._delay_delta)
        real_delay = str(real_delay)
        payload = self._delay_fmt.replace(self.REPLACE_TOKEN, real_delay)
        return base64.b64encode(payload)


class B64DeserializationExactDelay(DeserializationExactDelay):
    """
    Subclass in order to provide base64 encoded data as a result of
    get_string_for_delay().

    The delay_fmt is provided base64 encoded

    Instead of using string formatting to replace the delay we do a string replace
    of __DELAY_HERE__. This change is to make sure that we don't break the payload
    in any way, or crash because the payload has a %s we never expected.
    """
    def get_string_for_delay(self, seconds):
        """
        Applies :param seconds to self._delay_fmt and returns a base64 encoded
        string.
        """
        payload = super(B64DeserializationExactDelay, self).get_string_for_delay(seconds)
        return base64.b64encode(payload)
