"""
test_fileupload.py

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
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.core.controllers.ci.php_moth import get_php_moth_http


class TestFileUpload(PluginTest):

    file_upload_url = get_php_moth_http('/audit/file_upload/')

    _run_configs = {
        'cfg': {
            'target': file_upload_url,
            'plugins': {
                'audit': (
                    PluginConfig(
                        'file_upload', ('extensions',
                                        'gif,html,bmp,jpg,png,txt',
                                        PluginConfig.LIST)
                    ),)
            }, }
    }

    def test_reported_file_uploads(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        fu_vulns = self.kb.get('file_upload', 'file_upload')
        self.assertEquals(1, len(fu_vulns))

        v = fu_vulns[0]
        self.assertEquals(v.get_name(), 'Insecure file upload')
        self.assertEquals(str(v.get_url().get_domain_path()),
                          self.file_upload_url)
