"""
encoding.py

Copyright 2012 Andres Riancho

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
import codecs
import urllib
import chardet

# Custom error handling schemes registration
ESCAPED_CHAR = "slash_escape_char"
PERCENT_ENCODE = "percent_encode"
HTML_ENCODE = 'html_encode_char'


def _return_html_encoded(encodingexc):
    """
    :return: &#xff when input is \xff
    """
    st = encodingexc.start
    en = encodingexc.end
    hex_encoded = "".join(hex(ord(c))[2:] for c in encodingexc.object[st:en])

    return (unicode('&#x' + hex_encoded), en)


def _return_escaped_char(encodingexc):
    """
    :return: \\xff when input is \xff
    """
    st = encodingexc.start
    en = encodingexc.end

    slash_x_XX = repr(encodingexc.object[st:en])[1:-1]
    return (unicode(slash_x_XX), en)


def _percent_encode(encodingexc):
    if not isinstance(encodingexc, UnicodeEncodeError):
        raise encodingexc

    st = encodingexc.start
    en = encodingexc.end

    return (
        u'%s' % (urllib.quote(encodingexc.object[st:en].encode('utf8')),),
        en
    )

codecs.register_error(ESCAPED_CHAR, _return_escaped_char)
codecs.register_error(PERCENT_ENCODE, _percent_encode)
codecs.register_error(HTML_ENCODE, _return_html_encoded)


def smart_unicode(s, encoding='utf8', errors='strict', on_error_guess=True):
    """
    Return the unicode representation of 's'. Decodes bytestrings using
    the 'encoding' codec.
    """
    if isinstance(s, unicode):
        return s
    
    if isinstance(s, str):
        try:
            s = s.decode(encoding, errors)
        except UnicodeDecodeError:
            if not on_error_guess:
                raise
            guessed_encoding = chardet.detect(s)['encoding']
            try:
                s = s.decode(guessed_encoding, errors)
            except UnicodeDecodeError:
                s = s.decode(encoding, 'ignore')
    else:
        if hasattr(s, '__unicode__'):
            s = unicode(s)
        else:
            s = unicode(str(s), encoding, errors)
    return s


def smart_str(s, encoding='utf-8', errors='strict'):
    """
    Return a bytestring version of 's', encoded as specified in 'encoding'.
    """
    if isinstance(s, unicode):
        s = s.encode(encoding, errors)
    elif not isinstance(s, str):
        s = str(s)
    return s


def is_known_encoding(encoding):
    """
    :return: True if the encoding name is known.

    >>> is_known_encoding( 'foo' )
    False
    >>> is_known_encoding( 'utf-8' )
    True
    """
    try:
        ''.decode(encoding)
    except LookupError:
        return False
    else:
        return True
