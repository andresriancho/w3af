"""
base.py

Copyright 2015 Andres Riancho

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


class BaseContext(object):
    CAN_BREAK = None

    def __init__(self, payload, context_content):
        """
        :param context_content: See get_context_content docs
        """
        self.payload = payload
        self.context_content = context_content

    def is_executable(self):
        """
        :return: True if the context is executable, True examples:
                    * foo(); PAYLOAD; bar();
                    * <div onmouseover="PAYLOAD">

                 False examples were we need to break from the context:
                    * foo('PAYLOAD');
                    * foo("PAYLOAD");
                    * /* PAYLOAD */
        """
        return False

    def can_break(self):
        """
        :return: True if we can break out
        """
        return self.any_in(self.CAN_BREAK, self.payload)

    def get_context_content(self):
        """
        Extract the current context text, handles at least the following values
        for the html variable:

            <script type="application/json">foo;PAYLOAD
            <script>foo();PAYLOAD
            <a href="foo();PAYLOAD
            <a href='foo();PAYLOAD
            <tag>foo();PAYLOAD

        Returning 'foo();PAYLOAD' in all.
        """
        return self.context_content

    def any_in(self, needle_list, html):
        """
        :param needle_list: A list of strings to match in html
        :param html: The HTML response
        :return: True if at least one of the needles is in the html
        """
        klass = self.__class__.__name__
        assert needle_list is not None, 'CAN_BREAK is None at %s' % klass

        for needle in needle_list:
            if needle in html:
                return True

        return False

    def all_in(self, needle_list, html):
        """
        :param needle_list: A list of strings to match in html
        :param html: The HTML response
        :return: True if all needles are in the html
        """
        klass = self.__class__.__name__
        assert needle_list is not None, 'CAN_BREAK is None at %s' % klass

        for needle in needle_list:
            if needle not in html:
                return False

        return True