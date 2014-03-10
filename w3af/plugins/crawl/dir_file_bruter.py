"""
dir_file_bruter.py

Copyright 2009 Jon Rose

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

from itertools import repeat, izip

import w3af.core.controllers.output_manager as om

from w3af import ROOT_PATH

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404

from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import INPUT_FILE, BOOL
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.data.db.disk_set import DiskSet


class dir_file_bruter(CrawlPlugin):
    """
    Finds Web server directories and files by bruteforcing.

    :author: Jon Rose ( jrose@owasp.org )
    :author: Andres Riancho ( andres@bonsai-sec.com )
    :author: Tomas Velazquez
    """
    
    BASE_PATH = os.path.join(ROOT_PATH, 'plugins', 'crawl', 'dir_file_bruter')
    
    def __init__(self):
        CrawlPlugin.__init__(self)

        # User configured parameters
        self._dir_list = os.path.join(self.BASE_PATH, 'common_dirs_small.db')
        self._file_list = os.path.join(self.BASE_PATH, 'common_files_small.db')

        self._bf_directories = True
        self._bf_files = False
        self._be_recursive = False

        # Internal variables
        self._exec = True
        self._already_tested = DiskSet()

    def crawl(self, fuzzable_request):
        """
        Get the file and parse it.

        :param fuzzable_request: A fuzzable_request instance that contains
                               (among other things) the URL to test.
        """
        if not self._exec:
            raise RunOnce()
        else:
            domain_path = fuzzable_request.get_url().get_domain_path()

            # Should I run more than once?
            if not self._be_recursive:
                self._exec = False

            if domain_path not in self._already_tested:
                self._already_tested.add(domain_path)
                self._bruteforce_directories(domain_path)

    def _dir_name_generator(self, base_path):
        """
        Simple generator that returns the names of the directories and files to
        test. It extracts the information from the user configured wordlist
        parameter.

        @yields: (A string with the directory or file name,
                  a URL object with the dir or file name)
        """
        if self._bf_directories:
            for directory_name in file(self._dir_list):
                directory_name = directory_name.strip()

                # ignore comments and empty lines
                if directory_name and not directory_name.startswith('#'):
                    try:
                        dir_url = base_path.url_join(directory_name + '/')
                    except ValueError, ve:
                        msg = 'The "%s" line at "%s" generated an ' \
                              'invalid URL: %s'
                        om.out.debug(msg % (directory_name, self._dir_list, ve))
                    else:
                        yield directory_name, dir_url

        if self._bf_files:
            for file_name in file(self._file_list):
                file_name = file_name.strip()

                # ignore comments and empty lines
                if file_name and not file_name.startswith('#'):
                    try:
                        dir_url = base_path.url_join(file_name)
                    except ValueError, ve:
                        msg = 'The "%s" line at "%s" generated an ' \
                              'invalid URL: %s'
                        om.out.debug(msg % (file_name, self._file_list, ve))
                    else:
                        yield file_name, dir_url


    def _send_and_check(self, base_path, (directory_name, dir_url)):
        """
        Performs a GET and verifies that the response is not a 404.

        :return: None, data is stored in self.output_queue
        """
        try:
            http_response = self._uri_opener.GET(dir_url, cache=False)
        except:
            pass
        else:
            if is_404(http_response):
                return
            #
            #   Looking good, but lets see if this is a false positive
            #   or not...
            #
            dir_url = base_path.url_join(directory_name + rand_alnum(5) + '/')

            invalid_http_response = self._uri_opener.GET(dir_url,
                                                         cache=False)

            if is_404(invalid_http_response):
                #
                #    Good, the directory_name + rand_alnum(5) return a
                #    404, the original directory_name is not a false positive.
                #
                for fr in self._create_fuzzable_requests(http_response):
                    self.output_queue.put(fr)

                msg = 'dir_file_brute plugin found "%s" with HTTP response ' \
                      'code %s and Content-Length: %s.' \
                
                om.out.information(msg % (http_response.get_url(),
                                          http_response.get_code(),
                                          len(http_response.get_body())))

    def _bruteforce_directories(self, base_path):
        """
        :param base_path: The base path to use in the bruteforcing process,
                          can be something like http://host.tld/ or
                          http://host.tld/images/ .

        :return: None, the data is stored in self.output_queue
        """
        dir_name_generator = self._dir_name_generator(base_path)
        base_path_repeater = repeat(base_path)
        arg_iter = izip(base_path_repeater, dir_name_generator)

        self.worker_pool.map_multi_args(self._send_and_check, arg_iter,
                                           chunksize=20)

    def end(self):
        self._already_tested.cleanup()

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Wordlist to use in directory bruteforcing process.'
        o = opt_factory('dir_wordlist', self._dir_list, d, INPUT_FILE)
        ol.add(o)

        d = 'Wordlist to use in file bruteforcing process.'
        o = opt_factory('file_wordlist', self._file_list, d, INPUT_FILE)
        ol.add(o)

        d = 'If set to True, this plugin will bruteforce directories.'
        o = opt_factory('bf_directories', self._bf_directories, d, BOOL)
        ol.add(o)

        d = 'If set to True, this plugin will bruteforce files.'
        o = opt_factory('bf_files', self._bf_files, d, BOOL)
        ol.add(o)

        d = 'If set to True, this plugin will bruteforce all directories, not'\
            ' only the root directory.'
        h = 'WARNING: Enabling this will make the plugin send tens of thousands'\
            ' of requests.'
        o = opt_factory('be_recursive', self._be_recursive, d, BOOL, help=h)
        ol.add(o)

        return ol

    def set_options(self, option_list):
        """
        This method sets all the options that are configured using the user interface
        generated by the framework using the result of get_options().

        :param OptionList: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._dir_list = option_list['dir_wordlist'].get_value()
        self._file_list = option_list['file_wordlist'].get_value()
        self._bf_directories = option_list['bf_directories'].get_value()
        self._bf_files = option_list['bf_files'].get_value()
        self._be_recursive = option_list['be_recursive'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds directories and files on a web server by brute-forcing 
        their names using a wordlist.

        Given the large amount of time that this plugin can consume, by default,
        it will only try to identify directories in the current web resource, 
        ignoring the path that is sent as its input.

        Five configurable parameters exist:
            - dir_wordlist: The wordlist to be used in the directory bruteforce process.
            - file_wordlist: The wordlist to be used in the file bruteforce process.
            - bf_directories: If set to True, this plugin will bruteforce directories.
            - bf_files: If set to True, this plugin will bruteforce files.
            - be_recursive: If set to True, this plugin will bruteforce all
                            directories, not only the root directory.
        """
