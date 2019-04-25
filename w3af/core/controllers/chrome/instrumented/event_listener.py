"""
event_listener.py

Copyright 2018 Andres Riancho

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


class EventListener(object):
    def __init__(self, event_as_dict):
        self._event_as_dict = event_as_dict

    def get_type_selector(self):
        return (self._event_as_dict['event_type'],
                self._event_as_dict['selector'],)

    def __getitem__(self, item):
        return self._event_as_dict[item]

    def get(self, item):
        return self._event_as_dict.get(item)

    def __setitem__(self, key, value):
        self._event_as_dict[key] = value

    def __eq__(self, other):
        if len(other) != len(self._event_as_dict):
            return False

        for key, value in self._event_as_dict.iteritems():
            other_value = other.get(key)

            if value != other_value:
                return False

        return True

    def __len__(self):
        return len(self._event_as_dict)

    def __repr__(self):
        return 'EventListener(%r)' % self._event_as_dict
