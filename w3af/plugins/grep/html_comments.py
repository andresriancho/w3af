# coding: utf-8
"""
html_comments.py

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

import re

import w3af.core.controllers.output_manager as om
import w3af.core.data.parsers.parser_cache as parser_cache
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.data.esmre.multi_in import multi_in
from w3af.core.data.db.disk_dict import DiskDict
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.kb.info import Info
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException


class html_comments(GrepPlugin):
    """
    Extract and analyze HTML comments.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    HTML_RE = re.compile('<[a-zA-Z]*.*?>.*?</[a-zA-Z]>')

    INTERESTING_WORDS = (
        # In English
        'user', 'pass', 'xxx', 'fix', 'bug', 'broken', 'oops', 'hack',
        'caution', 'todo', 'note', 'warning', '!!!', '???', 'shit',
        'pass', 'password', 'passwd', 'pwd', 'secret', 'stupid',
        
        # In Spanish
        'tonto', 'porqueria', 'cuidado', 'usuario', u'contraseña',
        'puta', 'email', 'security', 'captcha', 'pinga', 'cojones',
        
        # some in Portuguese
        'banco', 'bradesco', 'itau', 'visa', 'bancoreal', u'transfêrencia',
        u'depósito', u'cartão', u'crédito', 'dados pessoais'
    )

    _multi_in = multi_in([' %s ' % w for w in INTERESTING_WORDS])

    def __init__(self):
        GrepPlugin.__init__(self)

        # Internal variables
        self._comments = DiskDict(table_prefix='html_comments')
        self._already_reported = ScalableBloomFilter()

    def grep(self, request, response):
        """
        Plugin entry point, parse those comments!

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        if not response.is_text_or_html():
            return
        
        try:
            dp = parser_cache.dpc.get_document_parser_for(response)
        except BaseFrameworkException:
            return
        
        for comment in dp.get_comments():
            # These next two lines fix this issue:
            # audit.ssi + grep.html_comments + web app with XSS = false positive
            if request.sent(comment):
                continue

            if self._is_new(comment, response):

                self._interesting_word(comment, request, response)
                self._html_in_comment(comment, request, response)

    def _interesting_word(self, comment, request, response):
        """
        Find interesting words in HTML comments
        """
        comment = comment.lower()

        for word in self._multi_in.query(comment):
            if (word, response.get_url()) in self._already_reported:
                continue

            desc = ('A comment with the string "%s" was found in: "%s".'
                    ' This could be interesting.')
            desc %= (word, response.get_url())

            i = Info.from_fr('Interesting HTML comment', desc, response.id,
                             self.get_name(), request)
            i.add_to_highlight(word)

            kb.kb.append(self, 'interesting_comments', i)
            om.out.information(i.get_desc())
                
            self._already_reported.add((word, response.get_url()))

    def _html_in_comment(self, comment, request, response):
        """
        Find HTML code in HTML comments
        """
        html_in_comment = self.HTML_RE.search(comment)

        if html_in_comment is None:
            return

        if (comment, response.get_url()) in self._already_reported:
            return

        # There is HTML code in the comment.
        comment = comment.strip()
        comment = comment.replace('\n', '')
        comment = comment.replace('\r', '')
        comment = comment[:40]

        desc = ('A comment with the string "%s" was found in: "%s".'
                ' This could be interesting.')
        desc %= (comment, response.get_url())

        i = Info.from_fr('HTML comment contains HTML code', desc, response.id,
                         self.get_name(), request)
        i.set_uri(response.get_uri())
        i.add_to_highlight(html_in_comment.group(0))

        kb.kb.append(self, 'html_comment_hides_html', i)
        om.out.information(i.get_desc())
        self._already_reported.add((comment, response.get_url()))

    def _is_new(self, comment, response):
        """
        Make sure that we perform a thread safe check on the self._comments
        dict, in order to avoid duplicates.
        """
        with self._plugin_lock:
            
            #pylint: disable=E1103
            comment_data = self._comments.get(comment, None)
            response_url = response.get_url()

            if comment_data is None:
                self._comments[comment] = [(response_url, response.id)]
                return True
            else:
                for saved_url, response_id in comment_data:
                    if response_url == saved_url:
                        return False
                else:
                    comment_data.append((response_url, response.id))
                    self._comments[comment] = comment_data
                    return True
            #pylint: enable=E1103

    def end(self):
        """
        This method is called when the plugin wont be used anymore.
        :return: None
        """
        for comment, url_request_id_lst in self._comments.iteritems():

            stick_comment = ' '.join(comment.split())

            if len(stick_comment) > 40:
                msg = ('A comment with the string "%s..." (and %s more bytes)'
                       ' was found on these URL(s):')
                args = (stick_comment[:40], str(len(stick_comment) - 40))
                om.out.information(msg % args)
            else:
                msg = 'A comment containing "%s" was found on these URL(s):'
                om.out.information(msg % stick_comment)

            inform = []

            for url, request_id in url_request_id_lst:
                msg = '- %s (request with id: %s)'
                inform.append(msg % (url, request_id))

            for i in sorted(inform):
                om.out.information(i)

        self._comments.cleanup()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every page for HTML comments, special comments like
        the ones containing the words "password" or "user" are specially
        reported.
        """
