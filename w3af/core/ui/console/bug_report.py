"""
bug_report.py

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

import w3af.core.controllers.output_manager as om

from w3af.core.ui.console.menu import menu
from w3af.core.ui.console.util import suggest
from w3af.core.controllers.easy_contribution.github_issues import (GithubIssues,
                                                                   OAUTH_TOKEN,
                                                                   OAUTH_AUTH_FAILED,
                                                                   LoginFailed,
                                                                   OAuthTokenInvalid)


class bug_report_menu(menu):
    """
    This menu is used to display bugs gathered by the exception handler during
    a scan and help the user report those vulnerabilities to our Github project.

    :author: Andres Riancho (andres.riancho |at| gmail.com)
    """
    def __init__(self, name, console, w3af_core, parent=None, **other):
        menu.__init__(self, name, console, w3af_core, parent)
        self._load_help('bug-report')

    def _cmd_summary(self, params):
        summary = self._w3af.exception_handler.generate_summary_str()
        om.out.console(summary)

    def _cmd_list(self, params):
        all_edata = self._w3af.exception_handler.get_unique_exceptions()

        if len(params) == 0:
            ptype = 'all'
        elif len(params) == 1 and params[0] in self._w3af.plugins.get_plugin_types():
            ptype = params[0]
        else:
            om.out.console('Invalid parameter type, please read help:')
            self._cmd_help(['list'])
            return

        table = [('ID', 'Phase', 'Plugin', 'Exception'),
                 ()]
        eid = 0
        for edata in all_edata:
            if edata.phase == ptype or ptype == 'all':
                table_line = ((str(
                    eid), edata.phase, edata.plugin, str(edata.exception)))
                table.append(table_line)
            eid += 1

        self._console.draw_table(table)

    def _cmd_details(self, params):
        """
        Show details for a bug referenced by id.
        """
        all_edata = self._w3af.exception_handler.get_unique_exceptions()

        if len(params) != 1:
            om.out.console(
                'The exception ID needs to be specified, please read help:')
            self._cmd_help(['details'])
            return
        elif not params[0].isdigit():
            om.out.console(
                'The exception ID needs to be an integer, please read help:')
            self._cmd_help(['details'])
            return
        elif int(params[0]) > len(all_edata) - 1 or int(params[0]) < 0:
            om.out.console('Invalid ID specified, please read help:')
            self._cmd_help(['details'])
            return
        else:
            eid = int(params[0])
            edata = all_edata[eid]
            om.out.console(str(edata))

    def _cmd_report(self, params):
        """
        Report one or more bugs to w3af's Github, menu command.
        """
        all_edata = self._w3af.exception_handler.get_unique_exceptions()

        if not all_edata:
            om.out.console('There are no exceptions to report for this scan.')
            return

        report_bug_eids = []

        for data in params:
            id_list = data.split(',')
            for eid in id_list:
                if not eid.isdigit():
                    om.out.console('Exception IDs must be integers.')
                else:
                    eid = int(eid)
                    if not eid < len(all_edata):
                        om.out.console('Exception ID out of range.')
                    else:
                        report_bug_eids.append(eid)

        # default to reporting all exceptions if none was specified
        if not report_bug_eids:
            report_bug_eids = range(len(all_edata))

        for num, eid in enumerate(report_bug_eids):
            edata = all_edata[eid]
            self._report_exception(edata, eid, num + 1, len(report_bug_eids))

    def _report_exception(self, edata, eid, num, total):
        """
        Report one or more bugs to w3af's Github, submit data to server.
        """
        try:
            gh = GithubIssues(OAUTH_TOKEN)
            gh.login()
        except LoginFailed:
            msg = 'Failed to contact github.com. Please try again later.'
            om.out.console(msg)
        except OAuthTokenInvalid:
            om.out.console(OAUTH_AUTH_FAILED)
        else:
            traceback_str = edata.traceback_str
            desc = edata.get_summary()
            plugins = edata.enabled_plugins
            summary = str(edata.exception)

            ticket_id, ticket_url = gh.report_bug(summary, desc,
                                                  tback=traceback_str,
                                                  plugins=plugins)

            if ticket_id is None:
                fmt = '    [%s/%s] Failed to report bug with id %s.'
                msg = fmt % (num, total, eid)
            else:
                fmt = '    [%s/%s] Bug with id %s reported at %s'
                msg = fmt % (num, total, eid, ticket_url)

            om.out.console(str(msg))

    def _para_details(self, params, part):
        if len(params):
            return []

        all_edata = self._w3af.exception_handler.get_unique_exceptions()
        suggestions = [str(i) for i in xrange(len(all_edata))]

        return suggest(suggestions, part)

    _para_report = _para_details

    def _para_list(self, params, part):
        if len(params):
            return []

        return suggest(self._w3af.plugins.get_plugin_types(), part)
