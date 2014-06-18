"""
test_file_upload.py

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
from w3af.core.controllers.ci.php_moth import get_php_moth_http
from w3af.plugins.tests.helper import PluginConfig, ExecExploitTest
from w3af.core.data.kb.vuln_templates.file_upload_template import FileUploadTemplate


class TestFileUploadShell(ExecExploitTest):

    file_upload_url = get_php_moth_http('/audit/file_upload/trivial/')

    _run_configs = {
        'cfg': {
            'target': file_upload_url,
            'plugins': {
                'crawl': (
                    PluginConfig(
                        'web_spider',
                        ('only_forward', True, PluginConfig.BOOL)),
                ),
                'audit': (
                    PluginConfig(
                        'file_upload', ('extensions',
                                        'gif,html,bmp,jpg,png,txt',
                                        PluginConfig.LIST)
                    ),)
            }, }
    }

    def test_found_exploit_file_upload(self):
        # Run the scan
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('file_upload', 'file_upload')
        self.assertEquals(1, len(vulns))
        
        vuln = vulns[0]
        
        self.assertEquals("Insecure file upload", vuln.get_name())

        vuln_to_exploit_id = vuln.get_id()
        self._exploit_vuln(vuln_to_exploit_id, 'file_upload')

    def test_from_template(self):
        fut = FileUploadTemplate()

        base_url = get_php_moth_http('/audit/file_upload/trivial/')

        options = fut.get_options()
        options['url'].set_value(base_url + 'uploader.php')
        options['data'].set_value('uploadedfile=&MAX_FILE_SIZE=10000000')
        options['file_vars'].set_value('uploadedfile')
        options['file_dest'].set_value(base_url + '/uploads/')
        options['vulnerable_parameter'].set_value('uploadedfile')
        fut.set_options(options)

        fut.store_in_kb()
        vuln = self.kb.get(*fut.get_kb_location())[0]
        vuln_to_exploit_id = vuln.get_id()
        
        self._exploit_vuln(vuln_to_exploit_id, 'file_upload')

    def test_from_template_534(self):
        fut = FileUploadTemplate()

        base_url = get_php_moth_http('/audit/file_upload/strange_extension_534/')

        options = fut.get_options()
        options['url'].set_value(base_url + 'uploader.534')
        options['data'].set_value('uploadedfile=&MAX_FILE_SIZE=10000000')
        options['file_vars'].set_value('uploadedfile')
        options['file_dest'].set_value(get_php_moth_http('/audit/file_upload/trivial/uploads/'))
        options['vulnerable_parameter'].set_value('uploadedfile')
        fut.set_options(options)

        fut.store_in_kb()
        vuln = self.kb.get(*fut.get_kb_location())[0]
        vuln_to_exploit_id = vuln.get_id()

        self._exploit_vuln(vuln_to_exploit_id, 'file_upload')