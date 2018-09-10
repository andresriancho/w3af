"""
file_upload.py

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

from itertools import repeat, izip
from collections import deque
from threading import RLock

from w3af import ROOT_PATH

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.controllers.output_manager as om
import w3af.core.data.constants.severity as severity
import w3af.core.data.parsers.parser_cache as parser_cache

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.controllers.misc.io import NamedStringIO
from w3af.core.controllers.exceptions import BaseFrameworkException

from w3af.core.data.constants.file_templates.file_templates import get_template_with_payload
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.data.kb.vuln import Vuln


class file_upload(AuditPlugin):
    """
    Uploads a file and then searches for the file inside all known directories.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    TEMPLATE_DIR = os.path.join(ROOT_PATH, 'core', 'data', 'constants', 'file_templates')

    MAX_BRUTEFORCE_FINDS = 250

    UPLOAD_PATHS = ['uploads',
                    'upload',
                    'up',
                    'files',
                    'file',
                    'user',
                    'content',
                    'images',
                    'documents',
                    'docs',
                    'downloads',
                    'download',
                    'down',
                    'public',
                    'pub',
                    'private']

    def __init__(self):
        AuditPlugin.__init__(self)

        # Internal attributes
        self._urls_recently_tested = deque(maxlen=30)
        self._urt_lock = RLock()

        # User configured
        self._extensions = ['gif', 'html', 'bmp', 'jpg', 'png', 'txt']

    def audit(self, freq, orig_response, debugging_id):
        """
        Searches for file upload vulns.

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        if freq.get_method().upper() != 'POST' or not freq.get_file_vars():
            return

        # Unique payload for the files we upload
        payload = rand_alnum(239)

        for file_parameter in freq.get_file_vars():
            for extension in self._extensions:

                _, file_content, file_name = get_template_with_payload(extension, payload)

                # Only file handlers are passed to the create_mutants functions
                named_stringio = NamedStringIO(file_content, file_name)
                mutants = create_mutants(freq, [named_stringio],
                                         fuzzable_param_list=[file_parameter])

                for mutant in mutants:
                    mutant.uploaded_file_name = file_name
                    mutant.extension = extension
                    mutant.file_content = file_content
                    mutant.file_payload = payload

                self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                              mutants,
                                              self._analyze_result,
                                              debugging_id=debugging_id)

    def _analyze_result(self, mutant, mutant_response):
        """
        Analyze results of the _send_mutant method.

        In this case, check if the file was uploaded to any of the known
        directories, or one of the "default" ones like "upload" or "files".
        """
        if self._has_bug(mutant):
            return

        self._find_files_by_parsing(mutant, mutant_response)
        self._find_files_by_bruteforce(mutant, mutant_response)

    def _find_files_by_parsing(self, mutant, mutant_response):
        """
        Parse the HTTP response and find our file.

        Take into account that the file name might have been changed (we do not care)
        if the extension remains the same then we're happy.

        :param mutant: The request used to upload the file
        :param mutant_response: The HTTP response associated with the file upload
        :return: None
        """
        try:
            doc_parser = parser_cache.dpc.get_document_parser_for(mutant_response)
        except BaseFrameworkException:
            # Failed to find a suitable parser for the document
            return

        parsed_refs, re_refs = doc_parser.get_references()

        all_references = parsed_refs
        all_references.extend(re_refs)

        to_verify = set()

        #
        #   Find the uploaded file in the references!
        #
        for ref in all_references:
            if mutant.uploaded_file_name in ref.url_string:
                # This one looks really promising!
                to_verify.add(ref)

            # These are just in case...
            if ref.get_extension() == mutant.extension:
                to_verify.add(ref)

        to_verify_filtered = list()

        # Run the read / writes to self._urls_recently_tested in a lock to
        # prevent RuntimeError generated when a thread is reading from it (in)
        # and another is appending to it.
        with self._urt_lock:
            for url in to_verify:
                if url in self._urls_recently_tested:
                    continue

                to_verify_filtered.append(url)
                self._urls_recently_tested.append(url)

        #
        #   Got nothing interesting, return.
        #
        if not to_verify_filtered:
            return

        #
        #   Now we verify what we got, this process makes sure that the links
        #   seen in the HTTP response body do contain the file we uploaded
        #
        debugging_id = rand_alnum(8)
        om.out.debug('audit.file_upload will search for the uploaded file'
                     ' in URLs extracted from the HTTP response body (did=%s).' % debugging_id)

        mutant_repeater = repeat(mutant)
        debugging_id_repeater = repeat(debugging_id)
        http_response_repeater = repeat(mutant_response)

        args = izip(to_verify_filtered,
                    mutant_repeater,
                    http_response_repeater,
                    debugging_id_repeater)

        self.worker_pool.map_multi_args(self._confirm_file_upload, args)

    def _find_files_by_bruteforce(self, mutant, mutant_response):
        """
        Use the framework's knowledge to find the file in all possible locations

        :param mutant: The request used to upload the file
        :param mutant_response: The HTTP response associated with the file upload
        :return: None
        """
        # Gen expr for directories where I can search for the uploaded file
        domain_path_set = set(u.get_domain_path() for u in
                              kb.kb.get_all_known_urls())

        debugging_id = rand_alnum(8)
        om.out.debug('audit.file_upload will search for the uploaded file'
                     ' in all known application paths (did=%s).' % debugging_id)

        # FIXME: Note that in all cases where I'm using kb's url_object info
        # I'll be making a mistake if the audit plugin is run before all
        # crawl plugins haven't run yet, since I'm not letting them
        # find all directories; which will make the current plugin run with
        # less information.
        mutant_repeater = repeat(mutant)
        debugging_id_repeater = repeat(debugging_id)
        http_response_repeater = repeat(mutant_response)
        url_generator = self._generate_urls(domain_path_set,
                                            mutant.uploaded_file_name)

        args = izip(url_generator,
                    mutant_repeater,
                    http_response_repeater,
                    debugging_id_repeater)

        self.worker_pool.map_multi_args(self._confirm_file_upload, args)

    def _confirm_file_upload(self, path, mutant, http_response, debugging_id):
        """
        Confirms if the file was uploaded to path

        :param path: The URL where we suspect that a file was uploaded to.
        :param mutant: The mutant that originated the file on the remote end
        :param http_response: The HTTP response associated with sending mutant
        """
        response = self._uri_opener.GET(path,
                                        cache=False,
                                        grep=False,
                                        debugging_id=debugging_id)

        if mutant.file_payload not in response.body:
            return

        if self._has_bug(mutant):
            return

        desc = 'A file upload to a directory inside the webroot was found at: %s'
        desc %= mutant.found_at()

        v = Vuln.from_mutant('Insecure file upload', desc, severity.HIGH,
                             [http_response.id, response.id],
                             self.get_name(), mutant)

        v['file_dest'] = response.get_url()
        v['file_vars'] = mutant.get_file_vars()

        self.kb_append_uniq(self, 'file_upload', v)

    def _generate_urls(self, domain_path_set, uploaded_file_name):
        """
        :param domain_path_set: A set of domain paths where the file could be
        :param uploaded_file_name: The name of the file that was uploaded to
                                   the server
        :return: A list of paths where the file could be.
        """
        seen = StopIterationLimitList(self.MAX_BRUTEFORCE_FINDS)

        #
        # First we go through all the known paths and check if any contains
        # one of the common path names where files are uploaded. If it does
        # then try to find the file there.
        #
        for url in domain_path_set:
            for common_path in self.UPLOAD_PATHS:
                if common_path not in url.url_string:
                    continue

                possible_location = url.url_join(uploaded_file_name)

                if not seen.contains(possible_location):
                    yield possible_location
                    seen.append(possible_location)

        #
        # No luck with the previous strategy? No problem! Be more aggressive
        # and try to find the file in the "shortest" paths. This means that
        # we'll first try:
        #
        #   http://target/uploads/{filename}
        #
        # And then if still nothing has been found we'll go for:
        #
        #   http://target/some/path/with/depth/uploads/{filename}
        #
        def sort_by_len(a, b):
            return cmp(len(b.url_string), len(a.url_string))

        domain_path_list = list(domain_path_set)
        domain_path_list.sort(sort_by_len)

        for url in domain_path_list:
            for common_path in self.UPLOAD_PATHS:
                possible_location = url.url_join(common_path + '/')
                possible_location = possible_location.url_join(uploaded_file_name)

                if not seen.contains(possible_location):
                    yield possible_location
                    seen.append(possible_location)

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Extensions that w3af will try to upload through the form.'
        h = ('When finding a form with a file upload, this plugin will try to'
             ' upload a set of files with the extensions specified here.')
        o = opt_factory('extensions', self._extensions, d, 'list', help=h)

        ol.add(o)

        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._extensions = options_list['extensions'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin will try to exploit insecure file upload forms.

        One configurable parameter exists:
            - extensions

        The extensions parameter is a comma separated list of extensions that
        this plugin will try to upload. Many web applications verify the extension
        of the file being uploaded, if special extensions are required, they can
        be added here.

        Some web applications check the contents of the files being uploaded to
        see if they are really what their extension is telling. To bypass this
        check, this plugin uses file templates located at "plugins/audit/file_upload/",
        this templates are valid files for each extension that have a section
        (the comment field in a gif file for example ) that can be replaced
        by scripting code ( PHP, ASP, etc ).

        After uploading the file, this plugin will try to find it on common
        directories like "upload" and "files" on every know directory. If the
        file is found, a vulnerability exists.
        """


class StopIterationLimitList(object):
    def __init__(self, max_items):
        """
        A rather strange list which will raise StopIteration when storing
        more than max_items.

        :param max_items: How many items to store before raising StopIteration
        """
        self.max_items = max_items
        self.store = list()

    def append(self, item):
        if len(self.store) > self.max_items:
            raise StopIteration

        self.store.append(item)

    def contains(self, item):
        return item in self.store
