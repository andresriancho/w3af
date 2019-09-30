"""
halberd.py

Copyright 2014 Andres Riancho

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
from __future__ import absolute_import

import os
import tempfile

import Halberd.shell as halberd_shell
import Halberd.logger as halberd_logger
import Halberd.ScanTask as halberd_scan_task

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.misc.temp_dir import get_temp_dir
from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.misc.decorators import runonce
from w3af.plugins.infrastructure.halberd_helpers.strategy import CustomScanStrategy
from w3af.core.data.kb.info import Info


class halberd(InfrastructurePlugin):
    """
    Identify if the remote server has HTTP load balancers.

    This plugin is a wrapper of Juan M. Bello Rivas' halberd.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request, debugging_id):
        """
        It calls the "main" from halberd and writes the results to the kb.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        msg = 'halberd plugin is starting. Original halberd author: ' \
              'Juan M. Bello Rivas; http://halberd.superadditive.com/'
        om.out.information(msg)

        self._main(fuzzable_request.get_url().base_url().url_string)

    def _main(self, url):
        """
        This was taken from the original halberd, 'script/halberd' .
        """
        scantask = halberd_scan_task.ScanTask()

        scantask.scantime = halberd_scan_task.default_scantime
        scantask.parallelism = halberd_scan_task.default_parallelism
        scantask.verbose = False
        scantask.debug = True
        scantask.conf_file = halberd_scan_task.default_conf_file
        scantask.cluefile = ''
        scantask.save = ''

        temp_output = tempfile.NamedTemporaryFile(delete=False,
                                                  dir=get_temp_dir(),
                                                  prefix='w3af-halberd-',
                                                  suffix='.output')
        scantask.out = temp_output.name

        halberd_logger.setError()
        try:
            scantask.readConf()
        except halberd_scan_task.ConfError, e:
            # halberd: 'unable to create a default conf. file'
            # https://github.com/andresriancho/w3af/issues/9988
            om.out.error('Failed to initialize Halberd configuration: "%s"' % e)
            return

        # UniScan
        scantask.url = url
        scantask.addr = ''
        scanner = CustomScanStrategy

        try:
            s = scanner(scantask)
        except halberd_shell.ScanError, msg:
            om.out.error('Halberd error: %s' % msg)
            return

        # The scantask initialization worked, we can start the actual scan!
        try:
            s.execute()
        except halberd_shell.ScanError, msg:
            om.out.debug('Halberd error: %s' % msg)
            return

        self._report(s.task, temp_output.name)

    def _report(self, scantask, report_file):
        """
        Displays detailed report information to the user and save the data to
        the kb.

        :return: None.
        """
        halberd_report = file(report_file).read()
        os.unlink(report_file)
        om.out.information(halberd_report)

        clues = scantask.analyzed
        if len(clues) > 1:

            # This is added so other w3af plugins can read the halberd results.
            # If needed by other plugins, I could fill up the info object with
            # more data about the different headers, time, etc...
            i = Info('HTTP load balancer detected', halberd_report, 1,
                     self.get_name())
            i['server_number'] = len(clues)

            kb.kb.append(self, 'halberd', i)
            
    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin tries to find if an HTTP Load balancer is present.

        One important thing to notice is that halberd connects directly to the
        remote web server, without using the framework's HTTP configurations
        (like proxy or authentication).
        """
