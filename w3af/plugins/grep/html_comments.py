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

from w3af.core.data.quick_match.multi_in import MultiIn
from w3af.core.data.db.disk_dict import DiskDict
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.kb.info import Info
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.controllers.exceptions import (BaseFrameworkException,
                                              NoSuchTableException)


class html_comments(GrepPlugin):
    """
    Extract and analyze HTML comments.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    HTML_RE = re.compile('<[a-zA-Z]+ .*?>.*?</[a-zA-Z]+>')

    HTML_FALSE_POSITIVES = {
        '[if IE]',
        '[if !IE]',
        '[if IE 7 ]',
        '[if IE 8 ]',
        '[if IE 9]',
        '[if lte IE 8]',
        '[if lte IE 9]',
    }

    INTERESTING_WORDS = (
        # In English
        'user', 'pass', 'xxx', 'fix', 'bug', 'broken', 'oops', 'hack',
        'caution', 'todo', 'note', 'warning', '!!!', '???', 'shit',
        'pass', 'password', 'passwd', 'pwd', 'secret', 'stupid',
        
        # In Spanish
        'tonto', 'porqueria', 'cuidado', 'usuario', u'contraseña',
        'puta', 'email', 'security', 'captcha', 'pinga', 'cojones',
        
        # In Portuguese
        'banco', 'bradesco', 'itau', 'visa', 'bancoreal', u'transfêrencia',
        u'depósito', u'cartão', u'crédito', 'dados pessoais'
    )

    _multi_in = MultiIn([' %s ' % w for w in INTERESTING_WORDS])

    def __init__(self):
        GrepPlugin.__init__(self)

        # Internal variables
        self._comments = DiskDict(table_prefix='html_comments')
        self._already_reported = ScalableBloomFilter()
        self._end_was_called = False

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
            if self._is_new(comment, response):
                self._interesting_word(comment, request, response)
                self._html_in_comment(comment, request, response)

    def _interesting_word(self, comment, request, response):
        """
        Find interesting words in HTML comments
        """
        lower_comment = comment.lower()

        for word in self._multi_in.query(lower_comment):
            if (word, response.get_url()) in self._already_reported:
                continue

            # These next two lines fix a false positive which appears when
            # audit.ssi sends a payload to a site which has XSS, and
            # grep.html_comments sees that comment and reports it.
            if request.sent(comment):
                continue

            self._already_reported.add((word, response.get_url()))

            desc = ('A comment with the string "%s" was found in: "%s".'
                    ' This could be interesting.')
            desc %= (word, response.get_url())

            i = Info.from_fr('Interesting HTML comment', desc, response.id,
                             self.get_name(), request)
            i.add_to_highlight(word)

            kb.kb.append(self, 'interesting_comments', i)
            om.out.information(i.get_desc())

    def _html_in_comment(self, comment, request, response):
        """
        Find HTML code in HTML comments
        """
        html_in_comment = self.HTML_RE.search(comment)

        if html_in_comment is None:
            return

        for false_positive_string in self.HTML_FALSE_POSITIVES:
            if false_positive_string in comment:
                return

        comment_data = (comment, response.get_url())

        if comment_data in self._already_reported:
            return

        self._already_reported.add(comment_data)

        # There is HTML code in the comment.
        comment = comment.strip()
        comment = comment.replace('\n', '')
        comment = comment.replace('\r', '')
        comment = comment[:40]

        desc = ('A comment containing HTML code "%s" was found in: "%s".'
                ' This could be interesting.')
        desc %= (comment, response.get_url())

        i = Info.from_fr('HTML comment contains HTML code', desc, response.id,
                         self.get_name(), request)
        i.set_uri(response.get_uri())
        i.add_to_highlight(html_in_comment.group(0))

        kb.kb.append(self, 'html_comment_hides_html', i)
        om.out.information(i.get_desc())

    def _handle_no_such_table(self, comment, response, nste):
        """
        I had a lot of issues trying to reproduce [0], so this code is just
        a helper for me to identify the root cause.

        [0] https://github.com/andresriancho/w3af/issues/10849

        :param nste: The original exception
        :param comment: The comment we're analyzing
        :param response: The HTTP response
        :return: None, an exception with more information is re-raised
        """
        msg = ('A NoSuchTableException was raised by the DBMS. This issue is'
               ' related with #10849 , but since I was unable to reproduce'
               ' it, extra debug information is added to the exception:'
               '\n'
               '\n - Grep plugin end() was called: %s'
               '\n - Response ID is: %s'
               '\n - HTML comment is: "%s"'
               '\n - Original exception: "%s"'
               '\n\n'
               'https://github.com/andresriancho/w3af/issues/10849\n')
        args = (self._end_was_called,
                response.get_id(),
                comment,
                nste)

        raise NoSuchTableException(msg % args)

    def _is_new(self, comment, response):
        """
        Avoid duplicates by checking self._comments
        """
        # pylint: disable=E1103
        try:
            comment_data = self._comments.get(comment, None)
        except NoSuchTableException, nste:
            self._handle_no_such_table(comment, response, nste)
            return

        response_url = response.get_url()

        # The comment was never seen before
        if comment_data is None:
            self._comments[comment] = [(response_url, response.id)]
            return True

        # The comment was seen before, maybe on a different URL
        for saved_url, response_id in comment_data:
            if response_url == saved_url:
                return False

        # The comment was never seen before on this URL, store this knowledge
        comment_data.append((response_url, response.id))
        self._comments[comment] = comment_data

        return True
        # pylint: enable=E1103

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

        self._end_was_called = True
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
