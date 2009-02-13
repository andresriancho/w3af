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
import os
import cgi
import time
import md5
import urllib2, urllib
import cookielib
from core.controllers.misc.get_w3af_version import get_w3af_version
import core.data.url.handlers.MultipartPostHandler as MultipartPostHandler


class sourceforge(object):
    
    def __init__(self):
        '''
        This class is a wrapper for reporting bugs to sourceforge using python.
        
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
        url = 'https://sourceforge.net/account/login.php'
        values = {'return_to' : '',
            'ssl_status' : '',
            'form_loginname' : user, 
            'form_pw' : passwd,
            'login' : 'Log in'}

        data = urllib.urlencode(values)
        req = urllib2.Request(url, data)
        try:
            response = urllib2.urlopen(req)
            the_page = response.read()
        except:
            return False
        else:
            self.logged_in = 'Invalid username or password' not in the_page
            return self.logged_in
            
    def report_bug(self, user_title, user_description, w3af_version, traceback, filename):
        '''
        I use urllib2 instead of the w3af wrapper, because the error may be in there!
        
        @parameter user_title: The title that the user wants to use in the bug report
        @parameter user_description: The description for the bug that was provided by the user
        
        @return: The new bug URL if the bug report was successful, or None if something failed.
        '''
        
        # Handle the summary
        summary = '[Auto-Generated] Bug Report - '
        if user_title:
            summary += user_title
        else:
            # Generate the summary, the random token is added to avoid the
            # double click protection added by sourceforge.
            summary += md5.new( time.ctime() ).hexdigest()
            
        # Now we handle the details
        details = ''
        if user_description:
            details += 'User description: \n'+ user_description + '\n\n\n'
        
        details += 'Version information: \n' + w3af_version + '\n\n\n'
        details += 'Traceback: \n' + traceback
        
        # sourceforge rule #3759-3: Users that don't have logged in; can't send bugs using https.
        if self.logged_in:
            schema = 'https://'
        else:
            schema = 'http://'
        url = schema + 'sourceforge.net/tracker2/index.php'
        
        values = {'group_id' : '170274',
            'atid' : '853652',
            'func' : 'postadd', 
            'category_id':'1166485', 
            'artifact_group_id':'100', 
            'assigned_to':'100', 
            'priority':'5',
            'summary': summary,
            'details': details,
            'input_file': file(filename),
            'file_description':'Traceback',
            'submit':'Add Artifact' }
        
        if not self.logged_in:
            # anonymous bug reports are slightly different
            values.pop('priority')
            values.pop('assigned_to')

        req = urllib2.Request(url, values)
        try:
            response = urllib2.urlopen(req)
            the_page = response.read()
        except:
            return False
        
        if 'ERROR' not in the_page:
            # parse the tracking URL
            # (Artifact <a href="/tracker2/?func=detail&aid=2590539&group_id=170274&atid=853652">2590539</a>)
            re_result = re.findall('\\(Artifact <a href="(.*?)">\d*</a>\\)', the_page)
            if re_result:
                return 'https://sourceforge.net' + re_result[0]
            
            return None
        else:
            return None
