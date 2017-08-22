"""
user_defined_regex.py

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
from __future__ import with_statement

import os
import re

import w3af.core.controllers.output_manager as om

from w3af import ROOT_PATH
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import INPUT_FILE, REGEX
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.kb.info import Info


class user_defined_regex(GrepPlugin):
    """
    Report a vulnerability if the response matches a user defined regex.

    :author: floyd fuh ( floyd_fuh@yahoo.de )
    """

    def __init__(self):
        GrepPlugin.__init__(self)

        # User defined options
        self._single_regex = ''
        self._regex_file_path = os.path.join(ROOT_PATH, 'plugins', 'grep',
                                             'user_defined_regex', 'empty.txt')

        # Internal variables
        # Improved performance by compiling all the regular expressions
        # before using them (see set_options method)
        self._regexlist_compiled = []
        self._all_in_one = None

    def grep(self, request, response):
        """
        Plugin entry point, search for the user defined regex.
        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        if self._all_in_one is None:
            return

        if not response.is_text_or_html():
            return

        # TODO: Verify this this is really a performance improvement
        html_string = response.get_body()
        if not self._all_in_one.search(html_string):
            return

        # One of them is in there, now we need to find out which one
        for index, regex_tuple in enumerate(self._regexlist_compiled):

            regex, info_inst = regex_tuple
            match_object = regex.search(html_string)

            if match_object:
                with self._plugin_lock:
                    # Don't change the next line to "if info_inst:",
                    # because the info_inst is an empty dict {}
                    # which evaluates to false
                    # but an info object is not the same as None
                    if not info_inst is None:
                        ids = info_inst.get_id()
                        ids.append(response.id)
                        info_inst.set_id(ids)
                    else:
                        str_match = match_object.group(0)
                        if len(str_match) > 20:
                            str_match = str_match[:20] + '...'
                            
                        desc = 'User defined regular expression "%s" matched a' \
                               ' response. The matched string is: "%s".'
                        desc = desc % (regex.pattern, str_match)
                        
                        info_inst = Info('User defined regular expression match',
                                         desc, response.id, self.get_name())
                        info_inst.set_url(response.get_url())
                        
                        om.out.information(desc)

                        self.kb_append_uniq(self, 'user_defined_regex', info_inst, 'URL')

                    # Save the info_inst
                    self._regexlist_compiled[index] = (regex, info_inst)

    def set_options(self, options_list):
        """
        Handle user configuration parameters.
        :return: None
        """
        # The not yet compiled all_in_one_regex
        tmp_not_compiled_all = []
        #
        #   Add the regexes from the file
        #
        self._regexlist_compiled = []
        regex_file_path = options_list['regex_file_path'].get_value()
        if regex_file_path and not regex_file_path == 'None':
            self._regex_file_path = regex_file_path

            try:
                f = file(self._regex_file_path)
            except Exception, e:
                msg = 'Unable to open file "%s", error: "%s".'
                raise BaseFrameworkException(msg % (self._regex_file_path, e))
            else:
                for regex in f:
                    current_regex = regex.strip()
                    try:
                        re_inst = re.compile(current_regex, re.I | re.DOTALL)
                    except:
                        msg = 'Invalid regex in input file: "%s"'
                        raise BaseFrameworkException(msg % current_regex)
                    else:
                        self._regexlist_compiled.append((re_inst, None))
                        tmp_not_compiled_all.append(current_regex)

        #
        #   Add the single regex
        #
        self._single_regex = options_list['single_regex'].get_value()
        if self._single_regex:
            # Please note that the regex compilation can not fail because
            # the option is of type REGEX and there is a validation made in
            # regex_option.py
            re_inst = re.compile(self._single_regex, re.I | re.DOTALL)

            self._regexlist_compiled.append((re_inst, None))
            tmp_not_compiled_all.append(self._single_regex)

        #
        #   Compile all in one regex
        #
        if tmp_not_compiled_all:
            # get a string like (regexA)|(regexB)|(regexC)
            all_in_one_uncompiled = '(' + ')|('.join(
                tmp_not_compiled_all) + ')'
            self._all_in_one = re.compile(all_in_one_uncompiled,
                                          re.IGNORECASE | re.DOTALL)

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Single regex to use in the grep process.'
        o = opt_factory('single_regex', self._single_regex, d, REGEX)
        ol.add(o)

        d = 'Path to file with regular expressions to use in the grep process.'
        h = 'Attention: The file will be loaded line by line into memory,'\
            ' because the regex will be pre-compiled in order to achieve '\
            ' better performance during the scan process. \n\n'\
            'A list of example regular expressions can be found at '\
            '"plugins/grep/user_defined_regex/".'
        o = opt_factory('regex_file_path', self._regex_file_path, d,
                        INPUT_FILE, help=h)
        ol.add(o)

        return ol

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every response for a user defined regex.

        You can specify a single regex or an entire file of regexes (each line
        one regex), if both are specified, the single_regex will be added to
        the list of regular expressions extracted from the file.

        Sample files containing interesting regular expressions can be found at:
            "plugins/grep/user_defined_regex/".

        For every match an information message is shown.
        """
