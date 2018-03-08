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
import base64

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

    def do_nothing(self, *args, **kwargs):
        pass

    debug = log_http = vulnerability = do_nothing
    information = error = console = log_enabled_plugins = do_nothing

    def end(self):
        self.flush()

    def flush(self):
        """
        Exports the vulnerabilities and information to the user configured
        file.
        """
        self.output_file = os.path.expanduser(self.output_file)

        try:
            output_handler = file(self.output_file, 'wb')
        except IOError, ioe:
            msg = 'Failed to open the output file for writing: "%s"'
            om.out.error(msg % ioe)
            return

        try:
            csv_writer = csv.writer(output_handler,
                                    delimiter=',',
                                    quotechar='|',
                                    quoting=csv.QUOTE_MINIMAL)
        except Exception, e:
            msg = ('An exception was raised while trying to open the '
                   ' CSV writer. Exception: "%s"')
            om.out.error(msg % e)
            output_handler.close()
            return

        for info in kb.kb.get_all_findings_iter():
            try:
                row = [info.get_severity(),
                       info.get_name(),
                       info.get_method(),
                       info.get_uri(),
                       info.get_token_name(),
                       base64.b64encode(info.get_mutant().get_data()),
                       info.get_id(),
                       info.get_desc()]
                csv_writer.writerow(row)
            except Exception, e:
                msg = ('An exception was raised while trying to write the '
                       ' vulnerabilities to the output file. Exception: "%s"')
                om.out.error(msg % e)
                output_handler.close()
                print(e)
                return

        output_handler.close()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin exports all identified vulnerabilities to a CSV file.

        Each line in the file contains the following fields:
            * Severity
            * Name
            * HTTP method
            * URL
            * Vulnerable parameter
            * Base64 encoded POST-data
            * Unique vulnerability ID
            * Description

        Fields are comma separated and the | character is used for quoting.

        The CSV plugin should be used for quick and easy integrations with w3af,
        external tools which require more details, such as the HTTP request and
        response associated with each vulnerability, should use the xml_file
        output plugin.

        One configurable parameter exists:
            - output_file
        """

    def set_options(self, option_list):
        """
        Sets the Options given on the OptionList to self. The options are the
        result of a user entering some data on a window that was constructed
        using the XML Options that was retrieved from the plugin using
        get_options()

        :return: No value is returned.
        """
        self.output_file = option_list['output_file'].get_value()

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'The name of the output file where the vulnerabilities are be saved'
        o = opt_factory('output_file', self.output_file, d, OUTPUT_FILE)
        ol.add(o)

        return ol
