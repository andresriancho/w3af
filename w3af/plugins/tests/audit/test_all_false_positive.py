"""
test_all_false_positive.py

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
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from nose.plugins.skip import SkipTest


class TestAllFP(PluginTest):

    target_url = 'http://moth/w3af/core/base_false_positive/'

    @attr('ci_fails')
    def test_false_positive(self):
        raise SkipTest('FIXME: This test takes too long to run.')

        audit_plugin_names = self.w3afcore.plugins.get_plugin_list('audit')

        for audit_plugin in audit_plugin_names:
            run_config = {
                'target': self.target_url,
                'plugins': {
                    'audit': (PluginConfig(audit_plugin),),
                    'crawl': (
                        PluginConfig(
                            'web_spider',
                             ('only_forward', True, PluginConfig.BOOL)),
                    )
                }
            }

            # I tried to do this in the right way, with nosetests test
            # generators, but they have a bug with unittest.TestCase
            self.setUp()

            target = run_config['target']
            plugins = run_config['plugins']
            self._scan(target, plugins)

            infos = [str(i) for i in self.kb.get_all_findings()]

            msg_i = 'audit.%s found a vulnerability in "%s"' % (audit_plugin,
                                                                ','.join(infos))
            self.assertEquals(len(infos), 0, msg_i)

            # I tried to do this in the right way, with nosetests test
            # generators, but they have a bug with unittest.TestCase
            self.tearDown()