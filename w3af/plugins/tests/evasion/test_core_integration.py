"""
test_core_integration.py

Copyright 2012 Andres Riancho

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

from mock import MagicMock
from nose.plugins.attrib import attr

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.controllers.w3afCore import w3afCore
from w3af.core.data.parsers.doc.url import URL
from w3af.plugins.tests.helper import create_target_option_list


@attr('moth')
class TestCoreIntegration(unittest.TestCase):
    
    def setUp(self):
        self.w3afcore = w3afCore()

    def tearDown(self):
        self.w3afcore.quit()
            
    def test_send_mangled(self):
        
        self.w3afcore.plugins.set_plugins(['self_reference'], 'evasion')
        self.w3afcore.plugins.set_plugins(['sqli'], 'audit')
        
        target_opts = create_target_option_list(URL(get_moth_http()))
        self.w3afcore.target.set_options(target_opts)

        # Verify env and start the scan
        self.w3afcore.plugins.init_plugins()
        self.w3afcore.verify_environment()
        
        sref = self.w3afcore.plugins.plugins['evasion'][0]
        
        def return_arg(request):
            return request
        sref.modify_request = MagicMock(side_effect=return_arg)
        
        self.w3afcore.start()
        
        self.assertGreater(sref.modify_request.call_count, 15)