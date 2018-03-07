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
import json
import base64

import w3af.core.data.constants.severity as severity

from w3af import ROOT_PATH
from w3af.core.controllers.delay_detection.exact_delay_controller import ExactDelayController
from w3af.core.controllers.delay_detection.exact_delay import ExactDelay
from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.data.misc.base64_nopadding import maybe_decode_base64
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.dc.generic.form import Form
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.parsers.utils.form_constants import INPUT_TYPE_FILE, INPUT_TYPE_HIDDEN
from w3af.core.data.serialization.detect import (is_java_serialized_data,
                                                 is_net_serialized_data,
                                                 is_nodejs_serialized_data,
                                                 is_pickled_data)


class deserialization(AuditPlugin):
    """
    Identify deserialization vulnerabilities.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    PAYLOADS = os.path.join(ROOT_PATH, 'plugins/audit/deserialization/')
    PAYLOAD_EXTENSION = '.json'
    IS_LANG_FUNCTION_MAP = {'java': is_java_serialized_data,
                            'net': is_net_serialized_data,
                            'node': is_nodejs_serialized_data,
                            'python': is_pickled_data}

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

    def _should_inject(self, mutant, language):
        """
        Should we inject a `language` payload into this mutant? This method will return
        True only if:

            * If the parameter was found in an HTML form, only inject if the type
              is hidden or file

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
        # If the parameter is base64 encoded, then we want to decode it and
        # perform some analysis on it later. While base64 encoding is commonly
        # used for sending serialized objects, not all base64-encoded strings
        # are serialized objects.
        #
        isb64, b64_decoded_ov = maybe_decode_base64(original_value)
        if isb64:
            original_value = b64_decoded_ov

        #
        # This code makes sure that we only send payloads with the expected
        # serialization format. We don't want to send a python pickle when
        # a java serialized object was found in the original_value
        #
        is_lang_serialized_obj = self.IS_LANG_FUNCTION_MAP.get(language)
        if is_lang_serialized_obj(original_value):
            return True

        return False

    def _generate_delay_tests(self, freq):
        """
        Generate the ExactDelay instances for each mutant

        :param freq: The fuzzable request
        :yield: Tuples with mutants and ExactDelay instances
        """
        for mutant in create_mutants(freq, ['', ]):
            for language, payload in self._get_payloads():
                if not self._should_inject(mutant, language):
                    continue

                yield mutant, B64DeserializationExactDelay(payload)
                yield mutant, DeserializationExactDelay(payload)

    def _get_payloads(self):
        """
        :yield: all payloads from the audit/deserialization/ directory.
                The results are (language, payload) tuples.

        Remember that all payloads are base64 encoded!
        """
        for root, dirs, files in os.walk(self.PAYLOADS):

            # Ignore helpers used for creating the nodejs payloads
            if 'node_modules' in root:
                continue

            _, language = os.path.split(root)

            for file_name in files:

                # Ignore helpers used for creating the nodejs payloads
                if file_name in ('package-lock.json', 'package.json'):
                    continue

                if file_name.endswith(self.PAYLOAD_EXTENSION):
                    json_str = file(os.path.join(root, file_name)).read()
                    yield language, json.loads(json_str)

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

        desc = 'Insecure deserialization vulnerability was found at: %s'
        desc %= mutant.found_at()

        v = Vuln.from_mutant('Insecure deserialization',
                             desc,
                             severity.HIGH,
                             [r.id for r in responses],
                             self.get_name(),
                             mutant)

        self.kb_append_uniq(self, 'deserialization', v)

    def get_plugin_deps(self):
        return ['grep.serialized_object']

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds vulnerabilities in the deserialization of untrusted
        data.
        
        These vulnerabilities are found when the application loads an untrusted,
        user-controlled, binary blob into an instance using methods such as
        pickle (Python) or unserialize (Node JS).
        
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

        offsets = data_for_delay_len['offsets']

        return payload, offsets

    def get_string_for_delay(self, seconds):
        """
        Applies :param seconds to self._delay_fmt and returns a base64 encoded
        string.
        """
        seconds = str(seconds)
        delay_len = len(seconds)

        payload, offsets = self._get_payload_and_offset(delay_len)
        payload_lst = list(payload)

        for offset in offsets:
            for i, second_i in enumerate(seconds):
                payload_lst[offset + i] = second_i

        return ''.join(payload_lst)


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
