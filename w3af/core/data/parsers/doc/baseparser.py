# -*- coding: UTF-8 -*-
"""
baseparser.py

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
import urllib

from w3af.core.data.constants.encodings import UTF8
from w3af.core.data.misc.encoding import is_known_encoding

NOT_IMPLEMENTED_FMT = 'You should create your own parser class ' \
                      'and implement the %s() method.'


class BaseParser(object):
    """
    This class is an abstract document parser.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    SAFE_CHARS = (('\x00', '%00'),)

    def __init__(self, http_response):

        encoding = http_response.get_charset()
        if not is_known_encoding(encoding):
            raise ValueError('Unknown encoding: %s' % encoding)

        # "set_base_url"
        url = http_response.get_url()
        redir_url = http_response.get_redir_url()
        if redir_url:
            url = redir_url

        self._base_url = url
        self._base_domain = url.get_domain()
        self._root_domain = url.get_root_domain()
        self._encoding = http_response.get_charset()

        # Store the http response, this shouldn't be so bad since we're only
        # storing ParserCache.LRU_LENGTH in memory and not storing responses
        # which have more than ParserCache.MAX_CACHEABLE_BODY_LEN in length
        self._http_response = http_response

    def get_http_response(self):
        return self._http_response

    @staticmethod
    def can_parse(http_resp):
        """
        :return: True if this parser can extract links from the http_response
        """
        raise NotImplementedError

    def _decode_url(self, url_string):
        """
        Decode `url_string` using urllib's url-unquote
        algorithm. The returned value is always a unicode string.

        See http://www.blooberry.com/indexdot/html/topics/urlencoding.htm for
        more info on urlencoding.

        So, when _decode_url() is called and take as input
        u'http://host.tld/%05%44', it is encoded using the instance's _encoding
        then it is applied the unquote routine and finally is decoded back to
        unicode being u'http://host.tld/é' the final result.

        Something small to remember:
        >>> urllib.unquote('ind%c3%a9x.html').decode('utf-8').encode('utf-8') \
        == 'ind\xc3\xa9x.html'
        True

        """
        enc = self._encoding

        if isinstance(url_string, unicode):
            url_string = url_string.encode(enc)

        dec_url = urllib.unquote(url_string)
        for sch, repl in self.SAFE_CHARS:
            dec_url = dec_url.replace(sch, repl)

        # Always return unicode
        # TODO: Any improvement for this? We're certainly losing
        # information by using the 'ignore' error handling

        try:
            dec_url = dec_url.decode(UTF8)
        except UnicodeDecodeError:
            dec_url = dec_url.decode(enc, 'ignore')
        #
        # TODO: Lines below will remain commented until we make a
        # decision regarding which is the (right?) way to decode URLs.
        # The tests made on FF and Chrome revealed that if strange
        # (i.e. non ASCII) characters are present in a URL the browser
        # will urlencode the URL string encoded until the beginning
        # of the query string using the page charset and the query
        # string itself encoded in UTF-8.
        #
        # Apparently this is not a universal practice. We've found
        # some static sites having URL's encoded *only* in Windows-1255
        # (hebrew) for example.
        #
        # This is what de W3C recommends (not a universal practice though):
        #    http://www.w3.org/TR/REC-html40/appendix/notes.html#h-B.2
        #
##        index = dec_url.find('?')
##        if index > -1:
##            dec_url = (dec_url[:index].decode(enc, 'ignore') +
##                       dec_url[index:].decode('utf-8', 'ignore'))

        return dec_url

    def get_forms(self):
        """
        :return: A list of forms.
        """
        raise NotImplementedError(NOT_IMPLEMENTED_FMT % 'get_forms')

    def get_references(self):
        """
        Searches for references on a page. w3af searches references in every
        html tag, including:
            - a
            - forms
            - images
            - frames
            - etc.

        :return: Two sets, one with the parsed URLs, and one with the URLs that
                 came out of a regular expression. The second list if less
                 trustworthy.
        """
        raise NotImplementedError(NOT_IMPLEMENTED_FMT % 'get_references')

    def get_emails(self, domain=None):
        """
        :return: A set with email addresses
        """
        raise NotImplementedError(NOT_IMPLEMENTED_FMT % 'get_emails')

    def get_comments(self):
        """
        :return: A list of comments.
        """
        raise NotImplementedError(NOT_IMPLEMENTED_FMT % 'get_comments')

    def get_meta_redir(self):
        """
        :return: Returns list of meta redirections.
        """
        raise NotImplementedError(NOT_IMPLEMENTED_FMT % 'get_meta_redir')

    def get_meta_tags(self):
        """
        :return: Returns list of all meta tags.
        """
        raise NotImplementedError(NOT_IMPLEMENTED_FMT % 'get_meta_tags')

    def _return_empty_list(self, *args, **kwds):
        """
        Some parsers don't implement some of the features, so they can add
        something like:

        get_forms = _return_empty_list

        At the class definition, and simply return an empty list.
        """
        return []

    def get_clear_text_body(self):
        """
        :return: A clear text representation of the HTTP response body.
        """
        raise NotImplementedError(NOT_IMPLEMENTED_FMT % 'get_clear_text_body')

    def clear(self):
        """
        Called when the parser won't be used anymore, it should clear all the
        open files, sockets, memory, etc.

        :return: None
        """
        self._base_url = None
        self._base_domain = None
        self._root_domain = None
        self._encoding = None
        self._http_response = None