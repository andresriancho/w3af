"""
test_crawl_infrastructure.py

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
import time

from nose.plugins.attrib import attr

import w3af.core.data.kb.config as cf

from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.core.controllers.w3afCore import w3afCore
from w3af.core.controllers.ci.moth import get_moth_http


class TestTimeLimit(PluginTest):

    target_url = get_moth_http()

    _run_configs = {
        'basic': {
            'target': target_url,
            'plugins': {
                'crawl': (
                    PluginConfig('web_spider',),
                )
            }
        },
    }

    @attr('slow')
    @attr('ci_fails')
    def test_spider_with_time_limit(self):
        #
        #    First scan
        #
        cf.cf.save('max_discovery_time', 1)
        cfg = self._run_configs['basic']
        
        start_time = time.time()
        
        self._scan(self.target_url, cfg['plugins'])

        end_time = time.time()
        first_scan_time = end_time - start_time

        len_first_urls = len(self.kb.get_all_known_urls())
        self.assertGreater(len_first_urls, 500)
        self.assertLess(first_scan_time, 120)
        
        # Cleanup
        self.w3afcore.quit()
        self.kb.cleanup()
        self.w3afcore = w3afCore()
        
        #
        #    Second scan
        #
        cf.cf.save('max_discovery_time', 2)
        cfg = self._run_configs['basic']
        
        start_time = time.time()
        
        self._scan(self.target_url, cfg['plugins'])
        
        end_time = time.time()
        second_scan_time = end_time - start_time

        len_second_urls = len(self.kb.get_all_known_urls())
        self.assertGreater(len_second_urls, 900)
        self.assertGreater(len_second_urls, len_first_urls)
        self.assertLess(second_scan_time, 150)
        
        # The setup delta is the time it takes w3af to setup the scan, and
        # finish once the should_stop_scan method returns true. The 60 in the
        # next line is the initial scan time of 1 minute
        setup_delta = first_scan_time - 60
        
        # Scan should take at least the setup time, 2 minutes which is the time
        # delay and because the setup_delta might be a little bit off, we just
        # substract some seconds from it
        at_least_takes = setup_delta + 120 - 10
        
        self.assertGreater(second_scan_time, at_least_takes)
