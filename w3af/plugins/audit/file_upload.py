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

from w3af import ROOT_PATH
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.controllers.misc.io import NamedStringIO

from w3af.core.data.constants.file_templates.file_templates import get_file_from_template
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.kb.vuln import Vuln


class file_upload(AuditPlugin):
    """
    Uploads a file and then searches for the file inside all known directories.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    TEMPLATE_DIR = os.path.join(ROOT_PATH, 'core', 'data', 'constants',
                                'file_templates')
    UPLOAD_PATHS = ['uploads', 'upload', 'file', 'user', 'files', 'downloads',
                    'download', 'up', 'down']

    def __init__(self):
        AuditPlugin.__init__(self)

        # User configured
        self._extensions = ['gif', 'html', 'bmp', 'jpg', 'png', 'txt']

    def audit(self, freq, orig_response):
        """
        Searches for file upload vulns.

        :param freq: A FuzzableRequest
        """
        if freq.get_method().upper() != 'POST' or not freq.get_file_vars():
            return

        for file_parameter in freq.get_file_vars():
            for extension in self._extensions:

                _, file_content, file_name = get_file_from_template(extension)

                # Only file handlers are passed to the create_mutants functions
                named_stringio = NamedStringIO(file_content, file_name)
                mutants = create_mutants(freq, [named_stringio],
                                         fuzzable_param_list=[file_parameter])

                for mutant in mutants:
                    mutant.uploaded_file_name = file_name

                self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                              mutants,
                                              self._analyze_result)

    def _analyze_result(self, mutant, mutant_response):
        """
        Analyze results of the _send_mutant method.

        In this case, check if the file was uploaded to any of the known
        directories, or one of the "default" ones like "upload" or "files".
        """
        if self._has_bug(mutant):
            return

        # Gen expr for directories where I can search for the uploaded file
        domain_path_list = set(u.get_domain_path() for u in
                               kb.kb.get_all_known_urls())

        # FIXME: Note that in all cases where I'm using kb's url_object info
        # I'll be making a mistake if the audit plugin is run before all
        # crawl plugins haven't run yet, since I'm not letting them
        # find all directories; which will make the current plugin run with
        # less information.
        url_generator = self._generate_urls(domain_path_list,
                                            mutant.uploaded_file_name)
        mutant_repeater = repeat(mutant)
        http_response_repeater = repeat(mutant_response)
        args = izip(url_generator, mutant_repeater, http_response_repeater)

        self.worker_pool.map_multi_args(self._confirm_file_upload, args)

    def _confirm_file_upload(self, path, mutant, http_response):
        """
        Confirms if the file was uploaded to path

        :param path: The URL where we suspect that a file was uploaded to.
        :param mutant: The mutant that originated the file on the remote end
        :param http_response: The HTTP response asociated with sending mutant
        """
        get_response = self._uri_opener.GET(path, cache=False)

        if not is_404(get_response) and self._has_no_bug(mutant):
            desc = 'A file upload to a directory inside the webroot' \
                   ' was found at: %s' % mutant.found_at()
            
            v = Vuln.from_mutant('Insecure file upload', desc, severity.HIGH,
                                 [http_response.id, get_response.id],
                                 self.get_name(), mutant)
            
            v['file_dest'] = get_response.get_url()
            v['file_vars'] = mutant.get_file_vars()

            self.kb_append_uniq(self, 'file_upload', v)

    def _generate_urls(self, domain_path_list, uploaded_file_name):
        """
        :param url: A URL where the uploaded_file_name could be
        :param uploaded_file_name: The name of the file that was uploaded to
                                   the server
        :return: A list of paths where the file could be.
        """
        for url in domain_path_list:
            for default_path in self.UPLOAD_PATHS:
                for sub_url in url.get_directories():
                    possible_location = sub_url.url_join(default_path + '/')
                    possible_location = possible_location.url_join(
                        uploaded_file_name)
                    yield possible_location

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Extensions that w3af will try to upload through the form.'
        h = 'When finding a form with a file upload, this plugin will try to'\
            ' upload a set of files with the extensions specified here.'
        o = opt_factory('extensions', self._extensions, d, 'list', help=h)

        ol.add(o)

        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param OptionList: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._extensions = options_list['extensions'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin will try to expoit insecure file upload forms.

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
