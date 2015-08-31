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
from functools import wraps


class BaseContext(object):
    CAN_BREAK = None

    @staticmethod
    def is_executable(html):
        return False

    def can_break(self, payload):
        return self.any_in(self.CAN_BREAK, payload)

    @staticmethod
    def match(data):
        raise NotImplementedError('match() MUST be implemented')

    @staticmethod
    def is_inside_context(html, context_start, context_end):
        """
        :return: True if we perform a reverse find of context_start
                 (ie '<script'), then a reverse find of context_end (ie.
                 '</script>') and the second has a lower index; meaning we're
                 still in the context of '<script>' tag

        :param context_start: Would be '<script' in the example above
        :param context_end: Would be '</script>' in the example above
        """
        context_start_idx = html.rfind(context_start)
        if context_start_idx == -1:
            return False

        context_end_idx = html.rfind(context_end)
        if context_end_idx == -1:
            # The tag opens and never closes
            return True

        # The tag does close, but maybe we have multiple opens/closes and we
        # need to verify that the current tag is not closed
        if context_end_idx < context_start_idx:
            return True

        if context_start_idx == context_end_idx:
            return True

        return False

    @staticmethod
    def is_inside_nested_contexts(html, context_starts, context_ends):
        """
        Will return True if we're inside all defined contexts, for example if
        we have this HTML:

            <script src="PAYLOAD" />

        And we want to know if we're inside the <script context AND the tag
        attribute value context we specify {'<script', '"'}

        The order for context starts and ends is important because this method
        makes sure they are respected.

        :return: True if we're inside the N specified contexts (in order)
        :param context_starts: Would be ['<script', '"'] in the example above
        :param context_ends: Would be ['</script>', '"'] in the example above
        """
        assert len(context_starts) == len(context_ends)

        # First we make sure we're in all the specified contexts
        for context_start, context_end in zip(context_starts, context_ends):
            if not BaseContext.is_inside_context(html,
                                                 context_start,
                                                 context_end):
                return False

        # Now we guarantee order
        previous_idx = None
        for context_start in context_starts:
            child_idx = html.rfind(context_start)

            if previous_idx is None:
                previous_idx = child_idx
            elif previous_idx < child_idx:
                continue
            else:
                return False

        return True

    @staticmethod
    def get_context_content(html, context_start, context_end,
                            context_start_cut=None):
        """
        Extract the current context text, handles at least the following values
        for the html variable:

            <script type="application/json">foo;PAYLOAD
            <script>foo();PAYLOAD
            <a href="foo();PAYLOAD
            <a href='foo();PAYLOAD
            <tag>foo();PAYLOAD

        Returning 'foo();PAYLOAD' in all.

        :param html: The html to extract the data from
        :param context_start: See is_inside_context
        :param context_end: See is_inside_context
        """
        assert BaseContext.is_inside_context(html, context_start, context_end)

        context_start_idx = html.rfind(context_start)
        ctx_start_end = context_start_idx+len(context_start)

        if context_start_cut is None:
            return html[ctx_start_end:]

        context_start_cut_idx = html[ctx_start_end:].find(context_start_cut)

        msg = 'Context start cut "%s" not found!' % context_start_cut
        assert context_start_cut_idx != -1, msg

        return html[ctx_start_end:][context_start_cut_idx+1:]

    @staticmethod
    def get_attr_name(html, attr_delim):
        """
        :return: The name of the attribute where the payload lives, for example
                 if the html variable contains '<a href="PAYLOAD' we'll return
                 'href'
        """
        # First we make sure we're getting called in a context that makes sense
        assert BaseContext.is_inside_context(html, '<', '>')

        # Analyze the context data
        attr_delim_idx = html.rfind(attr_delim)

        # Now I iterate the string in reverse order to find the "=" and then the
        # attribute name, ignoring spaces which might be between the attr_delim
        # and the =, and the attribute name and the =. Examples we need to cover
        # are:
        #       <a href="
        #       <a href= "
        #       <a href = "
        attr_name = ''
        eq_found = False
        until_attr_delim = html[:attr_delim_idx]

        for char_idx in reversed(xrange(len(until_attr_delim))):
            char = until_attr_delim[char_idx]

            if char == '=':
                eq_found = True
                continue

            elif char == ' ' and not eq_found:
                # We're between attr delim and =
                continue

            elif char == ' ' and attr_name:
                # The attr name has finished
                break

            elif char == ' ' and eq_found:
                # We're between = and the start of the attr name
                continue

            elif char != ' ':
                attr_name += char

        assert eq_found, 'The attribute equals character was not found.'

        return attr_name[::-1]

    @staticmethod
    def is_inside_html_comment(html):
        """
        :return: True if we're inside an HTML comment, return true in at least
                 the following examples:

                    <html><!-- foo --></html>
                    <html><script><!-- foo --></script></html>
        """
        return BaseContext.is_inside_context(html, '<!--', '-->')

    @staticmethod
    def any_in(needle_list, html):
        """
        :param needle_list: A list of strings to match in html
        :param html: The HTML response
        :return: True if at least one of the needles is in the html
        """
        for needle in needle_list:
            if needle in html:
                return True

        return False


def outside_comment_context(func):
    @wraps(func)
    def inner(html):
        if BaseContext.is_inside_html_comment(html):
            return False

        return func(html)

    return inner