'''
halberd.py

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

'''
import sys
import os
import pprint
import StringIO
#
# Halberd imports, done this way so the user can run this plugin without having
# to install halberd Also, the halberd version i'm using, has some changes.
#
halberd_dir = os.path.join('plugins', 'infrastructure', 'oHalberd')
# This insert in the first position of the path is to "step over" an installation
# of halberd.
sys.path.insert(0, halberd_dir)
# I do it this way and not with a "from w3af.plugins.infrastructure.oHalberd.Halberd
# import logger" because inside the original hablerd they are crossed imports
# and stuff that I don't want to modify.
import Halberd.shell as halberd_shell
import Halberd.logger as halberd_logger
import Halberd.ScanTask as halberd_scan_task
import Halberd.version as halberd_shell_version
import Halberd.clues.analysis as halberd_analysis

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.exceptions import w3afRunOnce
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.data.kb.info import Info


class halberd(InfrastructurePlugin):
    '''
    Identify if the remote server has HTTP load balancers.

    This plugin is a wrapper of Juan M. Bello Rivas' halberd.

    :author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        InfrastructurePlugin.__init__(self)

    @runonce(exc_class=w3afRunOnce)
    def discover(self, fuzzable_request):
        '''
        It calls the "main" from halberd and writes the results to the kb.

        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        '''
        msg = 'halberd plugin is starting. Original halberd author: '
        msg += 'Juan M. Bello Rivas; http://halberd.superadditive.com/'
        om.out.information(msg)

        self._main(fuzzable_request.get_url().base_url().url_string)

    def _main(self, url):
        '''
        This was taken from the original halberd, 'script/halberd' .
        '''
        scantask = halberd_scan_task.ScanTask()

        scantask.scantime = halberd_scan_task.default_scantime
        scantask.parallelism = halberd_scan_task.default_parallelism
        scantask.verbose = False
        scantask.debug = False
        scantask.conf_file = halberd_scan_task.default_conf_file
        scantask.cluefile = ''
        scantask.save = ''
        scantask.output = ''

        halberd_logger.set_error()
        scantask.read_conf()

        # UniScan
        scantask.url = url
        scantask.addr = ''
        scanner = halberd_shell.UniScanStrategy

        try:
            s = scanner(scantask)
        except halberd_shell.ScanError, msg:
            om.out.error('*** %s ***' % msg)
        else:
            #
            #       The scantask initialization worked, we can start the actual scan!
            #
            try:
                result = s.execute()
                # result should be: <Halberd.ScanTask.ScanTask instance at 0x85df8ec>
            except halberd_shell.ScanError, msg:
                om.out.debug('*** %s ***' % msg)
            else:
                self._report(result)

    def _report(self, scantask):
        """
        Displays detailed report information to the user and save the data to
        the kb.

        :return: None.
        """
        if len(scantask.analyzed) == 1:
            msg = '"%s" doesn\'t seem to have an HTTP load balancer'\
                  ' configuration.'
            om.out.information(msg % scantask.url)
        else:
            clues = scantask.analyzed
            hits = halberd_analysis.hits(clues)

            # In some strange cases, we have no clues about the remote
            # server. We just need to return in this case.
            if not len(clues):
                return

            # xxx This could be passed by the caller in order to avoid
            # recomputation in case the clues needed a re-analysis.
            diff_fields = halberd_analysis.diff_fields(clues)

            desc = 'Target URL for HTTP load balancer detection: %s\n'\
                   'Number of real server(s) detected: %d\n'\
                   'Server information:\n    %s'
            real_servers = '    %s\n' % scantask.addr
            desc = desc % (scantask.url, len(clues), real_servers)
            
            om.out.information(desc)

            for num, clue in enumerate(clues):
                assert hits > 0
                clue_info = clue.info

                om.out.information('')
                om.out.information(
                    'server %d: %s' % (num + 1, clue_info['server'].lstrip()))
                om.out.information('-' * 70 + '\n')

                om.out.information('difference: %d seconds' % clue.diff)

                om.out.information('successful requests: %d hits (%.2f%%)'
                                   % (clue.get_count(), clue.get_count() * 100 / float(hits)))

                if clue_info['contloc']:
                    om.out.information(
                        'content-location: %s' % clue_info['contloc'].lstrip())

                if len(clue_info['cookies']) > 0:
                    om.out.information('cookie(s):')
                for cookie in clue_info['cookies']:
                    om.out.information('  %s' % cookie.lstrip())

                om.out.information('header fingerprint: %s' % clue_info['digest'])

                different = [(field, value) for field, value in clue.headers
                             if field in diff_fields]
                if different:
                    om.out.information('different headers:')
                    idx = 1
                    for field, value in different:
                        om.out.information('  %d. %s:%s' % (idx, field, value))
                        idx += 1

                if scantask.debug:
                    tmp = StringIO.StringIO()
                    om.out.information('headers:')
                    pprint.pprint(clue.headers, stream=tmp, indent=2)
                    om.out.information(tmp)

            om.out.information('\n')
            
            # This is added so other w3af plugins can read the halberd results.
            # If needed by other plugins, I could fill up the info object with more
            # data about the different headers, time, etc...
            i = Info('HTTP load balancer detected', desc, 1, self.get_name())
            i['server'] = clue_info['server'].lstrip()
            i['server_number'] = len(clues)
            
            kb.kb.append(self, 'halberd', i)
            

    def get_long_desc(self):
        '''
        :return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin tries to find if an HTTP Load balancer is present.
        '''
