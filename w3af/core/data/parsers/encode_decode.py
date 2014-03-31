# -*- coding: utf-8 -*-

"""
encode_decode.py

Copyright 2008 Andres Riancho

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
import re
import urllib
import sys

from htmlentitydefs import name2codepoint

from w3af.core.data.misc.encoding import HTML_ENCODE
from w3af.core.data.constants.encodings import DEFAULT_ENCODING

# This pattern matches a character entity reference (a decimal numeric
# references, a hexadecimal numeric reference, or a named reference).
CHAR_REF_PATT = re.compile(r'&(#(\d+|x[\da-fA-F]+)|[\w.:-]+);?', re.U)


def htmldecode(text, use_repr=False):
    """
    :return: Decode HTML entities in the given text and return it as unicode.
    """

    # Internal function to do the work
    def entitydecode(match):
        entity = match.group(1)

        # In some cases the entity is invalid and it triggers an exception
        # in unichr, that's why I need to have a try/except
        try:
            if entity.startswith('#x'):
                return unichr(int(entity[2:], 16))

            elif entity.startswith('#'):
                return unichr(int(entity[1:]))

            elif entity in name2codepoint:
                return unichr(name2codepoint[entity])
            else:
                return match.group(0)
        except:
            return match.group(0)

    # TODO: Requires more analysis
    #
    # re.sub decodes the text before applying the regular expression
    # and if we don't decode it ourselves, the default settings are
    # used, which can (in strange cases), trigger a UnicodeDecodeError
    #
    # In some cases, the text has special characters, which we want to
    # encode in &#xYY format. We encode it like this because it is the
    # "best thing we can do" with the available time we have
    #
    # It seems that I still need to learn more about the encoding/decoding
    # stuff, since adding this isinstance fixes a bug that I can't reproduce
    # with the test_encode_decode, even with the same input string :S
    #
    # My understanding of this isinstance is that we're basically preventing
    # a "double decode" which can trigger UnicodeDecodeError
    if not isinstance(text, unicode):
        text = text.decode(DEFAULT_ENCODING, errors=HTML_ENCODE)

    # "main"
    return CHAR_REF_PATT.sub(entitydecode, text)


def urlencode(query, encoding, safe='/<>"\'=:()'):
    """
    This is my version of urllib.urlencode. It adds "/" as a safe character
    and also adds support for "repeated parameter names".

    Note:
        This function is EXPERIMENTAL and should be used with care ;)

    Original documentation:
        Encode a sequence of two-element tuples or dictionary into a URL query
        string.

        If any values in the query arg are sequences and doseq is true, each
        sequence element is converted to a separate parameter.

        If the query arg is a sequence of two-element tuples, the order of the
        parameters in the output will match the order of parameters in the
        input.
    """

    if hasattr(query, "items"):
        # mapping objects
        query = query.items()
    else:
        # it's a bother at times that strings and string-like objects are
        # sequences...
        try:
            # non-sequence items should not work with len()
            # non-empty strings will fail this
            if len(query) and not isinstance(query[0], tuple):
                raise TypeError
            # zero-length sequences of all types will get here and succeed,
            # but that's a minor nit - since the original implementation
            # allowed empty dicts that type of behavior probably should be
            # preserved for consistency
        except TypeError:
            try:
                tb = sys.exc_info()[2]
                raise TypeError, "not a valid non-string sequence or " \
                    "mapping object", tb
            finally:
                del tb

    l = []
    is_unicode = lambda x: isinstance(x, unicode)

    for k, v in query:
        # first work with keys
        k = k.encode(encoding) if is_unicode(k) else str(k)
        k = urllib.quote(k, safe)

        if isinstance(v, basestring):
            v = [v]
        else:
            try:
                # is this a sufficient test for sequence-ness?
                len(v)
            except TypeError:
                v = [(v if v is None else str(v))]
        for ele in v:
            if not ele:
                toapp = k + '='
            else:
                if is_unicode(ele):
                    ele = ele.encode(encoding)
                else:
                    ele = str(ele)
                    
                toapp = k + '=' + urllib.quote(ele, safe)
                
            l.append(toapp)

    return '&'.join(l)
