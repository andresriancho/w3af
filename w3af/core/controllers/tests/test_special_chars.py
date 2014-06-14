"""
test_special_chars.py

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
from w3af.core.controllers.ci.moth import get_moth_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig


class TestSpecialChars(PluginTest):
    """
    This test verifies that a fix for the bug identified while scanning
    demo.testfire.net is still working as expected. The issue was that the
    site had a form that looked like:

    <form action="/xyz">
        <intput name="foo" value="bar+spam" type="hidden">
        <intput name="eggs" type="text">
        ...
    </form>

    And when trying to send a request to that form the "+" in the value
    was sent as %20. The input was an .NET's EVENTVALIDATION thus it was
    impossible to find any bugs in the "eggs" parameter.

    Please note that this is a functional test and a unittest (which does not
    verify that everything works as expected) can be found at test_form.py
    """
    target_url = get_moth_http('/core/encoding_spaces/')

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'audit': (PluginConfig('xss'),),
                'crawl': (
                    PluginConfig('web_spider',
                                 ('only_forward', True, PluginConfig.BOOL),),
                ),
            }
        }
    }

    def test_special_chars(self):
        cfg = self._run_configs['cfg']

        self._scan(cfg['target'], cfg['plugins'])
        
        xss_vulns = self.kb.get('xss', 'xss')
        self.assertEqual(len(xss_vulns), 2, xss_vulns)
