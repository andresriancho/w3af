"""
test_lfi.py

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
from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.controllers.ci.wavsep import get_wavsep_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig


CONFIG = {
    'audit': (PluginConfig('lfi'),),
    'crawl': (
        PluginConfig(
            'web_spider',
            ('only_forward', True, PluginConfig.BOOL)),)

}


class TestLFI(PluginTest):

    target_url = get_moth_http('/audit/local_file_read/')

    def test_found_lfi(self):
        self._scan(self.target_url, CONFIG)

        # Assert the general results
        vulns = self.kb.get('lfi', 'lfi')

        # Verify the specifics about the vulnerabilities
        expected = [
            ('local_file_read.py', 'file'),
            ('local_file_read_full_path.py', 'file'),
        ]

        self.assertAllVulnNamesEqual('Local file inclusion vulnerability', vulns)
        self.assertExpectedVulnsFound(expected, vulns)


class TestWAVSEP500Error(PluginTest):

    base_path = '/wavsep/active/LFI/LFI-Detection-Evaluation-GET-500Error/'

    target_url = get_wavsep_http(base_path)

    def test_find_lfi_wavsep_error(self):
        expected_path_param = {
            (u'Case01-LFI-FileClass-FilenameContext-Unrestricted-OSPath-DefaultFullInput-AnyPathReq-Read.jsp', u'target'),
            (u'Case02-LFI-FileClass-FilenameContext-Unrestricted-FileDirective-DefaultFullInput-AnyPathReq-Read.jsp', u'target'),
            (u'Case03-LFI-FileClass-FilenameContext-Unrestricted-OSPath-DefaultRelativeInput-AnyPathReq-Read.jsp', u'target'),
            (u'Case04-LFI-FileClass-FilenameContext-Unrestricted-FileDirective-DefaultRelativeInput-AnyPathReq-Read.jsp', u'target'),
            (u'Case05-LFI-FileClass-FilenameContext-Unrestricted-OSPath-DefaultInvalidInput-AnyPathReq-Read.jsp', u'target'),
            (u'Case06-LFI-FileClass-FilenameContext-Unrestricted-FileDirective-DefaultInvalidInput-AnyPathReq-Read.jsp', u'target'),
            (u'Case07-LFI-FileClass-FilenameContext-Unrestricted-OSPath-DefaultEmptyInput-AnyPathReq-Read.jsp', u'target'),
            (u'Case08-LFI-FileClass-FilenameContext-Unrestricted-FileDirective-DefaultEmptyInput-AnyPathReq-Read.jsp', u'target'),
            (u'Case09-LFI-FileClass-FilenameContext-Unrestricted-OSPath-DefaultFullInput-NoPathReq-Read.jsp', u'target'),
            (u'Case11-LFI-FileClass-FilenameContext-Unrestricted-OSPath-DefaultInvalidInput-NoPathReq-Read.jsp', u'target'),
            (u'Case13-LFI-FileClass-FilenameContext-Unrestricted-OSPath-DefaultEmptyInput-NoPathReq-Read.jsp', u'target'),
            (u'Case15-LFI-FileClass-FilenameContext-Unrestricted-OSPath-DefaultFullInput-SlashPathReq-Read.jsp', u'target'),
            (u'Case17-LFI-FileClass-FilenameContext-Unrestricted-OSPath-DefaultInvalidInput-SlashPathReq-Read.jsp', u'target'),
            (u'Case19-LFI-FileClass-FilenameContext-Unrestricted-OSPath-DefaultEmptyInput-SlashPathReq-Read.jsp', u'target'),
            (u'Case21-LFI-FileClass-FilenameContext-Unrestricted-OSPath-DefaultFullInput-BackslashPathReq-Read.jsp', u'target'),
            (u'Case22-LFI-FileClass-FilenameContext-Unrestricted-OSPath-DefaultInvalidInput-BackslashPathReq-Read.jsp', u'target'),
            (u'Case23-LFI-FileClass-FilenameContext-Unrestricted-OSPath-DefaultEmptyInput-BackslashPathReq-Read.jsp', u'target'),
            (u'Case28-LFI-ContextStream-FilenameContext-Unrestricted-OSPath-DefaultFullInput-NoPathReq-Read.jsp', u'target'),
            (u'Case29-LFI-ContextStream-FilenameContext-Unrestricted-OSPath-DefaultInvalidInput-NoPathReq-Read.jsp', u'target'),
            (u'Case30-LFI-ContextStream-FilenameContext-Unrestricted-OSPath-DefaultEmptyInput-NoPathReq-Read.jsp', u'target'),
            (u'Case31-LFI-ContextStream-FilenameContext-Unrestricted-OSPath-DefaultFullInput-SlashPathReq-Read.jsp', u'target'),
            (u'Case32-LFI-ContextStream-FilenameContext-Unrestricted-OSPath-DefaultInvalidInput-SlashPathReq-Read.jsp', u'target'),
            (u'Case33-LFI-ContextStream-FilenameContext-Unrestricted-OSPath-DefaultEmptyInput-SlashPathReq-Read.jsp', u'target'),
            (u'Case34-LFI-ContextStream-FilenameContext-Unrestricted-OSPath-DefaultFullInput-BackslashPathReq-Read.jsp', u'target'),
            (u'Case35-LFI-ContextStream-FilenameContext-Unrestricted-OSPath-DefaultInvalidInput-BackslashPathReq-Read.jsp', u'target'),
            (u'Case36-LFI-ContextStream-FilenameContext-Unrestricted-OSPath-DefaultEmptyInput-BackslashPathReq-Read.jsp', u'target'),
            (u'Case38-LFI-FileClass-FilenameContext-BackslashTraversalValidation-OSPath-DefaultFullInput-AnyPathReq-Read.jsp', u'target'),
            (u'Case39-LFI-FileClass-FilenameContext-UnixTraversalValidation-OSPath-DefaultFullInput-NoPathReq-Read.jsp', u'target'),
            (u'Case40-LFI-FileClass-FilenameContext-WindowsTraversalValidation-OSPath-DefaultFullInput-NoPathReq-Read.jsp', u'target'),
            (u'Case41-LFI-FileClass-FilenameContext-UnixTraversalValidation-OSPath-DefaultFullInput-SlashPathReq-Read.jsp', u'target'),
            (u'Case42-LFI-FileClass-FilenameContext-WindowsTraversalValidation-OSPath-DefaultFullInput-SlashPathReq-Read.jsp', u'target'),
            (u'Case43-LFI-FileClass-FilenameContext-UnixTraversalValidation-OSPath-DefaultFullInput-BackslashPathReq-Read.jsp', u'target'),
            (u'Case44-LFI-FileClass-FilenameContext-WindowsTraversalValidation-OSPath-DefaultFullInput-BackslashPathReq-Read.jsp', u'target'),
            (u'Case47-LFI-ContextStream-FilenameContext-UnixTraversalValidation-OSPath-DefaultFullInput-NoPathReq-Read.jsp', u'target'),
            (u'Case48-LFI-ContextStream-FilenameContext-WindowsTraversalValidation-OSPath-DefaultFullInput-NoPathReq-Read.jsp', u'target'),
            (u'Case49-LFI-ContextStream-FilenameContext-UnixTraversalValidation-OSPath-DefaultFullInput-SlashPathReq-Read.jsp', u'target'),
            (u'Case50-LFI-ContextStream-FilenameContext-WindowsTraversalValidation-OSPath-DefaultFullInput-SlashPathReq-Read.jsp', u'target'),
            (u'Case51-LFI-ContextStream-FilenameContext-UnixTraversalValidation-OSPath-DefaultFullInput-BackslashPathReq-Read.jsp', u'target'),
            (u'Case52-LFI-ContextStream-FilenameContext-WindowsTraversalValidation-OSPath-DefaultFullInput-BackslashPathReq-Read.jsp', u'target'),
            (u'Case54-LFI-FileClass-FilenameContext-BackslashTraversalRemoval-OSPath-DefaultFullInput-AnyPathReq-Read.jsp', u'target'),
            (u'Case55-LFI-FileClass-FilenameContext-UnixTraversalRemoval-OSPath-DefaultFullInput-NoPathReq-Read.jsp', u'target'),
            (u'Case56-LFI-FileClass-FilenameContext-WindowsTraversalRemoval-OSPath-DefaultFullInput-NoPathReq-Read.jsp', u'target'),
            (u'Case57-LFI-FileClass-FilenameContext-UnixTraversalRemoval-OSPath-DefaultFullInput-SlashPathReq-Read.jsp', u'target'),
            (u'Case58-LFI-FileClass-FilenameContext-WindowsTraversalRemoval-OSPath-DefaultFullInput-SlashPathReq-Read.jsp', u'target'),
            (u'Case59-LFI-FileClass-FilenameContext-UnixTraversalRemoval-OSPath-DefaultFullInput-BackslashPathReq-Read.jsp', u'target'),
            (u'Case60-LFI-FileClass-FilenameContext-WindowsTraversalRemoval-OSPath-DefaultFullInput-BackslashPathReq-Read.jsp', u'target'),
            (u'Case63-LFI-ContextStream-FilenameContext-UnixTraversalRemoval-OSPath-DefaultFullInput-NoPathReq-Read.jsp', u'target'),
            (u'Case64-LFI-ContextStream-FilenameContext-WindowsTraversalRemoval-OSPath-DefaultFullInput-NoPathReq-Read.jsp', u'target'),
            (u'Case65-LFI-ContextStream-FilenameContext-UnixTraversalRemoval-OSPath-DefaultFullInput-SlashPathReq-Read.jsp', u'target'),
            (u'Case66-LFI-ContextStream-FilenameContext-WindowsTraversalRemoval-OSPath-DefaultFullInput-SlashPathReq-Read.jsp', u'target'),
            (u'Case67-LFI-ContextStream-FilenameContext-UnixTraversalRemoval-OSPath-DefaultFullInput-BackslashPathReq-Read.jsp', u'target'),
            (u'Case68-LFI-ContextStream-FilenameContext-WindowsTraversalRemoval-OSPath-DefaultFullInput-BackslashPathReq-Read.jsp', u'target'),
        }

        # None is OK to miss -> 100% coverage, that's our goal!
        ok_to_miss = {
            u'Case10-LFI-FileClass-FilenameContext-Unrestricted-FileDirective-DefaultFullInput-NoPathReq-Read.jsp',
            u'Case12-LFI-FileClass-FilenameContext-Unrestricted-FileDirective-DefaultInvalidInput-NoPathReq-Read.jsp',
            u'Case14-LFI-FileClass-FilenameContext-Unrestricted-FileDirective-DefaultEmptyInput-NoPathReq-Read.jsp',
            u'Case16-LFI-FileClass-FilenameContext-Unrestricted-FileDirective-DefaultFullInput-SlashPathReq-Read.jsp',
            u'Case18-LFI-FileClass-FilenameContext-Unrestricted-FileDirective-DefaultInvalidInput-SlashPathReq-Read.jsp',
            u'Case20-LFI-FileClass-FilenameContext-Unrestricted-FileDirective-DefaultEmptyInput-SlashPathReq-Read.jsp',
            u'Case24-LFI-FileClass-FilenameContext-Unrestricted-FileDirective-DefaultFullInput-BackslashPathReq-Read.jsp',
            u'Case25-LFI-ContextStream-FilenameContext-Unrestricted-OSPath-DefaultFullInput-AnyPathReq-Read.jsp',
            u'Case26-LFI-ContextStream-FilenameContext-Unrestricted-OSPath-DefaultInvalidInput-AnyPathReq-Read.jsp',
            u'Case27-LFI-ContextStream-FilenameContext-Unrestricted-OSPath-DefaultEmptyInput-AnyPathReq-Read.jsp',
            u'Case45-LFI-ContextStream-FilenameContext-SlashTraversalValidation-OSPath-DefaultFullInput-AnyPathReq-Read.jsp',
            u'Case46-LFI-ContextStream-FilenameContext-BackslashTraversalValidation-OSPath-DefaultFullInput-AnyPathReq-Read.jsp',
            u'Case53-LFI-FileClass-FilenameContext-SlashTraversalRemoval-OSPath-DefaultFullInput-AnyPathReq-Read.jsp',
            u'Case61-LFI-ContextStream-FilenameContext-SlashTraversalRemoval-OSPath-DefaultFullInput-AnyPathReq-Read.jsp',
            u'Case62-LFI-ContextStream-FilenameContext-BackslashTraversalRemoval-OSPath-DefaultFullInput-AnyPathReq-Read.jsp',

            #
            # These are confirmed not to work when WAVSEP is running in Linux,
            # so there is nothing w3af can improve to detect them:
            #
            # https://code.google.com/p/wavsep/issues/detail?id=10
            # https://github.com/sectooladdict/wavsep/issues/5
            #
            u'Case37-LFI-FileClass-FilenameContext-SlashTraversalValidation-OSPath-DefaultFullInput-AnyPathReq-Read.jsp',
        }
        skip_startwith = {'index.jsp'}
        kb_addresses = {('lfi', 'lfi')}

        self._scan_assert(CONFIG,
                          expected_path_param,
                          ok_to_miss,
                          kb_addresses,
                          skip_startwith)