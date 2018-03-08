"""
test_audit.py

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
import unittest
import httpretty

from mock import patch, call

import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.core_helpers.consumers.audit import audit
from w3af.core.controllers.w3afCore import w3afCore
from w3af.core.controllers.exceptions import ScanMustStopException
from w3af.plugins.audit.xss import xss
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL


class TestAuditConsumer(unittest.TestCase):

    def tearDown(self):
        kb.kb.cleanup()

    @httpretty.activate
    def test_teardown_with_must_stop_exception(self):
        w3af_core = w3afCore()

        xss_instance = xss()
        xss_instance.set_url_opener(w3af_core.uri_opener)
        xss_instance.set_worker_pool(w3af_core.worker_pool)

        audit_plugins = [xss_instance]

        audit_consumer = audit(audit_plugins, w3af_core)
        audit_consumer.start()

        url = 'http://w3af.org/?id=1'

        httpretty.register_uri(httpretty.GET, url,
                               body='hello world',
                               content_type='application/html')

        url = URL(url)
        fr = FuzzableRequest(url)

        # This will trigger a few HTTP requests to the target URL which will
        # also initialize all the xss plugin internals to be able to run end()
        # later.
        audit_consumer.in_queue_put(fr)
        kb.kb.add_fuzzable_request(fr)

        # Now that xss.audit() was called, we want to simulate network errors
        # that will put the uri opener in a state where it always answers with
        # ScanMustStopException
        w3af_core.uri_opener._stop_exception = ScanMustStopException('mock')

        # And now we just call terminate() which injects the poison pill and will
        # call teardown, which should call xss.end(), which should try to send HTTP
        # requests, which will raise a ScanMustStopException
        with patch('w3af.core.controllers.core_helpers.consumers.audit.om.out') as om_mock:
            audit_consumer.terminate()

            msg = ('Spent 0.00 seconds running xss.end() until a scan must'
                   ' stop exception was raised.')
            self.assertIn(call.debug(msg), om_mock.mock_calls)
