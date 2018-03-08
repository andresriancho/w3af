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
from w3af.core.data.dc.cookie import Cookie
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.fuzzer.mutants.querystring_mutant import QSMutant
from w3af.core.data.fuzzer.mutants.postdata_mutant import PostDataMutant
from w3af.core.data.fuzzer.mutants.cookie_mutant import CookieMutant
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
        self.fuzzer_config = {'fuzz_cookies': True}

    def test_should_inject_empty_qs(self):
        self.url = URL('http://moth/?id=')
        freq = FuzzableRequest(self.url)

        mutant = QSMutant.create_mutants(freq, self.payloads, [],
                                         False, self.fuzzer_config)[0]

        self.assertTrue(self.plugin._should_inject(mutant, 'python'))

    def test_should_not_inject_qs_with_digit(self):
        self.url = URL('http://moth/?id=1')
        freq = FuzzableRequest(self.url)

        mutant = QSMutant.create_mutants(freq, self.payloads, [],
                                         False, self.fuzzer_config)[0]

        self.assertFalse(self.plugin._should_inject(mutant, 'python'))

    def test_should_not_inject_qs_with_b64(self):
        b64data = base64.b64encode('just some random b64 data here')
        self.url = URL('http://moth/?id=%s' % b64data)
        freq = FuzzableRequest(self.url)

        mutant = QSMutant.create_mutants(freq, self.payloads, [],
                                         False, self.fuzzer_config)[0]

        self.assertFalse(self.plugin._should_inject(mutant, 'python'))

    def test_should_inject_qs_with_b64_pickle(self):
        b64data = base64.b64encode(cPickle.dumps({'data': 'here',
                                                  'cookie': 'A' * 16}))
        self.url = URL('http://moth/?id=%s' % b64data)
        freq = FuzzableRequest(self.url)

        mutant = QSMutant.create_mutants(freq, self.payloads, [],
                                         False, self.fuzzer_config)[0]

        self.assertTrue(self.plugin._should_inject(mutant, 'python'))

    def test_should_not_inject_qs_with_b64_pickle_java(self):
        b64data = base64.b64encode(cPickle.dumps(1))
        self.url = URL('http://moth/?id=%s' % b64data)
        freq = FuzzableRequest(self.url)

        mutant = QSMutant.create_mutants(freq, self.payloads, [],
                                         False, self.fuzzer_config)[0]

        self.assertFalse(self.plugin._should_inject(mutant, 'java'))

    def test_should_inject_qs_with_pickle(self):
        pickle_data = cPickle.dumps(1)
        self.url = URL('http://moth/?id=%s' % pickle_data)
        freq = FuzzableRequest(self.url)

        mutant = QSMutant.create_mutants(freq, self.payloads, [],
                                         False, self.fuzzer_config)[0]

        self.assertTrue(self.plugin._should_inject(mutant, 'python'))

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

        self.assertFalse(self.plugin._should_inject(m, 'python'))

        m.get_dc().set_token(('csrf_token', 0))
        self.assertTrue(self.plugin._should_inject(m, 'python'))

    def test_should_inject_cookie_value(self):
        b64data = base64.b64encode(cPickle.dumps({'data': 'here',
                                                  'cookie': 'A' * 16}))

        url = URL('http://moth/')
        cookie = Cookie('foo=%s' % b64data)
        freq = FuzzableRequest(url, cookie=cookie)

        mutant = CookieMutant.create_mutants(freq, self.payloads, [],
                                             False, self.fuzzer_config)[0]

        self.assertTrue(self.plugin._should_inject(mutant, 'python'))

    def test_should_not_inject_random_binary(self):
        self.url = URL('http://moth/?id=%s' % '\x00\x01\x02')
        freq = FuzzableRequest(self.url)

        mutant = QSMutant.create_mutants(freq, self.payloads, [],
                                         False, self.fuzzer_config)[0]

        self.assertFalse(self.plugin._should_inject(mutant, 'java'))


class TestJSONPayloadIsValid(unittest.TestCase):
    def test_all_jsons_are_valid(self):
        loaded_payloads = 0

        for root, dirs, files in os.walk(deserialization.PAYLOADS):

            # Ignore helpers used for creating the nodejs payloads
            if 'node_modules' in root:
                continue

            for file_name in files:

                # Ignore helpers used for creating the nodejs payloads
                if file_name in ('package-lock.json', 'package.json'):
                    continue

                if file_name.endswith(deserialization.PAYLOAD_EXTENSION):
                    json_str = file(os.path.join(root, file_name)).read()
                    data = json.loads(json_str)

                    self.assertIn('1', data, file_name)
                    self.assertIn('2', data, file_name)

                    self.assertIn('payload', data['1'], file_name)
                    self.assertIn('offsets', data['1'], file_name)

                    self.assertIn('payload', data['2'], file_name)
                    self.assertIn('offsets', data['2'], file_name)

                    self.assertGreater(len(data['1']['offsets']), 0)
                    self.assertGreater(len(data['2']['offsets']), 0)

                    for delay_len in [1, 2]:
                        for offset in data[str(delay_len)]['offsets']:
                            self.assertIsInstance(offset, int, file_name)

                            payload = base64.b64decode(data[str(delay_len)]['payload'])
                            self.assertGreater(len(payload), offset, file_name)

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

    def test_get_payload_all(self):
        for root, dirs, files in os.walk(deserialization.PAYLOADS):

            # Ignore helpers used for creating the nodejs payloads
            if 'node_modules' in root:
                continue

            for file_name in files:

                # Ignore helpers used for creating the nodejs payloads
                if file_name in ('package-lock.json', 'package.json'):
                    continue

                if file_name.endswith(deserialization.PAYLOAD_EXTENSION):
                    json_str = file(os.path.join(root, file_name)).read()
                    payload = json.loads(json_str)

                    ed = B64DeserializationExactDelay(payload)

                    try:
                        payload_1 = ed.get_string_for_delay(1)
                        payload_22 = ed.get_string_for_delay(22)
                    except Exception, e:
                        msg = 'Raised exception "%s" on "%s"'
                        args = (e, file_name)
                        self.assertTrue(False, msg % args)

                    #file('1', 'w').write(base64.b64decode(payload['1']['payload']))
                    #file('2', 'w').write(base64.b64decode(payload_1))

                    self.assertEqual(payload['1']['payload'], payload_1, file_name)
                    self.assertEqual(payload['2']['payload'], payload_22, file_name)
