"""
test_scan_vulnerable_site.py

Copyright 2014 Andres Riancho

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

from w3af.plugins.tests.helper import PluginConfig


@attr('functional')
@attr('internet')
@attr('slow')
@attr('ci_fails')
class TestScanVulnerableSite(object):

    target_url = None

    _run_configs = {
        'cfg': {
            'plugins': {
                'crawl': (PluginConfig('web_spider',),),
                'audit': (PluginConfig('all'),),
                'grep': (PluginConfig('all'),),
            }
        }
    }

    EXPECTED_URLS = {}

    EXPECTED_VULNS = {()}

    def test_scan_vulnerable_site(self):
        if self.target_url is None:
            return

        cfg = self._run_configs['cfg']
        self._scan(self.target_url, cfg['plugins'])

        #self.assertAllURLsFound(self.EXPECTED_URLS)
        self.assertMostExpectedVulnsFound(self.EXPECTED_VULNS)