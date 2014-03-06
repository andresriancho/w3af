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
        if not self.got_lang():
            return

        # I added the 404 code here to avoid doing some is_404 lookups
        if response.get_code() not in {500, 401, 403, 404} \
        and not is_404(response) and request.get_method() in {'POST', 'GET'}:

            # Run the plugins
            data = self._run_plugins(response)

            with self._plugin_lock:
                old_data = kb.kb.raw_read('password_profiling',
                                          'password_profiling')

                new_data = self.merge_maps(old_data, data, request,
                                           self.captured_lang)

                new_data = self._trim_data(new_data)

                # save the updated map
                kb.kb.raw_write(self, 'password_profiling', new_data)

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
                kb.kb.raw_write(self, 'password_profiling', {})
                self._need_init = False
                return True
        
        return True
    
    def _trim_data(self, data):
        """
        If the dict grows a lot, I want to trim it. Basically, if
        it grows to a length of more than 2000 keys, I'll trim it
        to 1000 keys.
        """
        if len(data) > 2000:
            def sortfunc(x_obj, y_obj):
                return cmp(y_obj[1], x_obj[1])
            
            # pylint: disable=E1103
            items = data.items()
            items.sort(sortfunc)

            items = items[:1000]

            new_data = {}
            for key, value in items:
                new_data[key] = value

        else:
            new_data = data
    
        return new_data
                
    def merge_maps(self, old_data, data, request, lang):
        """
        "merge" both maps and update the repetitions
        """
        if lang not in self.COMMON_WORDS.keys():
            lang = 'unknown'
            
        for d in data:

            if len(d) >= 4 and d.isalnum() and \
            not d.isdigit() and \
            d.lower() not in self.BANNED_WORDS and \
            d.lower() not in self.COMMON_WORDS[lang] and \
            not request.sent(d):

                if d in old_data:
                    old_data[d] += data[d]
                else:
                    old_data[d] = data[d]
        
        return old_data
    
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
            wordMap = plugin.get_words(response)
            if wordMap is not None:
                # If a plugin returned something thats not None, then we are done.
                # this plugins only return a something different of None of they
                # found something
                res = wordMap
                break

        return res

    def end(self):
        """
        This method is called when the plugin wont be used anymore.
        """
        def sortfunc(x_obj, y_obj):
            return cmp(y_obj[1], x_obj[1])

        profiling_data = kb.kb.raw_read('password_profiling', 'password_profiling')

        # This fixes a very strange bug where for some reason the kb doesn't
        # have a dict anymore (threading issue most likely) Seen here:
        # https://sourceforge.net/apps/trac/w3af/ticket/171745
        if isinstance(profiling_data, dict):
            
            # pylint: disable=E1103
            items = profiling_data.items()
            if len(items) != 0:

                items.sort(sortfunc)
                om.out.information('Password profiling TOP 100:')

                list_length = len(items)
                if list_length > 100:
                    xLen = 100
                else:
                    xLen = list_length

                for i in xrange(xLen):
                    msg = '- [' + str(i + 1) + '] ' + items[
                        i][0] + ' with ' + str(items[i][1])
                    msg += ' repetitions.'
                    om.out.information(msg)

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
