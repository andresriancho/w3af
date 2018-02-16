"""
test_deserialization.py

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
import re
import json
import urllib
import cPickle
import base64
import unittest

from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse
from w3af.plugins.audit.deserialization import deserialization, B64DeserializationExactDelay
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.fuzzer.mutants.querystring_mutant import QSMutant
from w3af.core.data.fuzzer.mutants.postdata_mutant import PostDataMutant
from w3af.core.data.dc.urlencoded_form import URLEncodedForm
from w3af.core.data.parsers.utils.form_params import FormParameters


test_config = {
    'audit': (PluginConfig('deserialization'),),
}


class TestDeserializePickle(PluginTest):

    target_url = 'http://mock/deserialize?message='

    class DeserializeMockResponse(MockResponse):
        def get_response(self, http_request, uri, response_headers):
            uri = urllib.unquote(uri)
            b64message = uri[uri.find('=') + 1:]

            try:
                message = base64.b64decode(b64message)
            except Exception, e:
                body = str(e)
                return self.status, response_headers, body

            try:
                cPickle.loads(message)
            except Exception, e:
                body = str(e)
                return self.status, response_headers, body

            body = 'Message received'
            return self.status, response_headers, body

    MOCK_RESPONSES = [DeserializeMockResponse(re.compile('.*'), body=None,
                                              method='GET', status=200)]

    def test_found_deserialization_in_pickle(self):
        self._scan(self.target_url, test_config)
        vulns = self.kb.get('deserialization', 'deserialization')

        self.assertEquals(1, len(vulns), vulns)

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]

        self.assertEquals('message', vuln.get_token_name())
        self.assertEquals('Insecure deserialization', vuln.get_name())


class TestDeserializePickleNotBase64(PluginTest):

    target_url = 'http://mock/deserialize?message='

    class DeserializeMockResponse(MockResponse):
        def get_response(self, http_request, uri, response_headers):
            uri = urllib.unquote(uri)
            message = uri[uri.find('=') + 1:]
            message = str(message)

            try:
                cPickle.loads(message)
            except Exception, e:
                body = str(e)
                return self.status, response_headers, body

            body = 'Message received'
            return self.status, response_headers, body

    MOCK_RESPONSES = [DeserializeMockResponse(re.compile('.*'), body=None,
                                              method='GET', status=200)]

    def test_found_deserialization_in_pickle(self):
        self._scan(self.target_url, test_config)
        vulns = self.kb.get('deserialization', 'deserialization')

        self.assertEquals(1, len(vulns), vulns)

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]

        self.assertEquals('message', vuln.get_token_name())
        self.assertEquals('Insecure deserialization', vuln.get_name())


class TestShouldInjectIsCalled(PluginTest):

    target_url = 'http://mock/deserialize?message=this-disables-injection'

    class DeserializeMockResponse(MockResponse):
        def get_response(self, http_request, uri, response_headers):
            uri = urllib.unquote(uri)
            b64message = uri[uri.find('=') + 1:]

            try:
                message = base64.b64decode(b64message)
            except Exception, e:
                body = str(e)
                return self.status, response_headers, body

            try:
                cPickle.loads(message)
            except Exception, e:
                body = str(e)
                return self.status, response_headers, body

            body = 'Message received'
            return self.status, response_headers, body

    MOCK_RESPONSES = [DeserializeMockResponse(re.compile('.*'), body=None,
                                              method='GET', status=200)]

    def test_found_deserialization_in_pickle(self):
        self._scan(self.target_url, test_config)
        vulns = self.kb.get('deserialization', 'deserialization')

        self.assertEquals(0, len(vulns), vulns)


class TestShouldInject(unittest.TestCase):
    def setUp(self):
        self.plugin = deserialization()
        self.payloads = ['']
        self.fuzzer_config = {}

    def test_should_inject_empty_qs(self):
        self.url = URL('http://moth/?id=')
        freq = FuzzableRequest(self.url)

        mutant = QSMutant.create_mutants(freq, self.payloads, [],
                                         False, self.fuzzer_config)[0]

        self.assertTrue(self.plugin._should_inject(mutant))

    def test_should_not_inject_qs_with_digit(self):
        self.url = URL('http://moth/?id=1')
        freq = FuzzableRequest(self.url)

        mutant = QSMutant.create_mutants(freq, self.payloads, [],
                                         False, self.fuzzer_config)[0]

        self.assertFalse(self.plugin._should_inject(mutant))

    def test_should_inject_qs_with_b64(self):
        b64data = base64.b16encode('just some random b64 data here')
        self.url = URL('http://moth/?id=%s' % b64data)
        freq = FuzzableRequest(self.url)

        mutant = QSMutant.create_mutants(freq, self.payloads, [],
                                         False, self.fuzzer_config)[0]

        self.assertTrue(self.plugin._should_inject(mutant))

    def test_should_inject_qs_with_pickle(self):
        pickle_data = cPickle.dumps(1)
        self.url = URL('http://moth/?id=%s' % pickle_data)
        freq = FuzzableRequest(self.url)

        mutant = QSMutant.create_mutants(freq, self.payloads, [],
                                         False, self.fuzzer_config)[0]

        self.assertTrue(self.plugin._should_inject(mutant))

    def test_should_inject_form_hidden(self):
        form_params = FormParameters()
        form_params.add_field_by_attr_items([("name", "username"), ("type", "text")])
        form_params.add_field_by_attr_items([("name", "csrf_token"), ("type", "hidden")])

        form = URLEncodedForm(form_params)
        freq = FuzzableRequest(URL('http://www.w3af.com/'),
                               post_data=form,
                               method='PUT')
        m = PostDataMutant(freq)
        m.get_dc().set_token(('username', 0))

        self.assertFalse(self.plugin._should_inject(m))

        m.get_dc().set_token(('csrf_token', 0))
        self.assertTrue(self.plugin._should_inject(m))


class TestJSONPayloadIsValid(unittest.TestCase):
    def test_all_jsons_are_valid(self):
        loaded_payloads = 0

        for root, dirs, files in os.walk(deserialization.PAYLOADS):
            for file_name in files:
                if file_name.endswith(deserialization.PAYLOAD_EXTENSION):
                    json_str = file(os.path.join(root, file_name)).read()
                    data = json.loads(json_str)

                    self.assertIn('1', data)
                    self.assertIn('2', data)

                    self.assertIn('payload', data['1'])
                    self.assertIn('offsets', data['1'])

                    self.assertIn('payload', data['2'])
                    self.assertIn('offsets', data['2'])

                    for delay_len in [1, 2]:
                        for offset in data[str(delay_len)]['offsets']:
                            self.assertIsInstance(offset, int)

                            payload = base64.b64decode(data[str(delay_len)]['payload'])
                            self.assertGreater(len(payload), offset)

                    loaded_payloads += 1

        self.assertGreater(loaded_payloads, 0)


class TestExactDelay(unittest.TestCase):
    def test_get_payload(self):
        payload = {
            "1": {"payload": "Y3RpbWUKc2xlZXAKcDEKKEkxCnRwMgpScDMKLg==",
                  "offsets": [17]},
            "2": {"payload": "Y3RpbWUKc2xlZXAKcDEKKEkyMgp0cDIKUnAzCi4=",
                  "offsets": [17]}
        }

        ed = B64DeserializationExactDelay(payload)

        payload_1 = ed.get_string_for_delay(1)
        payload_22 = ed.get_string_for_delay(22)

        self.assertEqual(payload['1']['payload'], payload_1)
        self.assertEqual(payload['2']['payload'], payload_22)
