# This library is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.  If not, see <http://www.gnu.org/licenses/>
# or <http://www.gnu.org/licenses/lgpl.txt>.

import urllib2
from ntlm import ntlm


class AbstractNtlmAuthHandler(urllib2.BaseHandler):
    """
    urllib2 handler which adds NTLM v1 support.
    
    NTLM v2 is NOT supported since the "ntlm" library does NOT support it.
    Nathaniel Cole confirmed this in the w3af-users mailing list.
    """
    
    auth_header = None

    def __init__(self, password_mgr=None):
        if password_mgr is None:
            password_mgr = urllib2.HTTPPasswordMgr()
        self.passwd = password_mgr
        self.add_password = self.passwd.add_password
        self.retried = 0

    def reset_retry_count(self):
        self.retried = 0

    def http_request(self, request):
        ntlm_auth_header = request.get_header(self.auth_header, None)
        if ntlm_auth_header is None:
            user, pw = self.passwd.find_user_password(None, request.get_full_url())
            if pw is not None:
                auth = 'NTLM %s' % ntlm.create_NTLM_NEGOTIATE_MESSAGE(user)
                request.add_unredirected_header(self.auth_header, auth)
        return request
    
    https_request = http_request

    def http_error_auth_reqed(self, auth_header_field, url, req, headers):
        if self.retried > 3:
            # Don't fail endlessly - if we failed once, we'll probably
            # fail a second time. Hm. Unless the Password Manager is
            # prompting for the information. Crap. This isn't great
            # but it's better than the current 'repeat until recursion
            # depth exceeded' approach <wink>
            raise urllib2.HTTPError(req.get_full_url(), 401,
                                    "NTLM auth failed",
                                    headers, None)
        else:
            self.retried += 1

        auth_header_value = headers.get(auth_header_field, None)
        
        if auth_header_field and 'ntlm' in auth_header_value.lower():
            return self.retry_using_http_NTLM_auth(req, auth_header_field,
                                                   None, headers)
        
    def retry_using_http_NTLM_auth(self, request, auth_header_field, realm, headers):
        auth_header_value = headers.getheader(auth_header_field, None)
        if auth_header_value is not None:
            server_data = auth_header_value[5:]
            try:
                challenge, flags = ntlm.parse_NTLM_CHALLENGE_MESSAGE(server_data)
            except:
                # Invalid protocol
                return None
            else:
                user, pw = self.passwd.find_user_password(None, request.get_full_url())
                user_parts = user.split('\\', 1)
                domain_name = user_parts[0].upper()
                user_name = user_parts[1]
                auth = 'NTLM %s' % ntlm.create_NTLM_AUTHENTICATE_MESSAGE(challenge,
                                                                         user_name,
                                                                         domain_name,
                                                                         pw, flags)
                request.add_unredirected_header(self.auth_header, auth)
                return self.parent.open(request, timeout=request.timeout)
        else:
            return None


class HTTPNtlmAuthHandler(AbstractNtlmAuthHandler):

    auth_header = 'Authorization'
        
    def http_error_401(self, req, fp, code, msg, headers):
        url = req.get_full_url()
        response = self.http_error_auth_reqed('www-authenticate',
                                              url, req, headers)
        self.reset_retry_count()
        return response


