"""
url_fuzzer.py

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
from itertools import chain, repeat, izip

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.data.dc.headers import Headers
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.kb.info import Info
from w3af.core.data.request.fuzzable_request import FuzzableRequest


class url_fuzzer(CrawlPlugin):
    """
    Try to find backups, and other related files.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    _appendables = ('~', '.tar.gz', '.gz', '.7z', '.cab', '.tgz',
                    '.gzip', '.bzip2', '.inc', '.zip', '.rar', '.jar', '.java',
                    '.class', '.properties', '.bak', '.bak1', '.bkp', '.back',
                    '.backup', '.backup1', '.old', '.old1', '.$$$'
                    )
    _backup_exts = ('tar.gz', '7z', 'gz', 'cab', 'tgz', 'gzip',
                    'bzip2', 'zip', 'rar')
    _file_types = (
        'inc', 'fla', 'jar', 'war', 'java', 'class', 'properties',
        'bak', 'bak1', 'backup', 'backup1', 'old', 'old1', 'c', 'cpp',
        'cs', 'vb', 'phps', 'disco', 'ori', 'orig', 'original'
    )

    def __init__(self):
        CrawlPlugin.__init__(self)

        self._headers = None
        self._first_time = True
        self._fuzz_images = False
        self._seen = ScalableBloomFilter()

    def crawl(self, fuzzable_request, debugging_id):
        """
        Searches for new URLs using fuzzing.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        url = fuzzable_request.get_url()
        self._headers = Headers([('Referer', url.url_string)])

        if self._first_time:
            self._verify_head_enabled(url)
            self._first_time = False

        # First we need to delete fragments and query strings from URL.
        url = url.uri2url()

        # And we mark this one as a "do not return" URL, because the
        # core already found it using another technique.
        self._seen.add(url)

        self._verify_head_enabled(url)
        if self._head_enabled():
            response = self._uri_opener.HEAD(url, cache=True,
                                             headers=self._headers)
        else:
            response = self._uri_opener.GET(url, cache=True,
                                            headers=self._headers)

        if response.is_text_or_html() or self._fuzz_images:
            mutants_chain = chain(self._mutate_by_appending(url),
                                  self._mutate_path(url),
                                  self._mutate_file_type(url),
                                  self._mutate_domain_name(url))
            url_repeater = repeat(url)
            args = izip(url_repeater, mutants_chain)

            self.worker_pool.map_multi_args(self._do_request, args)

    def _do_request(self, url, mutant):
        """
        Perform a simple GET to see if the result is an error or not, and then
        run the actual fuzzing.
        """
        response = self._uri_opener.GET(mutant,
                                        cache=True,
                                        headers=self._headers)

        if is_404(response):
            return

        if response.get_code() in (403, 401, 301, 302, 500, 400):
            return

        # Create the fuzzable request and send it to the core
        fr = FuzzableRequest.from_http_response(response)
        self.output_queue.put(fr)

        #
        #   Save it to the kb (if new)!
        #
        if response.get_url() in self._seen:
            return

        if not response.get_url().get_file_name():
            return

        # Report only once
        self._seen.add(response.get_url())

        desc = 'A potentially interesting file was found at: "%s".'
        desc %= response.get_url()

        i = Info('Potentially interesting file', desc, response.id, self.get_name())
        i.set_url(response.get_url())

        kb.kb.append(self, 'files', i)
        om.out.information(i.get_desc())

    def _mutate_domain_name(self, url):
        """
        If the url is : "http://www.foobar.com/asd.txt" this method returns:
            - http://www.foobar.com/foobar.zip
            - http://www.foobar.com/foobar.rar
            - http://www.foobar.com/www.foobar.zip
            - http://www.foobar.com/www.foobar.rar
            - etc...

        :param url: A URL to transform.
        :return: A list of URL's that mutate the original url passed
                 as parameter.

        >>> from w3af.core.data.parsers.doc.url import URL
        >>> u = url_fuzzer()
        >>> url = URL('http://www.w3af.com/')
        >>> mutants = list(u._mutate_domain_name(url))
        >>> URL('http://www.w3af.com/www.tar.gz') in mutants
        True
        >>> URL('http://www.w3af.com/www.w3af.tar.gz') in mutants
        True
        >>> URL('http://www.w3af.com/www.w3af.com.tar.gz') in mutants
        True
        >>> len(mutants) > 20
        True

        """
        domain = url.get_domain()
        domain_path = url.get_domain_path()

        splitted_domain = domain.split('.')
        for i in xrange(len(splitted_domain)):
            filename = '.'.join(splitted_domain[0: i + 1])

            for extension in self._backup_exts:
                filename_ext = filename + '.' + extension

                domain_path_copy = domain_path.copy()
                domain_path_copy.set_file_name(filename_ext)
                yield domain_path_copy

    def _mutate_by_appending(self, url):
        """
        Adds something to the end of the url (mutate the file being requested)

        :param url: A URL to transform.
        :return: A list of URL's that mutate the original url passed
                 as parameter.

        >>> from w3af.core.data.parsers.doc.url import URL
        >>> u = url_fuzzer()
        >>> url = URL( 'http://www.w3af.com/' )
        >>> mutants = u._mutate_by_appending( url )
        >>> list(mutants)
        []

        >>> url = URL( 'http://www.w3af.com/foo.html' )
        >>> mutants = u._mutate_by_appending( url )
        >>> URL( 'http://www.w3af.com/foo.html~' ) in mutants
        True
        >>> len(list(mutants)) > 20
        True

        """
        if not url.url_string.endswith('/') and url.url_string.count('/') >= 3:
            #
            #   Only get here on these cases:
            #       - http://host.tld/abc
            #       - http://host.tld/abc/def.html
            #
            #   And not on these:
            #       - http://host.tld
            #       - http://host.tld/abc/
            #
            for to_append in self._appendables:
                url_copy = url.copy()
                filename = url_copy.get_file_name()
                filename += to_append
                url_copy.set_file_name(filename)
                yield url_copy

    def _mutate_file_type(self, url):
        """
        If the url is : "http://www.foobar.com/asd.txt" this method returns:
            - http://www.foobar.com/asd.zip
            - http://www.foobar.com/asd.tgz
            - etc...

        :param url: A URL to transform.
        :return: A list of URL's that mutate the original url passed as parameter.

        >>> from w3af.core.data.parsers.doc.url import URL
        >>> u = url_fuzzer()
        >>> list(u._mutate_file_type(URL('http://www.w3af.com/')))
        []

        >>> url = URL('http://www.w3af.com/foo.html')
        >>> mutants = list(u._mutate_file_type( url))
        >>> URL('http://www.w3af.com/foo.tar.gz') in mutants
        True
        >>> URL('http://www.w3af.com/foo.disco') in mutants
        True
        >>> len(mutants) > 20
        True

        """
        extension = url.get_extension()
        if extension:
            for filetype in chain(self._backup_exts, self._file_types):
                url_copy = url.copy()
                url_copy.set_extension(filetype)
                yield url_copy

    def _mutate_path(self, url):
        """
        Mutate the path instead of the file.

        :param url: A URL to transform.
        :return: A list of URL's that mutate the original url passed
                 as parameter.

        >>> from w3af.core.data.parsers.doc.url import URL
        >>> u = url_fuzzer()
        >>> url = URL( 'http://www.w3af.com/' )
        >>> list(u._mutate_path(url))
        []

        >>> url = URL( 'http://www.w3af.com/foo.html' )
        >>> list(u._mutate_path(url))
        []

        >>> url = URL('http://www.w3af.com/foo/bar.html' )
        >>> mutants = list(u._mutate_path(url))
        >>> URL('http://www.w3af.com/foo.tar.gz') in mutants
        True
        >>> URL('http://www.w3af.com/foo.old') in mutants
        True
        >>> URL('http://www.w3af.com/foo.zip') in mutants
        True
        """
        url_string = url.url_string

        if url_string.count('/') > 3:
            # Create the new path
            url_string = url_string[:url_string.rfind('/')]
            to_append_list = self._appendables
            for to_append in to_append_list:
                newurl = URL(url_string + to_append)
                yield newurl

    def _verify_head_enabled(self, url):
        """
        Verifies if the requested URL permits a HEAD request.
        This was saved inside the KB by the plugin allowed_methods

        :return : Sets self._head to the correct value, nothing is returned.
        """
        allowed_methods_infos = kb.kb.get('allowed_methods', 'methods')
        allowed_methods = []
        for info in allowed_methods_infos:
            allowed_methods.extend(info['methods'])
        
        if 'HEAD' in allowed_methods:
            self._head = True
        else:
            self._head = False

    def _head_enabled(self):
        return self._head

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Apply URL fuzzing to all URLs, including images, videos, zip, etc.'
        h = 'Don\'t change this unless you read the plugin code.'
        o = opt_factory('fuzz_images', self._fuzz_images, d, 'boolean', help=h)
        ol.add(o)

        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user interface
        generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._fuzz_images = options_list['fuzz_images'].get_value()

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins that should be run before the
        current one.
        """
        return ['infrastructure.allowed_methods']

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin will try to find new URL's based on the input. If the input
        is for example:
            - http://host.tld/a.html

        The plugin will request:
            - http://host.tld/a.html.tgz
            - http://host.tld/a.tgz
            ...
            - http://host.tld/a.zip

        If the response is different from the 404 page (whatever it may be,
        automatic detection is performed), then we have found a new URL. This
        plugin searches for backup files, source code, and other common extensions.

        One configurable parameter exist:
            - fuzz_images
        """
