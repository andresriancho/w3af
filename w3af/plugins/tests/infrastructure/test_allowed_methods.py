"""
test_allowed_methods.py

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
from nose.plugins.attrib import attr

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig


@attr('smoke')
class TestAllowedMethods(PluginTest):
    """
    Note that this is a smoke test because the code in allowed_methods calls
    custom/special methods on the remote server using ExtendedUrllib and that's
    something we want to make sure works.
    """
    modsecurity_url = 'http://modsecurity/'
    moth_url = get_moth_http()

    _run_configs = {
        'cfg': {
            'target': None,
            'plugins': {'infrastructure': (PluginConfig('allowed_methods'),)}
        }
    }

    def test_moth(self):
        """
        test_moth in test_allowed_methods, test the "default" configuration for
        Apache+PHP.
        """
        cfg = self._run_configs['cfg']
        self._scan(self.moth_url, cfg['plugins'])

        #
        #   We do have a custom configuration
        #
        infos = self.kb.get('allowed_methods', 'custom-configuration')

        self.assertEqual(len(infos), 1, infos)
        info = infos[0]

        msg = 'The remote Web server has a custom configuration, in which any'
        self.assertTrue(info.get_desc().startswith(msg))
        self.assertEqual(info.get_name(), 'Non existent methods default to GET')

        #
        #   Now lets check the other part
        #
        infos = self.kb.get('allowed_methods', 'methods')

        self.assertEqual(len(infos), 0, infos)

    @attr('ci_fails')
    def test_modsecurity(self):
        """
        test_modsecurity in test_allowed_methods, test a different
        configuration:
            RewriteEngine on
            RewriteCond %{THE_REQUEST} !^(POST|GET)\ /.*\ HTTP/1\.1$
            RewriteRule .* - [F]
        """
        cfg = self._run_configs['cfg']
        self._scan(self.modsecurity_url, cfg['plugins'])

        infos = self.kb.get('allowed_methods', 'custom-configuration')

        self.assertEqual(len(infos), 0, infos)