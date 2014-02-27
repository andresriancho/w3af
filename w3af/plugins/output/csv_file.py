"""
csv_file.py

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
import csv
import itertools

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.plugins.output_plugin import OutputPlugin
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import OUTPUT_FILE
from w3af.core.data.options.option_list import OptionList


class csv_file(OutputPlugin):
    """
    Export identified vulnerabilities to a CSV file.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        OutputPlugin.__init__(self)
        self.output_file = '~/output-w3af.csv'

    def do_nothing(self, *args, **kwds):
        pass

    debug = log_http = vulnerability = do_nothing
    information = error = console = debug = log_enabled_plugins = do_nothing

    def end(self):
        """
        Exports the vulnerabilities and informations to the user configured file.
        """
        all_vulns = kb.kb.get_all_vulns()
        all_infos = kb.kb.get_all_infos()

        self.output_file = os.path.expanduser(self.output_file)

        try:
            csv_writer = csv.writer(
                open(self.output_file, 'wb'), delimiter=',',
                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        except Exception, e:
            msg = 'An exception was raised while trying to open the '
            msg += ' output file. Exception: "%s"' % e
            om.out.error(msg)
            return

        for data in itertools.chain(all_vulns, all_infos):
            try:
                row = [
                    data.get_name(),
                    data.get_method(),
                    data.get_uri(),
                    data.get_var(),
                    data.get_dc(),
                    data.get_id(),
                    data.get_desc()
                ]
                csv_writer.writerow(row)
            except Exception, e:
                msg = 'An exception was raised while trying to write the '
                msg += ' vulnerabilities to the output file. Exception: "%s"'
                msg = msg % e
                om.out.error(msg)
                return

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin exports all identified vulnerabilities and informations
        to the given CSV file.

        One configurable parameter exists:
            - output_file
        """

    def set_options(self, option_list):
        """
        Sets the Options given on the OptionList to self. The options are the
        result of a user entering some data on a window that was constructed
        using the XML Options that was retrieved from the plugin using get_options()

        :return: No value is returned.
        """
        self.output_file = option_list['output_file'].get_value()

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'The name of the output file where the vulnerabilities will be saved'
        o = opt_factory('output_file', self.output_file, d, OUTPUT_FILE)
        ol.add(o)

        return ol
