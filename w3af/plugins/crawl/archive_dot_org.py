"""
archive_dot_org.py

Copyright 2006 Andres Riancho

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
import re
from itertools import izip, repeat

import w3af.core.controllers.output_manager as om
from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.misc.is_private_site import is_private_site
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.data.request.fuzzable_request import FuzzableRequest


class archive_dot_org(CrawlPlugin):
    """
    Search archive.org to find new pages in the target site.

    :author: Andres Riancho (andres.riancho@gmail.com)
    :author: Darren Bilby, thanks for the good idea!
    """

    ARCHIVE_START_URL = 'http://web.archive.org/web/*/%s'
    INTERESTING_URLS_RE = '<a href="(http://web\.archive\.org/web/\d*?/https?://%s/.*?)"'
    NOT_IN_ARCHIVE = '<p>Wayback Machine doesn&apos;t have that page archived.</p>'

    def __init__(self):
        CrawlPlugin.__init__(self)

        # Internal variables
        self._already_crawled = ScalableBloomFilter()
        self._already_verified = ScalableBloomFilter()

        # User configured parameters
        self._max_depth = 3

    def crawl(self, fuzzable_request, debugging_id):
        """
        Does a search in archive.org and searches for links on the html. Then
        searches those URLs in the target site. This is a time machine !

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        domain = fuzzable_request.get_url().get_domain()

        if is_private_site(domain):
            msg = 'There is no point in searching archive.org for "%s"'\
                  ' because it is a private site that will never be indexed.'
            om.out.information(msg % domain)
            raise RunOnce(msg)

        # Initial check to verify if domain in archive
        start_url = self.ARCHIVE_START_URL % fuzzable_request.get_url()
        start_url = URL(start_url)
        http_response = self._uri_opener.GET(start_url, cache=True)

        if self.NOT_IN_ARCHIVE in http_response.body:
            msg = 'There is no point in searching archive.org for "%s"'
            msg += ' because they are not indexing this site.'
            om.out.information(msg % domain)
            raise RunOnce(msg)

        references = self._spider_archive(
            [start_url, ], self._max_depth, domain)
        self._analyze_urls(references)

    def _analyze_urls(self, references):
        """
        Analyze which references are cached by archive.org

        :return: A list of query string objects for the URLs that are in
                 the cache AND are in the target web site.
        """
        real_urls = []

        # Translate archive.org URL's to normal URL's
        for url in references:
            url = url.url_string[url.url_string.index('http', 1):]
            real_urls.append(URL(url))

        real_urls = list(set(real_urls))

        if len(real_urls):
            om.out.debug('Archive.org cached the following pages:')
            for u in real_urls:
                om.out.debug('- %s' % u)
        else:
            om.out.debug('Archive.org did not find any pages.')

        # Verify if they exist in the target site and add them to
        # the result if they do. Send the requests using threads:
        self.worker_pool.map(self._exists_in_target, real_urls)

    def _spider_archive(self, url_list, max_depth, domain):
        """
        Perform a classic web spidering process.

        :param url_list: The list of URL strings
        :param max_depth: The max link depth that we have to follow.
        :param domain: The domain name we are checking
        """
        # Start the recursive spidering
        res = []

        def spider_worker(url, max_depth, domain):
            if url in self._already_crawled:
                return []

            self._already_crawled.add(url)

            try:
                http_response = self._uri_opener.GET(url, cache=True)
            except:
                return []

            # Filter the ones we need
            url_regex_str = self.INTERESTING_URLS_RE % domain
            matched_urls = re.findall(url_regex_str, http_response.body)
            new_urls = [URL(u) for u in matched_urls]
            new_urls = [u.remove_fragment() for u in new_urls]
            new_urls = set(new_urls)

            # Go recursive
            if max_depth - 1 > 0:
                if new_urls:
                    res.extend(new_urls)
                    res.extend(self._spider_archive(new_urls,
                                                    max_depth - 1,
                                                    domain))
            else:
                msg = 'Some sections of the archive.org site were not analyzed'
                msg += ' because of the configured max_depth.'
                om.out.debug(msg)
                return new_urls

        args = izip(url_list, repeat(max_depth), repeat(domain))
        self.worker_pool.map_multi_args(spider_worker, args)

        return list(set(res))

    def _exists_in_target(self, url):
        """
        Check if a resource still exists in the target web site.

        :param url: The resource to verify.
        :return: None, the result is stored in self.output_queue
        """
        if url in self._already_verified:
            return

        self._already_verified.add(url)

        response = self._uri_opener.GET(url, cache=True)

        if not is_404(response):
            msg = 'The URL: "%s" was found at archive.org and is'\
                  ' STILL AVAILABLE in the target site.'
            om.out.debug(msg % url)

            fr = FuzzableRequest(response.get_uri())
            self.output_queue.put(fr)
        else:
            msg = 'The URL: "%s" was found at archive.org and was'\
                  ' DELETED from the target site.'
            om.out.debug(msg % url)

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Maximum recursion depth for spidering process'
        h = 'The plugin will spider the archive.org site related to the target'\
            ' site with the maximum depth specified in this parameter.'
        o = opt_factory('max_depth', self._max_depth, d, 'integer', help=h)
        ol.add(o)

        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._max_depth = options_list['max_depth'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin does a search in archive.org and parses the results. It
        then uses the results to find new URLs in the target site. This plugin
        is a time machine!
        """
