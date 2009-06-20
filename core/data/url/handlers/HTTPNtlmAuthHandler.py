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
# License along with this library.  If not, see <http://www.gnu.org/licenses/> or <http://www.gnu.org/licenses/lgpl.txt>.

import urllib2
import httplib, socket
from urllib import addinfourl
import ntlm

class AbstractNtlmAuthHandler:
    
    def __init__(self, password_mgr=None):
        if password_mgr is None:
            password_mgr = HTTPPasswordMgr()
        self.passwd = password_mgr
        self.add_password = self.passwd.add_password

    def http_error_authentication_required(self, auth_header_field, req, fp, headers):
        auth_header_value = headers.get(auth_header_field, None)
        if auth_header_field:
            if 'ntlm' in auth_header_value.lower():
                fp.close()
                return self.retry_using_http_NTLM_auth(req, auth_header_field, None, headers)

    def retry_using_http_NTLM_auth(self, req, auth_header_field, realm, headers):
        user, pw = self.passwd.find_user_password(realm, req.get_full_url())
        if pw is not None:
            # ntlm secures a socket, so we must use the same socket for the complete handshake
            headers = dict(req.headers)
            headers.update(req.unredirected_hdrs)
            auth = 'NTLM %s' % ntlm.create_NTLM_NEGOTIATE_MESSAGE(user)
            if req.headers.get(self.auth_header, None) == auth:
                return None
            headers[self.auth_header] = auth
            
            host = req.get_host()
            if not host:
                raise urllib2.URLError('no host given')
            h = None
            if req.get_full_url().startswith('https://'):
                h = httplib.HTTPSConnection(host) # will parse host:port
            else:
                h = httplib.HTTPConnection(host) # will parse host:port
            # we must keep the connection because NTLM authenticates the connection, not single requests
            headers["Connection"] = "Keep-Alive"
            headers = dict((name.title(), val) for name, val in headers.items())
            h.request(req.get_method(), req.get_selector(), req.data, headers)
            r = h.getresponse()
            r.begin()
            r._safe_read(int(r.getheader('content-length')))
            if r.getheader('set-cookie'): 
                # this is important for some web applications that store authentication-related info in cookies (it took a long time to figure out)
                headers['Cookie'] = r.getheader('set-cookie')
            r.fp = None # remove the reference to the socket, so that it can not be closed by the response object (we want to keep the socket open)
            auth_header_value = r.getheader(auth_header_field, None)
            (ServerChallenge, NegotiateFlags) = ntlm.parse_NTLM_CHALLENGE_MESSAGE(auth_header_value[5:])
            user_parts = user.split('\\', 1)
            DomainName = user_parts[0].upper()
            UserName = user_parts[1]
            auth = 'NTLM %s' % ntlm.create_NTLM_AUTHENTICATE_MESSAGE(ServerChallenge, UserName, DomainName, pw, NegotiateFlags)
            headers[self.auth_header] = auth
            headers["Connection"] = "Close"
            headers = dict((name.title(), val) for name, val in headers.items())
            try:
                h.request(req.get_method(), req.get_selector(), req.data, headers)
                # none of the configured handlers are triggered, for example redirect-responses are not handled!
                response = h.getresponse()
                def notimplemented():
                    raise NotImplementedError
                response.readline = notimplemented
                return addinfourl(response, response.msg, req.get_full_url())
            except socket.error, err:
                raise urllib2.URLError(err)
        else:
            return None


class HTTPNtlmAuthHandler(AbstractNtlmAuthHandler, urllib2.BaseHandler):

    auth_header = 'Authorization'

    def http_error_401(self, req, fp, code, msg, headers):
        return self.http_error_authentication_required('www-authenticate', req, fp, headers)


class ProxyNtlmAuthHandler(AbstractNtlmAuthHandler, urllib2.BaseHandler):
    """ 
        CAUTION: this class has NOT been tested at all!!! 
        use at your own risk
    """
    auth_header = 'Proxy-authorization'

    def http_error_407(self, req, fp, code, msg, headers):
        return self.http_error_authentication_required('proxy-authenticate', req, fp, headers)


if __name__ == "__main__":
    url = "http://ntlmprotectedserver/securedfile.html"
    user = u'DOMAIN\\User'
    password = 'Password'

    passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, url, user , password)
    auth_basic = urllib2.HTTPBasicAuthHandler(passman)
    auth_digest = urllib2.HTTPDigestAuthHandler(passman)
    auth_NTLM = HTTPNtlmAuthHandler(passman)
    
    # disable proxies (just for testing)
    proxy_handler = urllib2.ProxyHandler({}) 

    opener = urllib2.build_opener(proxy_handler, auth_NTLM) #, auth_digest, auth_basic)
    
    urllib2.install_opener(opener)
    
    response = urllib2.urlopen(url)
    print(response.read())