"""
moth.py

Copyright 2013 Andres Riancho

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

FMT = '/tmp/moth-%s.txt'
HTTP_ADDRESS_FILE = FMT % 'http'
HTTPS_ADDRESS_FILE = FMT % 'https'

DEFAULT_MOTH = 'fallback:80'
DEFAULT_MOTHS = 'fallback:443'


def whereis_moth():
    """
    :return: The net location for the moth http and https daemon. For example,
             if the HTTP Django application was started on 127.0.0.1 port 8083
             and listens HTTPS on port 8341 we return:
             
             {'http': '127.0.0.1:8083',
              'https': '127.0.0.1:8341',}
            
             We need this function because when we run on CI we don't really
             know which ports are going to be free for the server to bind.
    """
    try:
        moth = file(HTTP_ADDRESS_FILE).read().strip()
    except IOError:
        moth = None
    
    try:
        moths = file(HTTPS_ADDRESS_FILE).read().strip()
    except IOError:
        moths = None
    
    return {'http': moth or DEFAULT_MOTH,
            'https': moths or DEFAULT_MOTHS}


def get_moth_http(path='/'):
    return 'http://%s%s' % (whereis_moth()['http'], path)


def get_moth_https(path='/'):
    return 'https://%s%s' % (whereis_moth()['https'], path)
