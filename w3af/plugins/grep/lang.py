"""
lang.py

Copyright 2006 Andres Riancho

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
from __future__ import with_statement

import guess_language

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404

UNKNOWN = 'unknown'


class lang(GrepPlugin):
    """
    Read N pages and determines the language the site is written in.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):
        GrepPlugin.__init__(self)

        # Internal variables
        self._exec = True
        self._tries_left = 25
        
    def grep(self, request, response):
        """
        Get the page indicated by the fuzzable_request and determine the language
        using the preposition list.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        """
        if not self._exec:
            return

        if not response.is_text_or_html():
            return

        if is_404(response):
            return

        body = response.get_clear_text_body()
        if body is None:
            return

        body = body.lower()

        try:
            guessed_lang = guess_language.guessLanguage(body)
        except IndexError:
            # I don't care about exception handling of the external lib
            guessed_lang = UNKNOWN

        with self._plugin_lock:
            if guessed_lang == UNKNOWN:
                # None means "I'm still trying"
                kb.kb.raw_write(self, 'lang', None)

                # Keep running until self._tries_left is zero
                self._tries_left -= 1

                if self._tries_left == 0:
                    msg = ('Could not determine the site language using the'
                           ' first 25 HTTP responses, not enough text to make'
                           ' a good analysis.')
                    om.out.debug(msg)

                    # unknown means I'll stop testing because I don't
                    # have any idea about the target's language
                    kb.kb.raw_write(self, 'lang', 'unknown')

                    self._exec = False
            else:
                # Only run until we find the page language
                self._exec = False

                msg = 'The page is written in: "%s".'
                om.out.information(msg % guessed_lang)
                kb.kb.raw_write(self, 'lang', guessed_lang)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin reads N pages and determines the language the site is
        written in. This is done by saving a list of prepositions in different
        languages, and counting the number of matches on every page.
        """
