"""
export_requests.py

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
import os

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.plugins.output_plugin import OutputPlugin
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import OUTPUT_FILE
from w3af.core.data.options.option_list import OptionList


class export_requests(OutputPlugin):
    """
    Export the fuzzable requests found during crawl to a file.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        OutputPlugin.__init__(self)
        self.output_file = '~/output-requests.b64'

    def do_nothing(self, *args, **kwds):
        pass

    debug = log_http = vulnerability = do_nothing
    information = error = console = debug = log_enabled_plugins = do_nothing

    def end(self):
        self.flush()

    def flush(self):
        """
        Exports a list of fuzzable requests to the user configured file.
        """
        fuzzable_request_set = kb.kb.get_all_known_fuzzable_requests()
        
        filename = os.path.expanduser(self.output_file)

        try:
            out_file = open(filename, 'w')
        except IOError, ioe:
            msg = 'Failed to open the output file for writing: "%s"'
            om.out.error(msg % ioe)
            return

        try:
            for fr in fuzzable_request_set:
                out_file.write(fr.to_base64() + '\n')

        except Exception, e:
            msg = ('An exception was raised while trying to export fuzzable'
                   ' requests to the output file: "%s".' % e)
            om.out.error(msg)
        finally:
            out_file.close()

    def set_options(self, option_list):
        """
        :return: Save the options for this plugin
        """
        self.output_file = option_list['output_file'].get_value()

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'The name of the output file where the HTTP requests will be saved'
        o = opt_factory('output_file', self.output_file, d, OUTPUT_FILE)
        ol.add(o)

        return ol

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin exports all discovered HTTP requests to an output file. The
        output can then be read in another scan by the crawl.import_results to
        avoid performing an expensive crawling phase.

        The file format is simple:

         * HTTP requests are serialized to a string (just how they would be
           sent to the wire)

         * Base64 encoding is used to encode the serialized request

         * Each encoded request is stored in a new line

        One configurable parameter exists:
            - output_file
        """
