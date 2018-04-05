# coding: utf8
"""
test_webspider.py

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
import urllib2
import re
import os

import w3af.core.data.kb.config as cf

from nose.plugins.skip import SkipTest
from nose.plugins.attrib import attr

from w3af import ROOT_PATH
from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse
from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.controllers.ci.wivet import get_wivet_http
from w3af.core.controllers.misc_settings import EXCLUDE
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers.utils.form_id_matcher_list import FormIDMatcherList


class TestWebSpider(PluginTest):

    follow_links_url = get_moth_http('/crawl/web_spider/test_case_01/')
    dir_get_url = 'http://moth/w3af/crawl/web_spider/a/b/c/d/'
    encoding_url = get_moth_http('/core/encoding')
    relative_url = 'http://moth/w3af/crawl/web_spider/relativeRegex.html'

    wivet = get_wivet_http()

    _run_configs = {
        'basic': {
            'target': None,
            'plugins': {
                'crawl': (
                    PluginConfig('web_spider',

                                 ('only_forward', True, PluginConfig.BOOL),

                                 ('ignore_regex',
                                  '.*logout.php*',
                                  PluginConfig.STR)),
                )
            }
        },
    }

    def generic_scan(self, config, base_directory, start_url, expected_files):
        self._scan(start_url, config['plugins'])

        # Add the webroot to the list of expected files
        expected_files.append('')
        expected_urls = set(URL(base_directory).url_join(end).url_string for end
                            in expected_files)

        # pylint: disable=E1101
        # Pylint fails to detect the object types that come out of the KB
        urls = self.kb.get_all_known_urls()
        found_urls = set(str(u).decode('utf-8') for u in urls)

        self.assertEquals(found_urls, expected_urls)

    @attr('smoke')
    def test_spider_found_urls(self):
        config = self._run_configs['basic']
        expected_files = ['1.html', '2.html', '3.html', '4.html',
                          'd%20f/index.html', 'a%20b.html', 'd%20f/',]
        start_url = self.follow_links_url

        self.generic_scan(config, self.follow_links_url,
                          start_url, expected_files)

    def test_utf8_urls(self):
        config = self._run_configs['basic']
        expected_files = [u'vúlnerable.py',
                          u'é.py',
                          u'改.py',
                          u'проверка.py']
        start_url = self.encoding_url + '_utf8/'

        self.generic_scan(config, start_url, start_url, expected_files)

    def test_euc_jp_urls(self):
        config = self._run_configs['basic']
        expected_files = [u'raw-qs-jp.py',
                          u'qs-jp.py']
        start_url = self.encoding_url + '_euc-jp/'

        self.generic_scan(config, start_url, start_url, expected_files)

    def test_spider_relative_urls_found_with_regex(self):
        raise SkipTest('FIXME: Need to test this feature!')

    def test_spider_traverse_directories(self):
        raise SkipTest('FIXME: Need to test this feature!')

    def test_wivet(self):
        clear_wivet()

        cfg = self._run_configs['basic']
        self._scan(self.wivet, cfg['plugins'])

        #
        #    First, check that w3af identified all the URLs we want:
        #
        ALL_WIVET_URLS = {'10_17d77.php', '11_1f2e4.php', '1_12c3b.php',
                          '11_2d3ff.php', '12_2a2cf.php', '12_3a2cf.php',
                          '1_25e2a.php', '13_10ad3.php', '13_25af3.php',
                          '14_1eeab.php', '15_1c95a.php', '16_1b14f.php',
                          '16_2f41a.php', '17_143ef.php', '17_2da76.php',
                          '18_1a2f3.php', '19_1f52a.php', '19_2e3a2.php',
                          '20_1e833.php', '21_1f822.php', '2_1f84b.php',
                          '2_2b7a3.php', '3_16e1a.php', '3_2cc42.php',
                          '3_3fadc.php', '3_45589.php', '3_5befd.php',
                          '3_6ff22.php', '3_7e215.php', '4_1c3f8.php',
                          '5_1e4d2.php', '6_14b3c.php', '7_16a9c.php',
                          '8_1b6e1.php', '8_2b6f1.php', '9_10ee31.php',
                          '9_11ee31.php', '9_12ee31.php', '9_13ee31.php',
                          '9_14ee31.php', '9_15ee31.php', '9_16ee31.php',
                          '9_17ee31.php', '9_18ee31.php', '9_19ee31.php',
                          '9_1a1b2.php', '9_20ee31.php', '9_21ee31.php',
                          '9_22ee31.php', '9_23ee31.php', '9_24ee31.php',
                          '9_25ee31.php', '9_26dd2e.php', '9_2ff21.php',
                          '9_3a2b7.php', '9_4b82d.php', '9_5ee31.php',
                          '9_6ee31.php', '9_7ee31.php', '9_8ee31.php',
                          '9_9ee31.php', '12_1a2cf.php'}

        #
        #    FIXME: At some point this should be reduced to an empty set()
        #
        W3AF_FAILS = {'9_16ee31.php', '9_9ee31.php', '9_18ee31.php',
                      '9_11ee31.php', '9_20ee31.php', '9_25ee31.php',
                      '9_15ee31.php', '9_8ee31.php', '9_17ee31.php',
                      '9_13ee31.php', '9_19ee31.php', '9_14ee31.php',
                      '19_2e3a2.php', '17_143ef.php', '9_23ee31.php',
                      '9_12ee31.php', '9_5ee31.php', '9_6ee31.php',
                      '9_22ee31.php', '11_2d3ff.php', '17_2da76.php',
                      '18_1a2f3.php', '9_24ee31.php', '9_7ee31.php',
                      '9_10ee31.php', '9_21ee31.php',

                      # These were added to the fails group after #2104
                      '15_1c95a.php', '6_14b3c.php', '8_1b6e1.php',
                      '14_1eeab.php', '8_2b6f1.php'}

        EXPECTED_URLS = ALL_WIVET_URLS - W3AF_FAILS

        inner_pages = 'innerpages/'

        urls = self.kb.get_all_known_urls()

        found = set(str(u) for u in urls if inner_pages in str(u) and str(u).endswith('.php'))
        expected = set((self.wivet + inner_pages + end) for end in EXPECTED_URLS)

        self.assertEquals(found, expected)

        #
        #    And now, verify that w3af used only one session to identify these
        #    wivet links.
        #
        stats = extract_all_stats()
        self.assertEquals(len(stats), 1)

        coverage = get_coverage_for_scan_id(stats[0][0])
        # TODO: Sometimes coverage is 44 and sometimes it is 42!
        # https://github.com/andresriancho/w3af/issues/2309
        self.assertEqual(coverage, 42)


def clear_wivet():
    """
    Utility function that will clear all the previous stats from my wivet
    instance, very helpful for performing analysis of the stats after the
    scan ends.
    """
    clear_url = get_wivet_http('/offscanpages/remove-all-stats.php?sure=yes')

    response = urllib2.urlopen(clear_url)
    html = response.read()

    assert 'Done!' in html, html


def extract_all_stats():
    """
    :return: A list with all the stats generated during this scan
    """
    stats_url = get_wivet_http('/offscanpages/statistics.php')
    response = urllib2.urlopen(stats_url)

    index_page = response.read()

    result = []
    SCAN_ID_RE = '<a href="statistics\.php\?id=(.*?)">'
    SCAN_STATS = get_wivet_http('/offscanpages/statistics.php?id=')

    for scan_id in re.findall(SCAN_ID_RE, index_page):
        scan_stat_url = SCAN_STATS + scan_id
        response = urllib2.urlopen(scan_stat_url)
        result.append((scan_id, response.read()))

    return result


def get_coverage_for_scan_id(scan_id):
    specific_stats_url = get_wivet_http('/offscanpages/statistics.php?id=%s')

    response = urllib2.urlopen(specific_stats_url % scan_id)
    html = response.read()

    match_obj = re.search('<span id="coverage">%(.*?)</span>', html)
    if match_obj is not None:
        return int(match_obj.group(1))

    return None


class TestRelativePathsIn404(PluginTest):
    """
    This test reproduces the issue #5834 which generates an endless crawl loop

    :see: https://github.com/andresriancho/w3af/issues/5834
    """
    target_url = 'http://mock/'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'crawl': (PluginConfig('web_spider'),)}
        }
    }

    TEST_ROOT = os.path.join(ROOT_PATH, 'plugins', 'tests', 'crawl',
                             'web_spider', '5834')

    GALERIA_HTML = file(os.path.join(TEST_ROOT, 'galeria-root.html')).read()
    INDEX_HTML = file(os.path.join(TEST_ROOT, 'index.html')).read()

    MOCK_RESPONSES = [MockResponse(re.compile('http://mock/galeria/.*'),
                                   GALERIA_HTML),
                      MockResponse('http://mock/', 'Thanks.', method='POST'),
                      MockResponse('http://mock/', INDEX_HTML)]

    def test_crawl_404_relative(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        # Define the expected/desired output
        expected_files = ['',
                          '/galeria/',
                          '/i18n/setlang/',
                          '/reserva/resumen/']
        expected_urls = set(URL(self.target_url).url_join(end).url_string for end
                            in expected_files)

        # pylint: disable=E1101
        # Pylint fails to detect the object types that come out of the KB
        urls = self.kb.get_all_known_urls()
        found_urls = set(str(u).decode('utf-8') for u in urls)

        self.assertEquals(found_urls, expected_urls)


class TestDeadLock(PluginTest):
    """
    This test reproduces a lock that I've found while debugging #5834, as far as
    I know, it has nothing to do with #5834 itself.

    I tried, but was unable to make this test fail when the dead-lock is found,
    instead when the dead-lock is found the test will "hang", CI will timeout,
    and in your workstation you'll have to manually kill it.
    """
    target_url = 'http://mock/'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'crawl': (PluginConfig('web_spider'),)}
        }
    }

    TEST_ROOT = os.path.join(ROOT_PATH, 'plugins', 'tests', 'crawl',
                             'web_spider', '5834')

    INDEX_HTML = file(os.path.join(TEST_ROOT, 'index.html')).read()

    MOCK_RESPONSES = [MockResponse('http://mock/', INDEX_HTML),
                      MockResponse('http://mock/', 'Thanks.', method='POST')]

    def test_no_lock(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])


class TestFormExclusions(PluginTest):
    """
    This is an integration test for form exclusions

    :see: https://github.com/andresriancho/w3af/issues/15161
    """
    target_url = 'http://mock/'

    scan_config = {
        'target': target_url,
        'plugins': {'crawl': (PluginConfig('web_spider'),)}
    }

    MOCK_RESPONSES = [MockResponse('http://mock/',
                                   '<html>'
                                   ''
                                   '<form action="/out/" method="POST">'
                                   '<input name="x" /></form>'
                                   ''
                                   '<form action="/in/" method="POST">'
                                   '<input name="x" /></form>'
                                   ''
                                   '</html>'),
                      MockResponse('http://mock/out/', 'Thanks.', method='POST'),
                      MockResponse('http://mock/in/', 'Thanks.', method='POST')]

    def test_form_exclusions(self):
        user_value = '[{"action": "/out.*"}]'
        cf.cf.save('form_id_list', FormIDMatcherList(user_value))
        cf.cf.save('form_id_action', EXCLUDE)

        self._scan(self.scan_config['target'],
                   self.scan_config['plugins'])

        # Define the expected/desired output
        expected_files = ['',
                          '/in/']
        expected_urls = set(URL(self.target_url).url_join(end).url_string for end
                            in expected_files)

        # pylint: disable=E1101
        # Pylint fails to detect the object types that come out of the KB
        urls = self.kb.get_all_known_urls()
        found_urls = set(str(u).decode('utf-8') for u in urls)

        self.assertEquals(found_urls, expected_urls)

        # revert any changes to the default so we don't affect other tests
        cf.cf.save('form_id_list', FormIDMatcherList('[]'))
        cf.cf.save('form_id_action', EXCLUDE)
