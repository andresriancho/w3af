"""
test_html_file.py

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
import re

from lxml import etree

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.data.kb.tests.test_vuln import MockVuln
from w3af.core.data.parsers.url import URL
from w3af.plugins.tests.helper import PluginTest, PluginConfig


class TestHTMLOutput(PluginTest):

    target_url = get_moth_http('/audit/xss/')
    OUTPUT_FILE = 'output-unittest.html'

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
                        'html_file',
                        ('output_file', OUTPUT_FILE, PluginConfig.STR)),
                )
            },
        }
    }

    def test_found_xss(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        xss_vulns = self.kb.get('xss', 'xss')
        file_vulns = self._from_html_get_vulns()

        self.assertGreaterEqual(len(xss_vulns), 2)

        self.assertEquals(
            set(sorted([v.get_url() for v in xss_vulns])),
            set(sorted([v.get_url() for v in file_vulns]))
        )
        
        self._validate_xhtml()

    def _from_html_get_vulns(self):
        vuln_url_re = re.compile('<b>URL:</b> (.*?)<br />')
        vulns = []

        for line in file(self.OUTPUT_FILE):

            mo = vuln_url_re.search(line)
            if mo:
                url = URL(mo.group(1))
                v = MockVuln('TestCase', None, 'High', 1, 'plugin')
                v.set_url(url)
                vulns.append(v)

        return vulns

    def _validate_xhtml(self):
        parser = etree.XMLParser()

        def generate_msg(parser):
            msg = 'XHTML parsing errors:\n'
            for error in parser.error_log:
                msg += '\n    %s (line: %s, column: %s)' % (error.message,
                                                            error.line,
                                                            error.column)
            return msg

        try:
            parser = etree.XML(file(self.OUTPUT_FILE).read(), parser)
        except etree.XMLSyntaxError:
            self.assertTrue(False, generate_msg(parser))
        else:
            if hasattr(parser, 'error_log'):
                self.assertFalse(len(parser.error_log), generate_msg(parser))
        
    def tearDown(self):
        super(TestHTMLOutput, self).tearDown()
        try:
            os.remove(self.OUTPUT_FILE)
        except:
            pass
