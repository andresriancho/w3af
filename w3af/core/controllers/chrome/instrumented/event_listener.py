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
import Levenshtein

from w3af.core.data.misc.encoding import smart_str_ignore


class EventListener(object):
    """
    Wrapper around the dict that comes from Chrome and contains:

       {u'event_type': u'click',
        u'tag_name': u'div',
        u'handler': u'noop();',
        u'node_type': 1,
        u'selector': u'[onclick="noop\\(\\)\\;"]'}
    """

    MAX_HANDLER_EDIT_DISTANCE = 2
    MAX_SELECTOR_EDIT_DISTANCE = 5
    MAX_TEXT_CONTENT_EDIT_DISTANCE = 3

    __slots__ = (
        '_event_as_dict'
    )

    def __init__(self, event_as_dict):
        self._event_as_dict = event_as_dict

    def get_type_selector(self):
        return (self._event_as_dict['event_type'],
                self._event_as_dict['selector'],)

    def fuzzy_matches(self, other):
        """
        Compare two events and return true when:

            * The event_type is the same
            * The tag_name is the same
            * The handler attribute needs to be similar
            * The selector attribute needs to be similar

        :param other: Another instance of EventListener
        :return: True if the events are similar
        """
        if self.get('event_type') != other.get('event_type'):
            return False

        if self.get('tag_name') != other.get('tag_name'):
            return False

        if not self._are_similar(self.get('handler', default=''),
                                 other.get('handler', default=''),
                                 self.MAX_HANDLER_EDIT_DISTANCE):
            return False

        if not self._are_similar(self.get('selector', default=''),
                                 other.get('selector', default=''),
                                 self.MAX_SELECTOR_EDIT_DISTANCE):
            return False

        if not self._are_similar(self.get('text_content', default=''),
                                 other.get('text_content', default=''),
                                 self.MAX_TEXT_CONTENT_EDIT_DISTANCE):
            return False

        return True

    def _are_similar(self, str_a, str_b, max_edit_distance):
        if str_a == str_b:
            return True

        str_a = smart_str_ignore(str_a)
        str_b = smart_str_ignore(str_b)

        # pylint: disable=E1101
        edit_distance = Levenshtein.distance(str_a, str_b)
        # pylint: enable=E1101

        if edit_distance <= max_edit_distance:
            return True

        return False

    def __getitem__(self, item):
        return self._event_as_dict[item]

    def __getattr__(self, item):
        try:
            return self._event_as_dict[item]
        except KeyError:
            raise AttributeError('%s is not a known attribute' % item)

    def get(self, item, default=None):
        if item not in self._event_as_dict:
            return default

        return self._event_as_dict.get(item)

    def __setitem__(self, key, value):
        self._event_as_dict[key] = value

    def keys(self):
        return self._event_as_dict.keys()

    def __eq__(self, other):
        if set(other.keys()) != set(self._event_as_dict.keys()):
            return False

        for key, value in self._event_as_dict.iteritems():
            #
            # The event_source (where this event was found) is not important
            # when comparing events. Events are equal if they are of the same
            # type, are sent to the same selector and have the same URI
            #
            if key == 'event_source':
                continue

            other_value = other.get(key)

            if value != other_value:
                return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __len__(self):
        return len(self._event_as_dict)

    def __repr__(self):
        return 'EventListener(%r)' % self._event_as_dict
