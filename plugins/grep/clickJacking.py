'''
clickJacking.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''
import core.controllers.outputManager as om
from core.data.options.option import option
from core.data.options.optionList import optionList
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity
from core.data.db.disk_list import disk_list
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin


class clickJacking(baseGrepPlugin):
    '''
    Grep every page for X-Frame-Options header.

    @author: Taras (oxdef@oxdef.info)
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        self._total_count = 0
        self._vuln_count = 0
        self._vulns = disk_list()

    def grep(self, request, response):
        if not response.is_text_or_html():
            return
        self._total_count += 1
        # TODO need to check here for auth cookie?!
        headers = response.getLowerCaseHeaders()
        x_frame_options = headers.get('x-frame-options', None)
        if x_frame_options\
                and x_frame_options.lower() in ('deny', 'sameorigin'):
            return
        self._vuln_count += 1
        if response.getURL() not in self._vulns:
            self._vulns.append(response.getURL())

    def getOptions(self):
        ol = optionList()
        return ol

    def setOptions(self, o):
        pass

    def end(self):
        # If all URLs implement protection, don't report anything.
        if not self._vuln_count:
            return
        v = vuln.vuln()
        v.setPluginName(self.getName())
        v.setName('Possible ClickJacking attack' )
        v.setSeverity(severity.MEDIUM)
        # If none of the URLs implement protection, simply report
        # ONE vulnerability that says that.
        if self._total_count == self._vuln_count:
            msg = 'The whole target '
            msg += 'has no protection (X-Frame-Options header) against ClickJacking attack'
            v.setDesc(msg)
            kb.kb.append(self, 'clickJacking', v)
        # If most of the URLs implement the protection but some
        # don't, report ONE vulnerability saying: "Most are protected, but x, y are not.
        if self._total_count > self._vuln_count:
            msg = 'Some URLs has no protection (X-Frame-Options header) '
            msg += 'against ClickJacking attack. Among them:\n '
            msg += ' '.join([str(url) + '\n' for url in self._vulns])
            v.setDesc(msg)
            kb.kb.append(self, 'clickJacking', v)
        self.printUniq(kb.kb.getData( 'clickJacking', 'clickJacking' ), 'URL')

    def getPluginDeps(self):
        return []

    def getLongDesc(self):
        return '''
        This plugin greps every page for X-Frame-Options header and so
        for possible ClickJacking attack against URL.

        Additional information: https://www.owasp.org/index.php/Clickjacking
        '''
