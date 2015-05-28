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
from cStringIO import StringIO

from lxml import etree

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.data.kb.tests.test_vuln import MockVuln
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.db.history import HistoryItem
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.core.data.dc.headers import Headers
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.url.HTTPRequest import HTTPRequest


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
        vuln_url_re = re.compile('<li>Vulnerable URL: <a href="(.*?)">')
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


class TestHTMLRendering(PluginTest):

    CONTEXT = {'target_urls': ['http://w3af.com/', 'http://w3af.com/blog'],
               'target_domain': 'w3af.com',
               'enabled_plugins': {'audit': ['xss'],
                                   'crawl': ['web_spider']},
               'findings': [MockVuln('SQL injection', None, 'High', 1, 'sqli'),
                            MockVuln('XSS-2', None, 'Medium', [], 'xss'),
                            MockVuln('XSS-3', None, 'Low', [], 'xss'),
                            MockVuln('XSS-4', None, 'Information', 4, 'xss')],
               'debug_log': [('Fri Mar 13 14:11:58 2015', 'debug', 'Log 1' * 40),
                             ('Fri Mar 13 14:11:59 2015', 'debug', 'Log 2'),
                             ('Fri Mar 13 14:11:59 2015', 'error', 'Log 3' * 5)],
               'known_urls': [URL('http://w3af.com'),
                              URL('http://w3af.com/blog'),
                              URL('http://w3af.com/oss')]}

    def setUp(self):
        super(TestHTMLRendering, self).setUp()
        self.plugin = self.w3afcore.plugins.get_plugin_inst('output',
                                                            'html_file')

        HistoryItem().init()

        url = URL('http://w3af.com/a/b/c.php')
        request = HTTPRequest(url, data='a=1')
        hdr = Headers([('Content-Type', 'text/html')])
        res = HTTPResponse(200, '<html>', hdr, url, url)
        h1 = HistoryItem()
        h1.request = request
        res.set_id(1)
        h1.response = res
        h1.save()

        url = URL('http://w3af.com/foo.py')
        request = HTTPRequest(url, data='text=xss')
        hdr = Headers([('Content-Type', 'text/html')])
        res = HTTPResponse(200, '<html>empty</html>', hdr, url, url)
        h1 = HistoryItem()
        h1.request = request
        res.set_id(4)
        h1.response = res
        h1.save()

    def test_render(self):
        output = StringIO()
        template = file(self.plugin._template, 'r')

        result = self.plugin._render_html_file(template, self.CONTEXT, output)

        self.assertTrue(result)

        output.seek(0)
        file(os.path.expanduser(self.plugin._output_file_name), 'w').write(output.read())