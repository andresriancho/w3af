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
import re
import string
import time
import hashlib
import urllib2, urllib
import cookielib
import core.data.url.handlers.MultipartPostHandler as MultipartPostHandler


class sourceforge(object):
    
    # URLs
    LOGIN_PAGE = 'https://sourceforge.net/account/login.php'
    NEW_TKT_URL = 'https://sourceforge.net/apps/trac/w3af/newticket'
    CREATED_TKT = 'https://sourceforge.net/apps/trac/w3af/ticket/'
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
    # Form token regex
    FORM_TOKEN_RE = 'name="__FORM_TOKEN"\svalue="(\w*?)"'
    # Created ticket regex
    NEW_TICKET_RE = 'Add\sAttachment\sto\s<a href="/apps/trac/w3af/ticket/(\d*?)">Ticket'
    
    def __init__(self):
        '''
        This class is a wrapper for reporting bugs to sourceforge's TRAC
        using python.
        
        @author: Andres Riancho ( andres.riancho@gmail.com )
        '''
        # Internal variables
        self.logged_in = False
        
        # Init the urllib2 module
        self._init_urllib2_handlers()
        
    def _init_urllib2_handlers(self):
        # Build the cookie handler
        cj = cookielib.LWPCookieJar()
        cookie_handler = urllib2.HTTPCookieProcessor(cj)
        
        # Build the multipart post handler
        multi_handler = MultipartPostHandler.MultipartPostHandler()
        
        opener = apply(urllib2.build_opener, (multi_handler,cookie_handler) )
        urllib2.install_opener(opener)

    def login(self, user, passwd):
        '''
        Perform a login to the sourceforge page using the provided user and password.
        
        Once the user has logged in, the session is kept using the urllib2 cookie handler,
        nothing special has to be done regarding that.
        
        @parameter user: The user
        @parameter passwd: The password
        
        @return: True if successful login, false otherwise.
        '''
        values = {'return_to': '',
            'ssl_status': '',
            'form_loginname': user, 
            'form_pw': passwd,
            'login': 'Log in'}
        try:
            resp = self._do_request(self.LOGIN_PAGE, values)
        except:
            return False
        else:
            self.logged_in = 'Invalid username or password' not in resp.read()
            return self.logged_in
            
    def report_bug(self, user_title, filename, **body_data):
        '''
        I use urllib2 instead of the w3af wrapper, because the error may be in there!
        
        @parameter user_title: The title that the user wants to use in the bug report
        @parameter user_description: The description for the bug that was provided by the user
        @parameter body_data: keyword args to be used to be used in report's body
        
        @return: The new ticket URL if the bug report was successful, or None if something failed.
        '''
        
        m = hashlib.md5()
        m.update(time.ctime())
        random = m.hexdigest() 

        # Handle the summary. Concat 'user_title'. If empty, append a random
        # token to avoid the double click protection added by sourceforge.
        summary = '[Auto-Generated] Bug Report - %s' % \
            (user_title or random)
        
        # Build details string
        details = self.WIKI_DETAILS_TEMPLATE.safe_substitute(body_data)
        resp = self._do_request(self.NEW_TKT_URL)
        form_token = self._get_match_from_response(resp, self.FORM_TOKEN_RE) or ''
        
        values = {
            'field_component': 'automatic-bug-report',
            'field_milestone': '',
            'field_type': 'defect',
            'field_status': 'new',
            'field_priority': 'major',
            'field_summary': summary,
            'field_description': details,
            '__FORM_TOKEN': form_token,
            'attachment': 'on',
            'submit': 'Create ticket'}

        resp = self._do_request(self.NEW_TKT_URL, values)
        # If evrything went weel a ticket_id must be present        
        ticket_id = self._get_match_from_response(resp, self.NEW_TICKET_RE)

        if ticket_id:
            attach_file_url = resp.geturl()
            self._attach_file(attach_file_url, ticket_id, filename, form_token)
            return self.CREATED_TKT + ticket_id
        return None
        
    def _attach_file(self, url, ticket_id, filename, form_token):
        '''Attach file to ticket <ticket_id>
        '''
        values = {
            'attachment': [file(filename)],
            'description': ['Error Traceback'],
            'action': ['new'],
            'realm': ['ticket'],
            '__FORM_TOKEN': [form_token],
            'id': [ticket_id],
            'submit': ['Add attachment']}
        
        req = urllib2.Request(url, values)
        urllib2.urlopen(req)
    
    def _get_match_from_response(self, response, pattern):
        '''Try to match <pattern> in the response's body. Return the 
        matched string. If no match is found return None.
        '''
        the_page = response.read()
        mo = re.search(pattern, the_page)
        return (mo.groups()[0] if mo else None)

    def _do_request(self, url, data=None):
        '''Do request to <url> using <data>.
        Raises URLError on errors.
        '''
        if data:
            data = urllib.urlencode(data)

        req = urllib2.Request(url, data)
        resp = urllib2.urlopen(req)
        return resp
