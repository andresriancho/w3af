"""
threaded_impact.py

Copyright 2007 Andres Riancho

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
import threading


class ThreadedURLImpact(threading.Thread):
    """Impacts an URL in a different thread."""
    def __init__(self, w3af, tsup, tlow, event, fixContentLength):
        threading.Thread.__init__(self)
        self.daemon = True
        
        self.tsup = tsup
        self.tlow = tlow
        self.w3af = w3af
        self.event = event
        self.ok = False
        self.fixContentLength = fixContentLength

    def run(self):
        """Starts the thread."""
        try:
            self.httpResp = self.w3af.uri_opener.send_raw_request(self.tsup,
                                                                  self.tlow,
                                                                  self.fixContentLength)
            self.ok = True
        except Exception, e:
            self.exception = e
        finally:
            self.event.set()