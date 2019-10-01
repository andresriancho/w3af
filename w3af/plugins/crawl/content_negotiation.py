"""
content_negotiation.py

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
import os
import re
import Queue

from itertools import izip, repeat

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af import ROOT_PATH
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.dc.headers import Headers
from w3af.core.data.kb.info import Info
from w3af.core.data.request.fuzzable_request import FuzzableRequest


class content_negotiation(CrawlPlugin):
    """
    Use content negotiation to find new resources.
    :author: Andres Riancho ((andres.riancho@gmail.com))
    """

    def __init__(self):
        CrawlPlugin.__init__(self)

        # User configured parameters
        self._wordlist = os.path.join(ROOT_PATH, 'plugins', 'crawl',
                                      'content_negotiation',
                                      'common_filenames.db')

        # Internal variables
        self._already_tested_dir = ScalableBloomFilter()
        self._already_tested_resource = ScalableBloomFilter()

        # Test queue
        #
        # Note that this queue can have ~20 items in the worse case scenario
        # it is not a risk to store it all in memory
        self._to_bruteforce = Queue.Queue()

        # Run N checks to verify if content negotiation is enabled
        self._tries_left = 3
        self._content_negotiation_enabled = None

    def crawl(self, fuzzable_request, debugging_id):
        """
        1- Check if HTTP server is vulnerable
        2- Exploit using FuzzableRequest
        3- Perform bruteforce for each new directory

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                (among other things) the URL to test.
        """
        if self._content_negotiation_enabled is False:
            return

        con_neg_result = self._verify_content_neg_enabled(fuzzable_request)

        if con_neg_result is None:
            # I can't say if it's vulnerable or not (yet), save the current
            # directory to be included in the bruteforcing process, and
            # return.
            self._to_bruteforce.put(fuzzable_request.get_url())
            return

        if con_neg_result is False:
            # Not vulnerable, nothing else to do.
            self.clear_queue()
            return

        if con_neg_result is True:
            # Now we can test if we find new resources!
            self._find_new_resources(fuzzable_request)

            # and we can also perform a bruteforce:
            self._to_bruteforce.put(fuzzable_request.get_url())
            self._bruteforce()

    def clear_queue(self):
        while not self._to_bruteforce.empty():
            try:
                self._to_bruteforce.get_nowait()
            except Queue.Empty:
                continue

    def _find_new_resources(self, fuzzable_request):
        """
        Based on a request like http://host.tld/backup.php , this method will
        find files like backup.zip , backup.old, etc. Using the content
        negotiation technique.

        :return: A list of new fuzzable requests.
        """
        # Get the file name
        filename = fuzzable_request.get_url().get_file_name()
        if filename == '':
            return
        else:
            # The thing here is that I've found that if these files exist in
            # the directory:
            # - backup.asp.old
            # - backup.asp
            #
            # And I request "/backup" , then both are returned. So I'll request
            #  the "leftmost" filename.
            filename = filename.split('.')[0]

            # Now I simply perform the request:
            alternate_resource = fuzzable_request.get_url().url_join(filename)
            original_headers = fuzzable_request.get_headers()

            if alternate_resource not in self._already_tested_resource:
                self._already_tested_resource.add(alternate_resource)

                _, alternates = self._request_and_get_alternates(
                    alternate_resource,
                    original_headers)

                # And create the new fuzzable requests
                url = fuzzable_request.get_url()
                for fr in self._create_new_fuzzable_requests(url, alternates):
                    self.output_queue.put(fr)

    def _bruteforce(self):
        """
        Use some common words to bruteforce file names and find new resources.
        This process is done only once for every new directory.

        :return: A list of new fuzzable requests.
        """
        wl_url_generator = self._wordlist_url_generator()
        args_generator = izip(wl_url_generator, repeat(Headers()))

        # Send the requests using threads:
        for base_url, alternates in self.worker_pool.map_multi_args(
                self._request_and_get_alternates,
                args_generator,
                chunksize=10):

            for fr in self._create_new_fuzzable_requests(base_url, alternates):
                self.output_queue.put(fr)

    def _wordlist_url_generator(self):
        """
        Generator that returns alternate URLs to test by combining the following
        sources of information:
            - URLs in self._bruteforce
            - Words in the bruteforce wordlist file
        """
        while not self._to_bruteforce.empty():
            try:
                bf_url = self._to_bruteforce.get_nowait()
            except Queue.Empty:
                break
            else:
                directories = bf_url.get_directories()

                for directory_url in directories:
                    if directory_url not in self._already_tested_dir:
                        self._already_tested_dir.add(directory_url)

                        for word in file(self._wordlist):
                            word = word.strip()
                            yield directory_url.url_join(word)

    def _request_and_get_alternates(self, alternate_resource, headers):
        """
        Performs a request to an alternate resource, using the fake accept
        trick in order to retrieve the list of alternates, which is then
        returned.

        :return: A tuple with:
                    - alternate_resource parameter (unmodified)
                    - a list of strings containing the alternates.
        """
        headers['Accept'] = 'w3af/bar'
        response = self._uri_opener.GET(alternate_resource, headers=headers)

        alternates, _ = response.get_headers().iget('alternates')

        # And I parse the result
        if alternates:
            # An alternates header looks like this:
            # alternates: {"backup.php.bak" 1 {type application/x-trash} {length 0}},
            #             {"backup.php.old" 1 {type application/x-trash} {length 0}},
            #             {"backup.tgz" 1 {type application/x-gzip} {length 0}},
            #             {"backup.zip" 1 {type application/zip} {length 0}}
            #
            # All in the same line.
            return alternate_resource, re.findall('"(.*?)"', alternates)

        else:
            # something failed
            return alternate_resource, []

    def _create_new_fuzzable_requests(self, base_url, alternates):
        """
        With a list of alternate files, I create new fuzzable requests

        :param base_url: http://host.tld/some/dir/
        :param alternates: ['backup.old', 'backup.asp']

        :return: A list of fuzzable requests.
        """
        for alternate in alternates:
            # Get the new resource
            full_url = base_url.url_join(alternate)
            response = self._uri_opener.GET(full_url)

            if not is_404(response):
                yield FuzzableRequest(full_url)

    def _verify_content_neg_enabled(self, fuzzable_request):
        """
        Checks if the remote website is vulnerable or not. Saves the result in
        self._content_negotiation_enabled , because we want to perform this test
        only once.

        :return: True if vulnerable.
        """
        if self._content_negotiation_enabled is not None:
            # The test was already performed, we return the old response
            return self._content_negotiation_enabled

        # We perform the test, for this we need a URL that has a filename,
        # URLs that don't have a filename can't be used for this.
        filename = fuzzable_request.get_url().get_file_name()
        if filename == '':
            return None

        filename = filename.split('.')[0]

        # Now I simply perform the request:
        alternate_resource = fuzzable_request.get_url().url_join(filename)
        headers = fuzzable_request.get_headers()
        headers['Accept'] = 'w3af/bar'
        response = self._uri_opener.GET(alternate_resource, headers=headers)

        if response.get_headers().icontains('alternates'):
            # Even if there is only one file, with an unique mime type,
            # the content negotiation will return an alternates header.
            # So this is pretty safe.

            # Save the result as an info in the KB, for the user to see it:
            desc = ('HTTP Content negotiation is enabled in the remote web'
                    ' server. This could be used to bruteforce file names'
                    ' and find new resources')

            i = Info('HTTP Content Negotiation enabled', desc, response.id,
                     self.get_name())
            i.set_url(response.get_url())

            kb.kb.append(self, 'content_negotiation', i)
            om.out.information(i.get_desc())

            # Save the result internally
            self._content_negotiation_enabled = True
            return self._content_negotiation_enabled

        msg = 'The remote Web server has Content Negotiation disabled'
        om.out.information(msg)

        # I want to perform this test a couple of times... so I only
        # return False if that "couple of times" is empty
        self._tries_left -= 1
        if self._tries_left == 0:
            # Save the False result internally
            self._content_negotiation_enabled = False
        else:
            # None tells the plugin to keep trying with the next URL
            return None

        return self._content_negotiation_enabled

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        d1 = 'Word list to use in the file name brute forcing process.'
        o1 = opt_factory('wordlist', self._wordlist, d1, 'string')

        ol = OptionList()
        ol.add(o1)
        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        wordlist = options_list['wordlist'].get_value()
        if os.path.exists(wordlist):
            self._wordlist = wordlist

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin uses HTTP content negotiation to find new resources.

        The plugin has three distinctive phases:

            - Identify if the web server has content negotiation enabled.

            - For every resource found by any other plugin, perform a request
            to find new related resources. For example, if another plugin finds
            "index.php", this plugin will perform a request for "/index" with
            customized headers that will return a list of all files that have
            "index" as the file name.

            - Perform a brute force attack in order to find new resources.

        One configurable parameter exists:
        
            - wordlist: The wordlist to be used in the bruteforce process.

        The first reference to this technique was written by Stefano Di Paola
        in his blog (http://www.wisec.it/sectou.php?id=4698ebdc59d15).
        """
