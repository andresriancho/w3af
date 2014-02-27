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
from w3af.core.data.request.WebServiceRequest import WebServiceRequest


class export_requests(OutputPlugin):
    """
    Export the fuzzable requests found during crawl to a file.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        OutputPlugin.__init__(self)
        self.output_file = '~/output-requests.csv'

    def do_nothing(self, *args, **kwds):
        pass

    debug = log_http = vulnerability = do_nothing
    information = error = console = debug = log_enabled_plugins = do_nothing

    def end(self):
        """
        Exports a list of fuzzable requests to the user configured file.
        """
        fuzzable_request_set = kb.kb.get_all_known_fuzzable_requests()
        
        filename = os.path.expanduser(self.output_file)

        try:
            out_file = open(filename, 'w')
            out_file.write('HTTP-METHOD,URI,POSTDATA\n')

            for fr in fuzzable_request_set:
                # TODO: How shall we export WebServiceRequests?
                if not isinstance(fr, WebServiceRequest):
                    out_file.write(fr.export() + '\n')

            out_file.close()
        except Exception, e:
            msg = 'An exception was raised while trying to export fuzzable'\
                  ' requests to the output file: "%s".' % e
            om.out.error(msg)
            print msg

    def set_options(self, option_list):
        """
        Sets the Options given on the OptionList to self. The options are the
        result of a user entering some data on a window that was constructed
        using the XML Options that was retrieved from the plugin using
        get_options()

        This method MUST be implemented on every plugin.

        :return: No value is returned.
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
        This plugin exports all discovered HTTP requests (URL, Method, Params)
        to the given file (CSV) which can then be imported in another scan by
        using the crawl.import_results.

        One configurable parameter exists:
            - output_file
        """
