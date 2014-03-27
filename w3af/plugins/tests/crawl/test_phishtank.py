"""
test_phishtank.py

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
import datetime
import re

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.plugins.tests.helper import PluginTest
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.url import URL
from w3af.core.data.constants.severity import MEDIUM


class TestPhishtank(PluginTest):

    safe_url = get_moth_http()
    phish_detail = 'http://www.phishtank.com/phish_detail.php?phish_id='

    def test_phishtank_no_match(self):
        phishtank_inst = self.w3afcore.plugins.get_plugin_inst('crawl',
                                                               'phishtank')
        
        phishtank_inst.crawl(FuzzableRequest(URL(self.safe_url)))
        vulns = self.kb.get('phishtank', 'phishtank')

        self.assertEqual(len(vulns), 0, vulns)

    def get_vulnerable_url(self, phishtank_inst):
        for line in file(phishtank_inst.PHISHTANK_DB):
            # <url>http://www.lucabrassi.com/wp/aol/index.htm</url>
            match = re.search('<url>(.*?)</url>', line)
            if match and 'CDATA' not in line:
                return match.group(1)

    def get_last_vulnerable_url(self, phishtank_inst):
        for line in reversed(file(phishtank_inst.PHISHTANK_DB).readlines()):
            # <url>http://www.lucabrassi.com/wp/aol/index.htm</url>
            match = re.search('<url>(.*?)</url>', line)
            if match and 'CDATA' not in line:
                return match.group(1)

    def test_phishtank_match(self):
        phishtank_inst = self.w3afcore.plugins.get_plugin_inst('crawl',
                                                               'phishtank')
        
        vuln_url = URL(self.get_vulnerable_url(phishtank_inst))
        phishtank_inst.crawl(FuzzableRequest(vuln_url))

        vulns = self.kb.get('phishtank', 'phishtank')

        self.assertEqual(len(vulns), 1, vulns)
        vuln = vulns[0]

        self.assertEqual(vuln.get_name(), 'Phishing scam')
        self.assertEqual(vuln.get_severity(), MEDIUM)
        self.assertEqual(vuln.get_url(), vuln_url)

    def test_xml_parsing(self):
        phishtank_inst = self.w3afcore.plugins.get_plugin_inst('crawl',
                                                               'phishtank')

        vuln_url_str = self.get_vulnerable_url(phishtank_inst)
        ptm_list = phishtank_inst._is_in_phishtank([vuln_url_str, ])
        self.assertEqual(len(ptm_list), 1, ptm_list)

        ptm = ptm_list[0]
        self.assertEqual(ptm.url.url_string, vuln_url_str)
        self.assertTrue(ptm.more_info_URL.url_string.startswith(self.phish_detail))

    def test_xml_parsing_last_url(self):
        phishtank_inst = self.w3afcore.plugins.get_plugin_inst('crawl',
                                                               'phishtank')

        vuln_url_str = self.get_last_vulnerable_url(phishtank_inst)
        ptm_list = phishtank_inst._is_in_phishtank([vuln_url_str, ])
        self.assertEqual(len(ptm_list), 1, ptm_list)

        ptm = ptm_list[0]
        self.assertEqual(ptm.url.url_string, URL(vuln_url_str).url_string)
        self.assertTrue(ptm.more_info_URL.url_string.startswith(self.phish_detail))
        
    def test_too_old_xml(self):
        phishtank_inst = self.w3afcore.plugins.get_plugin_inst('crawl',
                                                               'phishtank')

        # Example: <generated_at>2012-11-01T11:00:13+00:00</generated_at>
        generated_at_re = re.compile('<generated_at>(.*?)</generated_at>')
        mo = generated_at_re.search(file(phishtank_inst.PHISHTANK_DB).read())

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

            msg = 'The phishtank database is too old, in order to update it'\
                  ' please follow these steps:\n'\
                  'wget -q -O- --header\="Accept-Encoding: gzip" http://data.phishtank.com/data/online-valid/ | gunzip > w3af/plugins/crawl/phishtank/index.xml\n'\
                  'git commit -m "Updating phishtank database." w3af/plugins/crawl/phishtank/index.xml\n'\
                  'git push\n'
            self.assertTrue(time_delta.days < 30, msg)