"""
password_profiling.py

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

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.controllers.misc.factory import factory
from w3af.core.data.constants.common_words import common_words


class password_profiling(GrepPlugin):
    """
    Create a list of possible passwords by reading HTTP response bodies.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    COMMON_WORDS = common_words
    COMMON_WORDS['unknown'] = COMMON_WORDS['en']

    BANNED_WORDS = {'forbidden', 'browsing', 'index'}
    BANNED_STATUS = {500, 401, 403, 404}
    ALLOWED_METHODS = {'POST', 'GET'}

    def __init__(self):
        GrepPlugin.__init__(self)
        
        self._need_init = True
        self.captured_lang = None
        
        # TODO: develop more plugins, there is a, pure-python metadata reader
        # named hachoir-metadata it will be useful for writing A LOT of plugins
        
        # Plugins to run
        self._plugins_names_dict = ['html', 'pdf']
        self._plugins = []

    def grep(self, request, response):
        """
        Plugin entry point. Get responses, analyze words, create dictionary.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None.
        """
        # I added the 404 code here to avoid doing some is_404 lookups
        if response.get_code() in self.BANNED_STATUS:
            return

        if request.get_method() not in self.ALLOWED_METHODS:
            return

        if not self.got_lang():
            return

        if is_404(response):
            return

        # Run the password profiling plugins
        data = self._run_plugins(response)

        with self._plugin_lock:
            old_data = kb.kb.raw_read(self, self.get_name())

            new_data = self.merge_maps(old_data, data, request, self.captured_lang)
            new_data = self._trim_data(new_data)

            # save the updated map
            kb.kb.raw_write(self, self.get_name(), new_data)

    def got_lang(self):
        """
        Initial setup that's run until we have the language or lang plugin
        gave up
        
        :return: True if we were able to get the language from the lang plugin
        """
        if self._need_init:
            captured_lang = kb.kb.raw_read('lang', 'lang')
            if captured_lang is None or captured_lang == []:
                # The lang plugin is still trying to identify the language
                return False
            else:
                self.captured_lang = captured_lang
                kb.kb.raw_write(self.get_name(), self.get_name(), {})
                self._need_init = False
                return True
        
        return True
    
    def _trim_data(self, data):
        """
        If the password profiling information dict grows too large, we want to
        trim it. Basically, if it grows to a length of more than N keys, trim it
        to M keys.
        """
        if len(data) < 2000:
            return data

        # pylint: disable=E1103
        items = data.items()
        items.sort(sort_func)

        items = items[:1000]

        new_data = {}

        for key, value in items:
            new_data[key] = value

        return new_data
                
    def merge_maps(self, old_data, data, request, lang):
        """
        "merge" both maps and update the repetitions, the maps contain:
            * Key:   word
            * Value: number of repetitions
        """
        for word in data:

            if self._should_ignore_word(word, lang, request):
                continue

            if word in old_data:
                old_data[word] += data[word]
            else:
                old_data[word] = data[word]
        
        return old_data

    def _should_ignore_word(self, word, lang, request):
        """
        Some common, short, etc. words should be ignored.

        :param word: The work to query
        :return: True if it should be ignored
        """
        if len(word) < 4:
            return True

        if not word.isalnum():
            return True

        if word.isdigit():
            return True

        lower_word = word.lower()

        if lower_word in self.BANNED_WORDS:
            return True

        if lang not in self.COMMON_WORDS:
            lang = 'unknown'

        if lower_word in self.COMMON_WORDS[lang]:
            return True

        if request.sent(word):
            return True

        return False

    def _run_plugins(self, response):
        """
        Runs password profiling plugins to collect data from HTML, TXT,
        PDF, etc files.
        
        :param response: A HTTPResponse object
        :return: A map with word:repetitions
        """
        # Create plugin instances only once
        if not self._plugins:
            for plugin_name in self._plugins_names_dict:
                plugin_klass = 'w3af.plugins.grep.password_profiling_plugins.%s'
                plugin_instance = factory(plugin_klass % plugin_name)
                self._plugins.append(plugin_instance)

        res = {}

        for plugin in self._plugins:
            word_map = plugin.get_words(response)
            if word_map is not None:
                # If a plugin returned something that's not None, then we are
                # done. These plugins only return a something different from
                # None if they found something
                res = word_map
                break

        return res

    def end(self):
        """
        This method is called when the plugin wont be used anymore.
        """
        profiling_data = kb.kb.raw_read(self, self.get_name())

        if not profiling_data:
            return

        # pylint: disable=E1103
        items = profiling_data.items()
        items.sort(sort_func)
        items = items[:100]

        om.out.information('Password profiling TOP 100:')

        for i, (password, repetitions) in enumerate(items):
            msg = ' - [%s] %s with %s repetitions'
            args = (i + 1, password, repetitions)
            om.out.information(msg % args)

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins that should be run before
                 the current one.
        """
        return ['grep.lang']

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin creates a list of possible passwords by reading responses
        and counting the most common words.
        """


def sort_func(x_obj, y_obj):
    return cmp(y_obj[1], x_obj[1])
