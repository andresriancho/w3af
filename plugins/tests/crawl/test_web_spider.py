# coding: utf8
'''
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
'''
import urllib2
import re

from nose.plugins.skip import SkipTest
from nose.plugins.attrib import attr

from plugins.tests.helper import PluginTest, PluginConfig


class TestWebSpider(PluginTest):

    follow_links_url = 'http://moth/w3af/crawl/web_spider/follow_links/'
    dir_get_url = 'http://moth/w3af/crawl/web_spider/a/b/c/d/'
    encoding_url = 'http://moth/w3af/core/encoding/'
    relative_url = 'http://moth/w3af/crawl/web_spider/relativeRegex.html'

    wivet = 'http://wivet/'

    _run_configs = {
        'basic': {
            'target': None,
            'plugins': {
                'crawl': (
                    PluginConfig('web_spider',
                                 ('only_forward', True, PluginConfig.BOOL),
                                 (
                                 'ignoreRegex', '.*pages/100.php.*', PluginConfig.STR)),
                )
            }
        },
    }

    @attr('smoke')
    def test_spider_found_urls(self):
        cfg = self._run_configs['basic']
        self._scan(self.follow_links_url + '1.html', cfg['plugins'])
        expected_urls = (
            '3.html', '4.html', '',
            'd%20f/index.html', '2.html', 'a%20b.html',
            'a.gif', 'd%20f/', '1.html'
        )
        urls = self.kb.get_all_known_urls()
        self.assertEquals(
            set(str(u) for u in urls),
            set((self.follow_links_url + end) for end in expected_urls)
        )

    @attr('smoke')
    def test_spider_urls_with_strange_charsets(self):
        cfg = self._run_configs['basic']
        self._scan(self.encoding_url + 'index.html', cfg['plugins'])
        
        # pylint: disable=E1101
        # Pylint fails to detect the object types that come out of the KB            
        urls = self.kb.get_all_known_urls()
        
        expected = (
            u'', u'index.html',
            # Japanese
            u'euc-jp/', u'euc-jp/jap1.php', u'euc-jp/jap2.php',
            # UTF8
            u'utf-8/', u'utf-8/vúlnerable.php', u'utf-8/é.html', u'utf-8/改.php',
            # Russian
            u'utf-8/russian.html',
            # Hebrew
            u'windows-1255/', u'windows-1255/heb1.php', u'windows-1255/heb2.php',
            # Encoded spaces
            'spaces/form_input_plus_POST.html', 'spaces/queryxpath.php',
            'spaces/', 'spaces/start end.html', 'spaces/form_input_plus_GET.html',
            'spaces/foo.html'
        )
        self.assertEquals(
            set([(self.encoding_url + u) for u in expected]),
            set([u.url_string for u in urls])
        )

    def test_spider_relative_urls_found_with_regex(self):
        raise SkipTest('FIXME: Need to test this feature!')
        self.relative_url

    def test_spider_traverse_directories(self):
        raise SkipTest('FIXME: Need to test this feature!')
        self.dir_get_url

    def test_wivet(self):
        clear_wivet()

        cfg = self._run_configs['basic']
        self._scan(self.wivet, cfg['plugins'])

        #
        #    First, check that w3af identified all the URLs we want:
        #
        ALL_WIVET_URLS = set((
            '10_17d77.php', '11_1f2e4.php', '1_12c3b.php', '11_2d3ff.php',
            '12_2a2cf.php', '12_3a2cf.php', '1_25e2a.php', '13_10ad3.php',
            '13_25af3.php', '14_1eeab.php', '15_1c95a.php', '16_1b14f.php',
            '16_2f41a.php', '17_143ef.php', '17_2da76.php', '18_1a2f3.php',
            '19_1f52a.php', '19_2e3a2.php', '20_1e833.php', '21_1f822.php',
            '2_1f84b.php', '2_2b7a3.php', '3_16e1a.php', '3_2cc42.php',
            '3_3fadc.php', '3_45589.php', '3_5befd.php', '3_6ff22.php',
            '3_7e215.php', '4_1c3f8.php', '5_1e4d2.php', '6_14b3c.php',
            '7_16a9c.php', '8_1b6e1.php', '8_2b6f1.php', '9_10ee31.php',
            '9_11ee31.php', '9_12ee31.php', '9_13ee31.php', '9_14ee31.php',
            '9_15ee31.php', '9_16ee31.php', '9_17ee31.php', '9_18ee31.php',
            '9_19ee31.php', '9_1a1b2.php', '9_20ee31.php', '9_21ee31.php',
            '9_22ee31.php', '9_23ee31.php', '9_24ee31.php', '9_25ee31.php',
            '9_26dd2e.php', '9_2ff21.php', '9_3a2b7.php', '9_4b82d.php',
            '9_5ee31.php', '9_6ee31.php', '9_7ee31.php', '9_8ee31.php',
            '9_9ee31.php', '12_1a2cf.php'
        ))

        #
        #    FIXME: At some point this should be reduced to an empty set()
        #
        W3AF_FAILS = set((
            '9_16ee31.php', '9_9ee31.php', '9_18ee31.php', '9_11ee31.php',
            '9_20ee31.php', '9_25ee31.php', '9_15ee31.php',
            '9_8ee31.php', '9_17ee31.php', '9_13ee31.php', '9_19ee31.php',
            '9_14ee31.php', '19_2e3a2.php', '17_143ef.php', '9_23ee31.php',
            '9_12ee31.php', '9_5ee31.php', '9_6ee31.php', '9_22ee31.php',
            '11_2d3ff.php', '17_2da76.php', '18_1a2f3.php', '9_24ee31.php',
            '9_7ee31.php', '9_10ee31.php', '9_21ee31.php',
        ))

        EXPECTED_URLS = ALL_WIVET_URLS - W3AF_FAILS

        inner_pages = 'innerpages/'

        urls = self.kb.get_all_known_urls()
        self.assertEquals(
            set(str(u) for u in urls if inner_pages in str(
                u) and str(u).endswith('.php')),
            set((self.wivet + inner_pages + end) for end in EXPECTED_URLS)
        )

        #
        #    And now, verify that w3af used only one session to identify these
        #    wivet links.
        #
        stats = extract_all_stats()
        self.assertEquals(len(stats), 1, stats)

        coverage = get_coverage_for_scan_id(stats[0][0])
        self.assertEqual(coverage, 51)


def clear_wivet():
    '''
    Utility function that will clear all the previous stats from my wivet
    instance, very helpful for performing analysis of the stats after the
    scan ends.
    '''
    clear_url = 'http://wivet/offscanpages/remove-all-stats.php?sure=yes'

    response = urllib2.urlopen(clear_url)
    html = response.read()

    assert 'Done!' == html, html


def extract_all_stats():
    '''
    :return: A list with all the stats generated during this scan
    '''
    stats_url = 'http://wivet/offscanpages/statistics/'
    response = urllib2.urlopen(stats_url)

    index_page = response.read()

    result = []

    for match_str in re.findall('<a href="(.*?).dat">', index_page):
        scan_stat_url = 'http://wivet/offscanpages/statistics/'
        scan_stat_url += match_str + '.dat'
        response = urllib2.urlopen(scan_stat_url)
        result.append((match_str, response.read()))

    return result


def get_coverage_for_scan_id(scan_id):
    specific_stats_url = 'http://wivet/offscanpages/statistics.php?id=%s'

    response = urllib2.urlopen(specific_stats_url % scan_id)
    html = response.read()

    match_obj = re.search('<span id="coverage">%(.*?)</span>', html)
    if match_obj is not None:
        return int(match_obj.group(1))

    return None
