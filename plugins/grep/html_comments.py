# coding: utf-8
'''
html_comments.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''
from __future__ import with_statement

import re

import core.controllers.output_manager as om
import core.data.parsers.parser_cache as parser_cache
import core.data.kb.knowledge_base as kb
import core.data.kb.info as info

from core.data.esmre.multi_in import multi_in
from core.data.db.temp_shelve import temp_shelve
from core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from core.controllers.plugins.grep_plugin import GrepPlugin
from core.controllers.exceptions import w3afException


class html_comments(GrepPlugin):
    '''
    Find HTML comments.

    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    HTML_RE = re.compile('<[a-zA-Z]*.*?>.*?</[a-zA-Z]>')

    INTERESTING_WORDS = (
        'user', 'pass', 'xxx', 'fix', 'bug', 'broken', 'oops', 'hack',
        'caution', 'todo', 'note', 'warning', '!!!', '???', 'shit',
        'stupid', 'tonto', 'porqueria', 'ciudado', 'usuario', 'contrase',
        'puta', 'secret', '@', 'email', 'security', 'captcha', 'pinga',
        'cojones',
        # some in Portuguese
        'banco', 'bradesco', 'itau', 'visa', 'bancoreal', u'transfêrencia',
        u'depósito', u'cartão', u'crédito', 'dados pessoais'
    )

    _multi_in = multi_in(INTERESTING_WORDS)

    def __init__(self):
        GrepPlugin.__init__(self)

        # Internal variables
        self._comments = temp_shelve()
        self._already_reported_interesting = ScalableBloomFilter()

    def grep(self, request, response):
        '''
        Plugin entry point, parse those comments!

        @param request: The HTTP request object.
        @param response: The HTTP response object
        @return: None
        '''
        if response.is_text_or_html():
            try:
                dp = parser_cache.dpc.get_document_parser_for(response)
            except w3afException:
                return
            else:
                for comment in dp.get_comments():
                    # These next two lines fix this issue:
                    # audit.ssi + grep.html_comments + web app with XSS = false positive
                    if request.sent(comment):
                        continue

                    # show nice comments ;)
                    comment = comment.strip()

                    if self._is_new(comment, response):

                        self._interesting_word(comment, request, response)
                        self._html_in_comment(comment, request, response)

    def _interesting_word(self, comment, request, response):
        '''
        Find interesting words in HTML comments
        '''
        comment = comment.lower()
        for word in self._multi_in.query(response.body):
            if (word, response.get_url()) not in self._already_reported_interesting:
                i = info.info()
                i.set_plugin_name(self.get_name())
                i.set_name('HTML comment with "' + word + '" inside')
                msg = 'A comment with the string "' + \
                    word + '" was found in: "'
                msg += response.get_url() + '". This could be interesting.'
                i.set_desc(msg)
                i.set_id(response.id)
                i.set_dc(request.get_dc)
                i.set_uri(response.get_uri())
                i.add_to_highlight(word)
                kb.kb.append(self, 'interesting_comments', i)
                om.out.information(i.get_desc())
                self._already_reported_interesting.add(
                    (word, response.get_url()))

    def _html_in_comment(self, comment, request, response):
        '''
        Find HTML code in HTML comments
        '''
        html_in_comment = self.HTML_RE.search(comment)
        if html_in_comment and \
                (comment, response.get_url()) not in self._already_reported_interesting:
            # There is HTML code in the comment.
            i = info.info()
            i.set_plugin_name(self.get_name())
            i.set_name('HTML comment contains HTML code')
            comment = comment.replace('\n', '')
            comment = comment.replace('\r', '')
            desc = 'A comment with the string "' + comment + \
                '" was found in: "'
            desc += response.get_url() + '" . This could be interesting.'
            i.set_desc(desc)
            i.set_id(response.id)
            i.set_dc(request.get_dc)
            i.set_uri(response.get_uri())
            i.add_to_highlight(html_in_comment.group(0))
            kb.kb.append(self, 'html_comment_hides_html', i)
            om.out.information(i.get_desc())
            self._already_reported_interesting.add(
                (comment, response.get_url()))

    def _is_new(self, comment, response):
        '''
        Make sure that we perform a thread safe check on the self._comments dict,
        in order to avoid duplicates.
        '''
        with self._plugin_lock:
            if comment not in self._comments.keys():
                self._comments[comment] = [(response.get_url(), response.id), ]
                return True
            else:
                if response.get_url() not in [x[0] for x in self._comments[comment]]:
                    self._comments[comment].append((
                        response.get_url(), response.id))
                    return True

        return False

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        @return: None
        '''
        inform = []
        for comment in self._comments.iterkeys():
            urls_with_this_comment = self._comments[comment]
            stick_comment = ' '.join(comment.split())
            if len(stick_comment) > 40:
                msg = 'A comment with the string "%s..." (and %s more bytes) was found on these URL(s):'
                om.out.information(
                    msg % (stick_comment[:40], str(len(stick_comment) - 40)))
            else:
                msg = 'A comment containing "%s" was found on these URL(s):' % (stick_comment)
                om.out.information(msg)

            for url, request_id in urls_with_this_comment:
                inform.append('- ' + url +
                              ' (request with id: ' + str(request_id) + ')')

            inform.sort()
            for i in inform:
                om.out.information(i)

    def get_long_desc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin greps every page for HTML comments, special comments like
        the ones containing the words "password" or "user" are specially reported.
        '''
