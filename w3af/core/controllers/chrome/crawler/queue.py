"""
queue.py

Copyright 2019 Andres Riancho

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


class CrawlerHTTPTrafficQueue(object):
    def __init__(self, http_traffic_queue):
        self.http_traffic_queue = http_traffic_queue
        self.count = 0

    def put(self, request_response):
        self.count += 1

        # msg = 'Received HTTP traffic from chrome in output queue. Count is %s (did: %s)'
        # args = (self.count, self.debugging_id)
        # om.out.debug(msg % args)

        return self.http_traffic_queue.put(request_response)

    def __getattr__(self, name):
        return getattr(self.http_traffic_queue, name)
