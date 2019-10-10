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
from w3af.core.data.kb.info_set import InfoSet
from w3af.core.data.kb.info import Info
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException


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
            self._interesting_word(comment, request, response)
            self._html_in_comment(comment, request, response)

    def _interesting_word(self, comment, request, response):
        """
        Find interesting words in HTML comments
        """
        lower_comment = comment.lower()

        for word in self._multi_in.query(lower_comment):
            # These next two lines fix a false positive which appears when
            # audit.ssi sends a payload to a site which has XSS, and
            # grep.html_comments sees that comment and reports it.
            if request.sent(comment):
                continue

            desc = ('A comment with the string "%s" was found in: "%s".'
                    ' This could be interesting.')
            desc %= (word, response.get_url())

            i = Info.from_fr('Interesting HTML comment',
                             desc,
                             response.id,
                             self.get_name(),
                             request)
            i.add_to_highlight(word)
            i[HTMLCommentHidesHTMLInfoSet.ITAG] = comment

            self.kb_append_uniq_group(self,
                                      'interesting_comments',
                                      i,
                                      group_klass=HTMLCommentHidesHTMLInfoSet)

    def _html_in_comment(self, comment, request, response):
        """
        Find HTML code in HTML comments
        """
        #
        # Check if HTML code is present in this comment
        #
        html_in_comment = self.HTML_RE.search(comment)

        if html_in_comment is None:
            return

        #
        # Remove false positives
        #
        for false_positive_string in self.HTML_FALSE_POSITIVES:
            if false_positive_string in comment:
                return

        #
        # There is HTML code in the comment, report it
        #
        comment = comment.strip()
        comment = comment.replace('\n', '')
        comment = comment.replace('\r', '')
        comment = comment[:40]

        desc = ('A comment containing HTML code "%s" was found in: "%s".'
                ' This could be interesting.')
        desc %= (comment, response.get_url())

        i = Info.from_fr('HTML comment contains HTML code',
                         desc,
                         response.id,
                         self.get_name(),
                         request)
        i.set_uri(response.get_uri())
        i.add_to_highlight(html_in_comment.group(0))
        i[HTMLCommentHidesHTMLInfoSet.ITAG] = comment

        self.kb_append_uniq_group(self,
                                  'html_comment_hides_html',
                                  i,
                                  group_klass=HTMLCommentHidesHTMLInfoSet)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin extracts HTML comments and reports interesting comments
        that include words such as "password" or "secret", or include HTML
        tags.
        """


class HTMLCommentHidesHTMLInfoSet(InfoSet):
    ITAG = 'html_comment'
    TEMPLATE = (
        'A total of {{ uris|length }} HTTP requests contained an HTML comment'
        ' that includes HTML tags: "{{ html_comment }}". The first ten matching'
        ' URLs are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )


class HTMLCommentInterestingWordInfoSet(InfoSet):
    ITAG = 'word'
    TEMPLATE = (
        'A total of {{ uris|length }} HTTP requests contained an HTML comment '
        ' that included the interesting word "{{ word }}". The first ten matching'
        ' URLs are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )
