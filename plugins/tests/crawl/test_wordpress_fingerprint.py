# coding: utf8
'''
test_wordpress_fingerprint.py

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
from plugins.tests.helper import PluginTest, PluginConfig
from core.data.misc.file_utils import days_since_file_update


class Testwordpress_fingerprint(PluginTest):

    wordpress_url = 'http://wordpress/'
    moth_url = 'http://moth/w3af/audit/'

    _run_configs = {
        'direct': {
            'target': wordpress_url,
            'plugins': {
        'crawl': (PluginConfig('wordpress_fingerprint',),)
            },
        },
        'crawl': {
            'target': moth_url,
            'plugins': {
        'crawl': (PluginConfig('wordpress_fingerprint',),
                  PluginConfig('web_spider',
                               ('only_forward', True, PluginConfig.BOOL)))

            },
        }
    }

    def test_find_version(self):
        cfg = self._run_configs['direct']
        self._scan(cfg['target'], cfg['plugins'])

        infos = self.kb.get('wordpress_fingerprint', 'info')

        self.assertEqual(len(infos), 4)

        for i in infos:
            self.assertEqual('Fingerprinted Wordpress version', i.get_name())

        descriptions = set([i.get_desc(with_id=False) for i in infos])
        expected_descriptions = set(
            ['WordPress version "3.4.1" found in the index header.',

             'WordPress version "3.4.1" found in the readme.html file.',

             'WordPress version "2.7.1" found from data.',

             'The sysadmin used WordPress version "3.4.1.tar.gz"'
             ' during the installation, which was found by matching'
             ' the contents of "http://wordpress/latest.tar.gz"'
             ' with the hashes of known releases. If the sysadmin'
             ' did not update wordpress, the current version will'
             ' still be the same.', ])
        self.assertEqual(descriptions, expected_descriptions)

    def test_todo(self):
        '''
        Please note that the version found by the data is 2.7.1 , this is because
        of an outdated data in wordpress_fingerprint.py , more specifically the
        WP_FINGERPRINT attribute.

        I should modify the plugin in order to use the XML file provided by the
        guys at wpscan.org:
        https://github.com/wpscanteam/wpscan/blob/master/data/wp_versions.xml
        '''
        self.assertTrue(False)

    def test_updated_release_db(self):

        wpfp_inst = self.w3afcore.plugins.get_plugin_inst('crawl',
                                                          'wordpress_fingerprint')

        wp_releases_file = wpfp_inst._release_db
        is_older = days_since_file_update(wp_releases_file, 30)

        msg = 'The releases.db database is too old. The following commands need'\
              ' to be run in order to update it:\n'\
              'cd plugins/crawl/wordpress_fingerprint/\n'\
              'python generate_release_db.py\n'\
              'svn commit -m "Updating wordpress release.db file." release.db\n'\
              'cd -'
        self.assertFalse(is_older, msg)
