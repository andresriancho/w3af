"""
test_csv_file.py

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
import os
import csv
import json

from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.dc.urlencoded_form import URLEncodedForm
from w3af.core.data.dc.headers import Headers
from w3af.core.data.parsers.doc.url import URL
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.data.fuzzer.mutants.querystring_mutant import QSMutant
from w3af.core.data.fuzzer.mutants.postdata_mutant import PostDataMutant
from w3af.core.data.request.fuzzable_request import FuzzableRequest


class TestCSVFile(PluginTest):

    OUTPUT_FILE = 'output-unittest.csv'

    target_url = get_moth_http('/audit/xss/simple_xss.py?text=1')

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'audit': (
                    PluginConfig(
                        'xss',
                         ('checkStored', True, PluginConfig.BOOL),
                         ('numberOfChecks', 3, PluginConfig.INT)),
                ),
                'crawl': (
                    PluginConfig(
                        'web_spider',
                        ('only_forward', True, PluginConfig.BOOL)),
                ),
                'output': (
                    PluginConfig(
                        'csv_file',
                        ('output_file', OUTPUT_FILE, PluginConfig.STR)),
                )
            },
        }
    }

    def test_found_xss(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        xss_vulns = self.kb.get('xss', 'xss')
        file_vulns = self._from_csv_get_vulns()

        self.assertEquals(
            set(sorted([v.get_url() for v in xss_vulns])),
            set(sorted([v.get_url() for v in file_vulns]))
        )

        self.assertEquals(
            set(sorted([v.get_method() for v in xss_vulns])),
            set(sorted([v.get_method() for v in file_vulns]))
        )

        self.assertEquals(
            set(sorted([v.get_id()[0] for v in xss_vulns])),
            set(sorted([v.get_id()[0] for v in file_vulns]))
        )

    def _from_csv_get_vulns(self):
        file_vulns = []
        vuln_reader = csv.reader(open(self.OUTPUT_FILE, 'rb'), delimiter=',',
                                 quotechar='|', quoting=csv.QUOTE_MINIMAL)

        for severity, name, method, uri, var, post_data, _id, desc in vuln_reader:
            mutant = create_mutant_from_params(method, uri, var, post_data)
            v = Vuln.from_mutant(name, desc, severity, json.loads(_id),
                                 'TestCase', mutant)
            file_vulns.append(v)

        return file_vulns

    def tearDown(self):
        try:
            os.remove(self.OUTPUT_FILE)
        except:
            pass


def create_mutant_from_params(method, uri, var, post_data):
    uri = URL(uri)

    if method.upper() == 'GET' and var in uri.querystring:
        MutantKlass = QSMutant
        headers = Headers()
    else:
        MutantKlass = PostDataMutant
        headers = Headers([('content-type', URLEncodedForm.ENCODING)])

    freq = FuzzableRequest.from_parts(uri, method=method,
                                      post_data=post_data, headers=headers)
    mutant = MutantKlass(freq)
    mutant.get_dc().set_token((var, 0))
    return mutant