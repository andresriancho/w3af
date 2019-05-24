"""
state.py

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
from collections import deque


class CrawlerState(object):
    """
    An object that keeps the crawler state.
    """

    MAX_EVENT_DISPATCH_LOG_EVENTS = 1000

    def __init__(self):
        self._event_dispatch_log = deque(maxlen=self.MAX_EVENT_DISPATCH_LOG_EVENTS)

    def get_event_dispatch_log(self):
        return self._event_dispatch_log

    def append_event_to_log(self, event_dispatch_log_unit):
        return self._event_dispatch_log.append(event_dispatch_log_unit)

    def event_in_log(self, event_dispatch_log_unit):
        return event_dispatch_log_unit in self._event_dispatch_log

    def __getitem__(self, val):
        try:
            return self._event_dispatch_log[val]
        except TypeError:
            # The deque does not support slices (eg. abc[1:2])
            return list(self._event_dispatch_log)[val]

    def __len__(self):
        return len(self._event_dispatch_log)

    def __iter__(self):
        for event_dispatch_log_unit in self._event_dispatch_log:
            yield event_dispatch_log_unit
