"""
email_report.py

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
import smtplib

from email.mime.text import MIMEText

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.kb.config as cf

from w3af.core.controllers.plugins.output_plugin import OutputPlugin
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList


class email_report(OutputPlugin):
    """
    Email report to specified addresses.

    :author: Taras (oxdef@oxdef.info)
    """

    MSG_TMPL = """Hello!
    Target: %s has some vulnerabilities.

    """

    def __init__(self):
        OutputPlugin.__init__(self)

        self.targets = []
        self._exec = False

        self.smtpServer = 'localhost'
        self.smtpPort = 25
        self.toAddrs = ''
        self.fromAddr = ''

    def log_enabled_plugins(self, plugins_dict, options_dict):
        self.targets = cf.cf.get('targets')

    def set_options(self, option_list):
        self.smtpServer = option_list['smtpServer'].get_value()
        self.smtpPort = option_list['smtpPort'].get_value()
        self.fromAddr = option_list['fromAddr'].get_value()
        self.toAddrs = option_list['toAddrs'].get_value()

    def get_options(self):
        ol = OptionList()

        d = 'SMTP server ADDRESS to send notifications through, e.g.' \
            ' smtp.yourdomain.com'
        o = opt_factory('smtpServer', self.smtpServer, d, 'string')
        ol.add(o)

        d = 'SMTP server PORT'
        o = opt_factory('smtpPort', self.smtpPort, d, 'integer')
        ol.add(o)

        d = 'Recipient email address'
        o = opt_factory('toAddrs', self.toAddrs, d, 'list')
        ol.add(o)

        d = '"From" email address'
        o = opt_factory('fromAddr', self.fromAddr, d, 'string')
        ol.add(o)

        return ol

    def end(self):
        if not self.targets or self._exec:
            return
        self._exec = True

        data = self.MSG_TMPL % (self.targets[0])
        # Only vulnerabilities are sent via email, the info objects we don't
        # care about in this output plugin. Modify this, or add a configuration
        # setting if you do.
        vulns = kb.kb.get_all_vulns()

        for v in vulns:
            data += v.get_desc() + '\n'

        msg = MIMEText(data)
        msg['From'] = self.fromAddr
        msg['To'] = ', '.join(self.toAddrs)
        msg['Subject'] = 'w3af report on %s' % self.targets[0]

        try:
            server = smtplib.SMTP(self.smtpServer, self.smtpPort)
            server.sendmail(self.fromAddr, self.toAddrs, msg.as_string())
            server.quit()
        except Exception, e:
            msg = 'The SMTP settings in email_report plugin seem to be'\
                  ' incorrect. Original error: "%s".'
            om.out.error(msg % e)

    def get_long_desc(self):
        return """
        This plugin sends short report (only vulnerabilities) by email to
        specified addresses.

        There are some configurable parameters:
            - smtpServer
            - smtpPort
            - toAddrs
            - fromAddr
        """

    def do_nothing(self, *args, **kwds):
        pass

    debug = information = error = vulnerability = console = do_nothing
