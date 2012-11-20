'''
test_phishtank.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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
'''
import datetime
import re

import core.data.constants.severity as severity

from plugins.tests.helper import PluginTest, PluginConfig


class TestPhishtank(PluginTest):

    safe_url = 'http://moth/'
    vuln_url_1 = 'http://www.i-fotbal.eu/'
    vuln_url_2 = 'http://190.16.196.11/web/update.html'
    phish_detail = 'http://www.phishtank.com/phish_detail.php?phish_id='

    _run_configs = {
        'cfg': {
            'target': None,
            'plugins': {'crawl': (PluginConfig('phishtank'),)}
        }
    }

    def test_phishtank_no_match(self):
        cfg = self._run_configs['cfg']
        self._scan(self.safe_url, cfg['plugins'])

        vulns = self.kb.get('phishtank', 'phishtank')

        self.assertEqual(len(vulns), 0, vulns)

    def test_phishtank_match(self):
        cfg = self._run_configs['cfg']
        self._scan(self.vuln_url_1, cfg['plugins'])

        vulns = self.kb.get('phishtank', 'phishtank')

        self.assertEqual(len(vulns), 1, vulns)
        vuln = vulns[0]

        self.assertEqual(vuln.get_name(), 'Phishing scam')
        self.assertEqual(vuln.get_severity(), severity.MEDIUM)
        self.assertTrue(vuln.get_url().url_string.startswith(self.vuln_url_1),
                        vuln.get_url())

    def test_xml_parsing_1(self):
        phishtank_inst = self.w3afcore.plugins.get_plugin_inst('crawl',
                                                               'phishtank')

        ptm_list = phishtank_inst._is_in_phishtank([self.vuln_url_1, ])
        self.assertEqual(len(ptm_list), 1, ptm_list)

        ptm = ptm_list[0]
        self.assertTrue(ptm.url.url_string.startswith(self.vuln_url_1))
        self.assertTrue(
            ptm.more_info_URL.url_string.startswith(self.phish_detail))

    def test_xml_parsing_2(self):
        phishtank_inst = self.w3afcore.plugins.get_plugin_inst('crawl',
                                                               'phishtank')

        ptm_list = phishtank_inst._is_in_phishtank([self.vuln_url_2, ])
        self.assertEqual(len(ptm_list), 1, ptm_list)

        ptm = ptm_list[0]
        self.assertTrue(ptm.url.url_string.startswith(self.vuln_url_2))
        self.assertTrue(
            ptm.more_info_URL.url_string.startswith(self.phish_detail))

    def test_too_old_xml(self):
        phishtank_inst = self.w3afcore.plugins.get_plugin_inst('crawl',
                                                               'phishtank')

        # Example: <generated_at>2012-11-01T11:00:13+00:00</generated_at>
        generated_at_re = re.compile('<generated_at>(.*?)</generated_at>')
        mo = generated_at_re.search(file(phishtank_inst._phishtank_DB).read())

        if mo is None:
            self.assertTrue(False, 'Error while parsing XML file.')
        else:
            # Example: 2012-11-01T11:00:13+00:00
            time_fmt = '%Y-%m-%dT%H:%M:%S+00:00'
            generated_time = mo.group(1)
            gen_date_time = datetime.datetime.strptime(
                generated_time, time_fmt)
            gen_date = gen_date_time.date()

            today_date = datetime.date.today()

            time_delta = today_date - gen_date

            msg = 'The phishtank database is too old.'
            self.assertTrue(time_delta.days < 30, msg)
