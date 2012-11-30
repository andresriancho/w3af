'''
sourceforge.py

Copyright 2008 Andres Riancho

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
import cookielib
import hashlib
import re
import socket
import string
import time
import urllib2
import urllib
import xmlrpclib

import core.data.url.handlers.MultipartPostHandler as MultipartPostHandler
from core.controllers.exception_handling.helpers import VERSIONS

#
#    Yeah, yeah, I know that this sucks but it's the best we could do...
#
DEFAULT_USER_NAME = 'w3afbugsreport'
DEFAULT_PASSWD = 'w3afs1nce2006'


class Sourceforge(object):

    CREATED_TKT = 'http://sourceforge.net/apps/trac/w3af/ticket/'
    # Error report body
    WIKI_DETAILS_TEMPLATE = string.Template(
        '''== User description: ==
$user_desc
[[BR]][[BR]]
== Version Information: ==
{{{
$w3af_v
}}}
[[BR]][[BR]]
== Traceback: ==
{{{
$t_back
}}}
== Enabled Plugins: ==
{{{
$plugins
}}}''')

    def __init__(self, username=None, passwd=None):
        self.username = username or ''
        self.passwd = passwd or ''
        self.logged_in = False

    def login(self):
        raise NotImplementedError

    def report_bug(self, summary, userdesc, tback='',
                   fname=None, plugins='', autogen=True):
        raise NotImplementedError

    def _build_summary_and_desc(self, summary, desc, tback,
                                fname, plugins, autogen, email):
        '''
        Build the formatted summary and description that will be
        part of the reported bug.
        '''
        #
        #    Define which summary to use
        #
        if summary:
            bug_summary = summary
        else:
            # Try to extract the last line from the traceback:
            if tback:
                bug_summary = tback.split('\n')[-2]
            else:
                # Failed... lets generate something random!
                m = hashlib.md5()
                m.update(time.ctime())
                bug_summary = m.hexdigest()

        # Generate the summary string. Concat 'user_title'. If empty, append a
        # random token to avoid the double click protection added by sourceforge.
        summary = '%sBug Report - %s' % (
            autogen and '[Auto-Generated] ' or '',
            bug_summary)

        #
        #    Define which description to use (depending on the availability of an
        #    email provided by the user or not).
        #
        if email is not None:
            email_fmt = '\n\nThe user provided the following email address for contact: %s'
            desc += email_fmt % email

        #
        #    Apply all the info
        #
        bdata = {'plugins': plugins, 't_back': tback,
                 'user_desc': desc, 'w3af_v': VERSIONS}

        # Build details string
        details = self.WIKI_DETAILS_TEMPLATE.safe_substitute(bdata)

        return summary, details


class SourceforgeXMLRPC(Sourceforge):

    LOGIN_URL = "https://%s:%s@sourceforge.net/apps/trac/w3af/login/xmlrpc"

    def __init__(self, username, passwd):
        Sourceforge.__init__(self, username, passwd)
        self._proxy = None

    def login(self):
        self._proxy = xmlrpclib.ServerProxy(
            SourceforgeXMLRPC.LOGIN_URL % (self.username, self.passwd)
        )
        # Test if the login was successful
        try:
            self._proxy.system.listMethods()
            self.logged_in = True
        except xmlrpclib.ProtocolError:
            return False
        except socket.gaierror:
            print 'Error resolving DNS name for sourceforge. Is your DNS properly set?'
            return False
        return self.logged_in

    def report_bug(self, summary, userdesc, tback='',
                   fname=None, plugins='', autogen=True, email=None):
        assert self.logged_in, "You should login first"

        summary, desc = self._build_summary_and_desc(
            summary, userdesc, tback, fname, plugins,
            autogen, email)

        values = {
            'type': 'defect',
            'status': 'new',
            'component': 'automatic-bug-report',
            'milestone': '',
            'priority': 'major',
        }
        try:
            newticket = self._proxy.ticket.create(summary, desc,
                                                  values, True)
            return str(newticket), self.CREATED_TKT + str(newticket)
        except xmlrpclib.ProtocolError:
            return None


