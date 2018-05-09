"""
web_encodings.py

Copyright 2018 Andres Riancho

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
import string
import functools

from w3af.core.data.misc.constants.web_encodings import (HEX_MAP,
                                                         HEX_FORMAT,
                                                         DEC_FORMAT,
                                                         DEC_PADDED_FORMAT,
                                                         URL_HEX_FORMAT,
                                                         SPECIAL_CHARS,
                                                         HTML_ENCODE_NAMES)


HTML_ENCODING_FUNCTIONS = []
URL_ENCODING_FUNCTIONS = []


def url_encode(data,
               by_code_replacer=None,
               replace_by_code=None,
               should_upper=False):
    """
    This is a generic function which can be used to generate all the functions
    we need for URL encoding.

    :param data: The data to encode
    :param by_code_replacer: The function to use to replace by code: &#xXX;
    :param replace_by_code: The character list that determines if a char should be replaced by a code
    :param should_upper: Should we upper-case the replacement? Use: &amp; or &AMP;?
    :return: The URL encoded string
    """
    result = []

    for char in data:
        if char in replace_by_code:
            replaced_char = by_code_replacer(char)
            if should_upper and replaced_char != char:
                char = replaced_char.upper()
            else:
                char = replaced_char

        result.append(char)

    return u''.join(result)


def generate_url_encoding_functions():
    by_code_replacers = (
        lambda c: c,
        lambda c: URL_HEX_FORMAT % HEX_MAP.get(c, c),
        lambda c: URL_HEX_FORMAT % HEX_MAP.get(c, c) if c != u' ' else u'+'
    )

    replace_by_codes = (
        # No character is replaced
        {},

        # RFC 2396 Uniform Resource Identifiers reserved
        {u';', u'/', u'?', u':', u'@', u'&', u'=', u'+', u'$', u','},

        # RFC 2396 Uniform Resource Identifiers reserved without the slash
        {u';', u'?', u':', u'@', u'&', u'=', u'+', u'$', u','},

        # All not in printable
        {unichr(c) for c in xrange(256) if unichr(c) not in string.printable},

        # All not in digits, letters and dot
        {unichr(c) for c in xrange(256) if unichr(c) not in string.digits + string.letters + u'.'},

        # All characters are replaced
        HEX_MAP,
    )

    # Add true here if you want the upper case and lower case versions of
    # the encoded character. With the current version of the code we don't
    # need to use True here because we do a case insensitive replace at
    # remove_using_lower_case
    should_uppers = {False}

    for by_code_replacer in by_code_replacers:
        for replace_by_code in replace_by_codes:
            for should_upper in should_uppers:
                functor = functools.partial(url_encode,
                                            by_code_replacer=by_code_replacer,
                                            replace_by_code=replace_by_code,
                                            should_upper=should_upper)

                URL_ENCODING_FUNCTIONS.append(functor)


def html_encode(data,
                by_code_replacer=None,
                by_name_replacer=None,
                replace_by_code=None,
                replace_by_name=None,
                should_upper=False):
    """
    This is a generic function which can be used to generate all the functions
    we need for HTML encoding.

    :param data: The data to encode
    :param by_code_replacer: The function to use to replace by code: &#xXX;
    :param by_name_replacer: The function to use to replace by name: &amp;
    :param replace_by_code: The character list that determines if a char should be replaced by a code
    :param replace_by_name: The character list that determines if a char should be replaced by a name
    :param should_upper: Should we upper-case the replacement? Use: &amp; or &AMP;?
    :return: The HTML encoded string
    """
    result = []

    for char in data:
        if char in replace_by_name:
            replaced_char = by_name_replacer(char)
            if should_upper and replaced_char != char:
                char = replaced_char.upper()
            else:
                char = replaced_char

        elif char in replace_by_code:
            replaced_char = by_code_replacer(char)
            if should_upper and replaced_char != char:
                char = replaced_char.upper()
            else:
                char = replaced_char

        result.append(char)

    return u''.join(result)


def generate_html_encoding_functions():
    by_code_replacers = (
        lambda c: c,
        lambda c: HEX_FORMAT % HEX_MAP.get(c, c),
        lambda c: DEC_FORMAT % ord(c),
        lambda c: DEC_PADDED_FORMAT % ord(c)
    )

    by_name_replacers = (
        lambda c: c,
        lambda c: HTML_ENCODE_NAMES.get(c, c),
    )

    replace_by_codes = (
        {},
        SPECIAL_CHARS,
        {u'&', u'<', u'>'},
        {u'&', u'<', u'>', u'"'},
        HEX_MAP,
    )

    replace_by_names = (
        {},
        SPECIAL_CHARS,
        HTML_ENCODE_NAMES,
        {u'&', u'<', u'>'},
        {u'&', u'<', u'>', u'"'},
        HEX_MAP,
    )

    # Add true here if you want the upper case and lower case versions of
    # the encoded character. With the current version of the code we don't
    # need to use True here because we do a case insensitive replace at
    # remove_using_lower_case
    should_uppers = {False}

    for by_code_replacer in by_code_replacers:
        for by_name_replacer in by_name_replacers:
            for replace_by_code in replace_by_codes:
                for replace_by_name in replace_by_names:
                    for should_upper in should_uppers:
                        functor = functools.partial(html_encode,
                                                    by_code_replacer=by_code_replacer,
                                                    by_name_replacer=by_name_replacer,
                                                    replace_by_code=replace_by_code,
                                                    replace_by_name=replace_by_name,
                                                    should_upper=should_upper)

                        HTML_ENCODING_FUNCTIONS.append(functor)


def unicode_escape(data):
    """
    This encoding is used in JSON:
        Double quotes become: \u0022
        Single quotes become: \u0027
    """
    return data.replace(u'"', u'\\u0022').replace(u"'", u'\\u0027')


def backslash_escape(data):
    """
    This encoding is used in JSON:
        Double quotes become: \"
        Single quotes become: \'
    """
    return data.replace(u'"', u'\\"').replace(u"'", u"\\'")


JSON_ENCODING_FUNCTIONS = (
    unicode_escape,
    backslash_escape
)
