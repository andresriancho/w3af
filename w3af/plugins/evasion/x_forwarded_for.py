"""
x_forwarded_for.py

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
import random

from w3af.core.controllers.plugins.evasion_plugin import EvasionPlugin


class x_forwarded_for(EvasionPlugin):
    """
    Add an X-Forwarded-For header with random IP to every request.

    @author: m3tamantra (m3tamantra@gmail.com )
    """
    def __init__(self):
        EvasionPlugin.__init__(self)

        """
        random.seed(..) is used to generate the same IP addresses in every scan
        otherwise the plugin could generate false negatives
        (scan #1 finds bug because of some specific IP it's sent in the header; 
        and then scan #2 doesn't send the same IP and the bug is not found).
        """
        self.random = random.Random()
        self.random.seed(42)
        
    def modify_request(self, request):
        """
        Add X-Forwarded-For header if the request doesn't have one
        """
        if not request.has_header('X-forwarded-for'):
            request.add_header('X-forwarded-for', self.get_random_ip())

        return request
    
    def get_random_ip(self):
        ret_ip = ''

        for _ in range(4):
            ret_ip += '%d.' % (self.random.randint(1, 254))

        return ret_ip[:-1]
        
    def get_priority(self):
        return 86
    
    def get_long_desc(self):
        return """
        This plugin adds an X-Forwarded-For header to every request (except when
        it already has one). It generates a new random IP for every request.
        The plugin can be handy if the target has some kind of "one request per
        host" feature.

        Example server side code:
            if(isset($_SERVER['HTTP_X_FORWARDED_FOR'])){
                $ip = explore(',', $_SERVER['HTTP_X_FORWARDED_FOR'])[0];
            } else {
                $ip = $_SERVER['REMOTE_ADDR'];
            }

        Example plugin run:
        
            Input:
                GET / HTTP/1.1
                ...
                
            Output:
                GET / HTTP/1.1
                X-Forwarded-For: 12.34.56.78
                ...
        """
