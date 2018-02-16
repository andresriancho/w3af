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
import re
import os
import json
import base64
import binascii

import w3af.core.data.constants.severity as severity

from w3af import ROOT_PATH
from w3af.core.controllers.delay_detection.exact_delay_controller import ExactDelayController
from w3af.core.controllers.delay_detection.exact_delay import ExactDelay
from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.data.misc.base64_nopadding import decode_base64
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.dc.generic.form import Form
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.parsers.utils.form_constants import INPUT_TYPE_FILE, INPUT_TYPE_HIDDEN


BASE64_RE = re.compile('^(?:[A-Z0-9+/]{4})*(?:[A-Z0-9+/]{2}==|[A-Z0-9+/]{3}=|[A-Z0-9+/]{4})$')


class deserialization(AuditPlugin):
    """
    Identify deserialization vulnerabilities.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    PAYLOADS = os.path.join(ROOT_PATH, 'plugins/audit/deserialization/')
    PAYLOAD_EXTENSION = '.json'

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

            * If the parameter was found in an HTML form, only inject if the type
              is hidden or file

            * Always inject if the parameter is base64 encoded (use a base64 decoder
              that doesn't care about padding to check if a string is base64 encoded!)

            * Always inject if the parameter is similar to one of our payloads (try
              to identify common strings / magic chars used by payloads)

            * Inject if the parameter is empty

        :param mutant: The mutant we want to inject to (or not)
        :return: True if we should inject into this mutant parameter
        """
        #
        # First we check if the mutant is based on an HTML form, if it is a form
        # and the type of the parameter is NOT hidden, then we don't inject into
        # this parameter.
        #
        # Another scenario where we do want to inject is a multipart form where
        # the parameter type is a file.
        #
        # Why: No sane application is going to unserialize() something that
        #      the user typed
        #
        dc = mutant.get_dc()

        if isinstance(dc, Form):
            token_name = mutant.get_token_name()
            param_type = dc.get_parameter_type(token_name)

            if param_type not in (INPUT_TYPE_FILE, INPUT_TYPE_HIDDEN):
                return False

        original_value = mutant.get_token_original_value()

        #
        # If the parameter is empty, then we inject into it.
        #
        # Why: We never know, maybe the application is going to unserialize() it
        #
        if original_value == '':
            return True

        #
        # If the parameter is base64 encoded, then we inject into it.
        #
        # Why: In most cases base64 is used to encode binary data. Serialized
        #      objects in most languages are composed of binary data.
        #
        if is_base64(original_value):
            return True

        if is_pickled_data(original_value):
            return True

        return False

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
                    json_str = file(os.path.join(root, file_name)).read()
                    yield json.loads(json_str)

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
    Subclass in order to handle creating payloads with different delays, for
    multiple serialization formats.

    The delay_data looks like this:

        {
            "1": {"payload": "Y3RpbWUKc2xlZXAKcDEKKEkxCnRwMgpScDMKLg==",
                  "offset": 17},
            "2": {"payload": "Y3RpbWUKc2xlZXAKcDEKKEkxCnRwMgpScDMKLg==",
                  "offset": 17}
        }

    Where 1 and 2 are the lengths of the delays to add. So, for example if we
    want to delay for 1, 3, or 9 seconds we need to use the first payload,
    and if we want to delay for 11, 32 or 99 seconds we need to use the second
    one.

    This is required because some serialization formats serialize strings using:

        S<length><string-contents>

    We can't just have one payload and replace <string-contents> with 1 or 11,
    the <length> will not match.

    Of course... I could have written an object serializer for java, .net, nodejs,
    python, etc. in order to avoid this ugly solution, but that would have taken
    a few weeks of work to complete.
    """
    def __init__(self, delay_data, delta=0, mult=1):
        super(DeserializationExactDelay, self).__init__(delay_data,
                                                        delta=delta,
                                                        mult=mult)
        self._delay_data = delay_data

    def _get_payload_and_offset(self, delay_len):
        data_for_delay_len = self._delay_data[str(delay_len)]

        payload = data_for_delay_len['payload']
        payload = base64.b64decode(payload)

        offset = data_for_delay_len['offset']

        return payload, offset

    def get_string_for_delay(self, seconds):
        """
        Applies :param seconds to self._delay_fmt and returns a base64 encoded
        string.
        """
        seconds = str(seconds)
        delay_len = len(seconds)
        payload, offset = self._get_payload_and_offset(delay_len)
        return payload[:offset] + seconds + payload[offset + delay_len:]


class B64DeserializationExactDelay(DeserializationExactDelay):
    """
    Subclass in order to provide base64 encoded data as a result of
    get_string_for_delay().
    """
    def get_string_for_delay(self, seconds):
        """
        Applies :param seconds to self._delay_fmt and returns a base64 encoded
        string.
        """
        payload = super(B64DeserializationExactDelay, self).get_string_for_delay(seconds)
        return base64.b64encode(payload)


def is_pickled_data(data):
    """
    :param data: Some data that we see on the application
    :return: True if the data looks like a python pickle
    """
    return data.endswith('\n.')


def is_base64(data):
    """
    Telling if a string is base64 encoded or not is hard. Simply decoding it
    with base64.b64decode will yield a lot of false positives (it successfully
    decodes strings with characters outside of the base64 RFC).

    :param data: A string we saw in the web application
    :return: True if data is a base64 encoded string
    """
    # At least for this plugin we want long base64 strings
    if len(data) < 16:
        return False

    if not BASE64_RE.match(data):
        return False

    try:
        decode_base64(data)
    except binascii.Error:
        return False

    return True
