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


class SourceforgeHTTP(Sourceforge):

    # URLs
    LOGGED_IN_PROTOCOL = 'https'
    ANON_PROTOCOL = 'http'

    LOGIN_PAGE = 'https://sourceforge.net/account/login.php'
    NEW_TKT_URL = '://sourceforge.net/apps/trac/w3af/newticket'

    # Form token regex
    FORM_TOKEN_RE = 'name="__FORM_TOKEN"\svalue="(\w*?)"'
    # Created ticket regex
    NEW_TICKET_RE = '://sourceforge.net/apps/trac/w3af/attachment/ticket/(\d*?)\?action=new'
    NEW_ATTACHMENT_URL_FORMAT = 'http://sourceforge.net/apps/trac/w3af/attachment/ticket/%s/?action=new&attachfilebutton=Attach+file'

    def __init__(self, username, passwd):
        '''
        This class is a wrapper for reporting bugs to sourceforge's TRAC
        using python.

        @author: Andres Riancho (andres.riancho@gmail.com)
        '''
        Sourceforge.__init__(self, username, passwd)

        # Init the urllib2 module
        self._init_urllib2_handlers()

    def get_new_ticket_url(self):
        if self.logged_in:
            return self.LOGGED_IN_PROTOCOL + self.NEW_TKT_URL
        else:
            return self.ANON_PROTOCOL + self.NEW_TKT_URL

    def get_ticket_re(self):
        if self.logged_in:
            return self.LOGGED_IN_PROTOCOL + self.NEW_TICKET_RE
        else:
            return self.ANON_PROTOCOL + self.NEW_TICKET_RE

    def _init_urllib2_handlers(self):
        # Build the cookie handler
        cj = cookielib.LWPCookieJar()
        cookie_handler = urllib2.HTTPCookieProcessor(cj)

        # Build the multipart post handler
        multi_handler = MultipartPostHandler.MultipartPostHandler()
        redir_handler = urllib2.HTTPRedirectHandler()

        self.opener = urllib2.build_opener(multi_handler,
                                           cookie_handler,
                                           redir_handler)

    def login(self):
        '''
        Perform a login to the sourceforge page using the provided user and password.

        Once the user has logged in, the session is kept using the urllib2 cookie handler,
        nothing special has to be done regarding that.

        @param user: The user
        @param passwd: The password

        @return: True if successful login, false otherwise.
        '''
        values = {'return_to': '',
                  'ssl_status': '',
                  'form_loginname': self.username,
                  'form_pw': self.passwd,
                  'login': 'Log in'}
        try:
            resp = self._do_request(self.LOGIN_PAGE, values)
        except:
            return False
        else:
            self.logged_in = 'Invalid username or password' not in resp.read()
            return self.logged_in

    def report_bug(self, summary, userdesc, tback='', fname=None,
                   plugins='', autogen=True, user=None):
        '''
        I use urllib2 instead of the w3af wrapper, because the error may be in there!

        @param summary: The title that the user wants to use in the bug report
        @param userdesc: The description for the bug that was provided by the
            user
        @param tback: Error traceback string.
        @param fname: File containing useful error data. To be attached to the
            bug report.
        @param plugins: Formatted string with the activated plugins.
        @param autogen: Whether this bug was automatically generated, i.e.,
            w3af crashed.

        @return: The new ticket URL if the bug report was successful, or None
            if something failed.

        '''

        summary, details = self._build_summary_and_desc(
            summary, userdesc, tback, fname, plugins, autogen
        )

        resp = self._do_request(self.get_new_ticket_url())
        form_token = self._get_match_from_response(
            resp.read(), self.FORM_TOKEN_RE) or ''

        values = {
            'field_component': 'automatic-bug-report',
            'field_milestone': '',
            'field_type': 'defect',
            'field_status': 'new',
            'field_priority': 'major',
            'field_summary': summary,
            'field_description': details,
            'author': user or 'anonymous',
            '__FORM_TOKEN': form_token,
            'attachment': fname and 'on' or 'off',
            'attachment': 'off',
            'submit': 'Create ticket'}

        resp = self._do_request(self.get_new_ticket_url(), values)

        # If everything went well a ticket_id must be present
        match = re.search(self.get_ticket_re(), resp.geturl())
        if match:
            ticket_id = match.group(1)

            if fname:
                NEW_ATTACHMENT_URL = self.NEW_ATTACHMENT_URL_FORMAT % ticket_id
                self._attach_file(
                    NEW_ATTACHMENT_URL, ticket_id, fname, form_token)

            return ticket_id, self.CREATED_TKT + ticket_id

        return None, None

    def _attach_file(self, url, ticket_id, filename, form_token):
        '''
        Attach file to ticket <ticket_id>
        '''
        values = {
            'attachment': [file(filename)],
            'description': ['Error Traceback'],
            'action': ['new'],
            'realm': ['ticket'],
            '__FORM_TOKEN': [form_token],
            'id': [ticket_id],
            'author': [getattr(self, 'logged_in_user', 'anonymous')],
            'submit': ['Add attachment']}

        req = urllib2.Request(url, values)
        req.add_header('Referer', url)
        self.opener.open(req)

    def _get_match_from_response(self, response_body, pattern):
        '''Try to match <pattern> in the response's body. Return the
        matched string. If no match is found return None.
        '''
        mo = re.search(pattern, response_body)
        return (mo.groups()[0] if mo else None)

    def _do_request(self, url, data=None):
        '''
        Perform request to <url> using <data>.
        Raises URLError on errors.
        '''
        if data:
            data = urllib.urlencode(data)

        req = urllib2.Request(url, data)
        resp = self.opener.open(req)
        return resp
