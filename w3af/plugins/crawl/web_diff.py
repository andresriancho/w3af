"""
web_diff.py

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

import w3af.core.controllers.output_manager as om
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import BOOL, STRING, LIST
from w3af.core.data.options.option_types import URL as URL_OPTION_TYPE
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest


class web_diff(CrawlPlugin):
    """
    Compare a local directory with a remote URL path.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        CrawlPlugin.__init__(self)

        # Internal variables
        self._first = True
        self._start_path = None

        self._not_exist_remote = []
        self._exist_remote = []

        self._not_eq_content = []
        self._eq_content = []

        # Configuration
        self._ban_url = ['asp', 'jsp', 'php']
        self._content = True
        self._local_dir = ''
        self._remote_url_path = URL('http://host.tld/')

    @runonce(exc_class=RunOnce)
    def crawl(self, fuzzable_request, debugging_id):
        """
        GET's local files one by one until done.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                     (among other things) the URL to test.
        """
        if self._local_dir and self._remote_url_path:
            os.path.walk(self._local_dir, self._compare_dir, None)
            self._generate_report()
        else:
            msg = 'web_diff plugin: You need to configure a local directory'\
                  ' and a remote URL to use in the diff process.'
            raise BaseFrameworkException(msg)

    def _generate_report(self):
        """
        Generates a report based on:
            - self._not_exist_remote
            - self._not_eq_content
            - self._exist_remote
            - self._eq_content
        """
        if len(self._exist_remote):
            msg = 'The following files exist in the local directory and in the'\
                  ' remote server:'
            om.out.information(msg)
            for file_name in self._exist_remote:
                om.out.information('- ' + file_name)

        if len(self._eq_content):
            msg = 'The following files exist in the local directory and in the'\
                  ' remote server and their contents match:'
            om.out.information(msg)
            for file_name in self._eq_content:
                om.out.information('- ' + file_name)

        if len(self._not_exist_remote):
            msg = 'The following files exist in the local directory and do NOT'\
                  ' exist in the remote server:'
            om.out.information(msg)
            for file_name in self._not_exist_remote:
                om.out.information('- ' + file_name)

        if len(self._not_eq_content):
            msg = 'The following files exist in the local directory and in the'\
                  ' remote server but their contents don\'t match:'
            om.out.information(msg)
            for file_name in self._not_eq_content:
                om.out.information('- ' + file_name)

        exist = len(self._exist_remote)
        total = len(self._exist_remote) + len(self._not_exist_remote)
        file_stats = '%s of %s' % (exist, total)
        om.out.information('Match files: ' + file_stats)

        if self._content:
            eq_content = len(self._eq_content)
            total = len(self._eq_content) + len(self._not_eq_content)
            content_stats = '%s of %s' % (eq_content, total)
            om.out.information('Match contents: ' + content_stats)

    def _compare_dir(self, arg, directory, flist):
        """
        This function is the callback function called from os.path.walk, python's
        help says:

        walk(top, func, arg)
            Directory tree walk with callback function.

            For each directory in the directory tree rooted at top (including top
            itself, but excluding '.' and '..'), call func(arg, dirname, fnames).
            dirname is the name of the directory, and fnames a list of the names of
            the files and subdirectories in dirname (excluding '.' and '..').  func
            may modify the fnames list in-place (e.g. via del or slice assignment),
            and walk will only recurse into the subdirectories whose names remain in
            fnames; this can be used to implement a filter, or to impose a specific
            order of visiting.  No semantics are defined for, or required of, arg,
            beyond that arg is always passed to func.  It can be used, e.g., to pass
            a filename pattern, or a mutable object designed to accumulate
            statistics.  Passing None for arg is common.

        """
        if self._first:
            self._first = False
            self._start_path = directory

        relative_dir = directory.replace(self._start_path, '')
        if relative_dir and not relative_dir.endswith('/'):
            relative_dir += '/'

        remote_root = self._remote_url_path
        remote_root_with_local_path = remote_root.url_join(relative_dir)

        for fname in flist:
            if os.path.isfile(directory + os.path.sep + fname):

                url = remote_root_with_local_path.url_join(fname)
                response = self._uri_opener.GET(url, cache=True)

                if not is_404(response):
                    if response.is_text_or_html():
                        fr = FuzzableRequest(response.get_url())
                        self.output_queue.put(fr)

                    path = '%s%s%s' % (directory, os.path.sep, fname)
                    self._check_content(response, path)
                    self._exist_remote.append(url)
                else:
                    self._not_exist_remote.append(url)

    def _check_content(self, response, file_name):
        """
        Check if the contents match.
        """
        if self._content:
            if file_name.count('.'):
                extension = os.path.splitext(file_name)[1].replace('.', '')

                if extension in self._ban_url:
                    return

                try:
                    local_content = open(file_name, 'r').read()
                except:
                    om.out.debug('Failed to open file: "%s".' % file_name)
                else:
                    if local_content == response.get_body():
                        self._eq_content.append(response.get_url())
                    else:
                        self._not_eq_content.append(response.get_url())

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'When comparing, also compare the content of files.'
        o = opt_factory('content', self._content, d, BOOL)
        ol.add(o)

        d = 'The local directory used in the comparison.'
        o = opt_factory('local_dir', self._local_dir, d, STRING)
        ol.add(o)

        d = 'The remote directory used in the comparison.'
        o = opt_factory(
            'remote_url_path', self._remote_url_path, d, URL_OPTION_TYPE)
        ol.add(o)

        d = 'When comparing content of two files, ignore files with these'\
            'extensions.'
        o = opt_factory('banned_ext', self._ban_url, d, LIST)
        ol.add(o)

        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user interface
        generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        url = options_list['remote_url_path'].get_value()
        self._remote_url_path = url.get_domain_path()

        local_dir = options_list['local_dir'].get_value()
        if os.path.isdir(local_dir):
            self._local_dir = local_dir
        else:
            msg = 'Error in user configuration: "%s" is not a directory.'
            raise BaseFrameworkException(msg % local_dir)

        self._content = options_list['content'].get_value()
        self._ban_url = options_list['banned_ext'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin tries to do a diff of two directories, a local and a remote
        one. The idea is to mimic the functionality implemented by the linux
        command "diff" when invoked with two directories.

        Four configurable parameter exist:
            - local_dir
            - remote_url_path
            - banned_ext
            - content

        This plugin will read the file list inside "local_dir", and for each file
        it will request the same filename from the "remote_url_path", matches and
        failures are recorded and saved.

        The content of both files is checked only if "content" is set to True
        and the file extension isn't in the "banned_ext" list.

        The "banned_ext" list should be used to ban script extensions like ASP,
        PHP, etc.
        """
