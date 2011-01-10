# -*- coding: utf-8 -*-

'''
encode_decode.py

Copyright 2008 Andres Riancho

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

import re
from htmlentitydefs import name2codepoint
import urllib
import sys


def htmldecode(text, use_repr=False):
    """
    Decode HTML entities in the given text.
    """
    # This pattern matches a character entity reference (a decimal numeric
    # references, a hexadecimal numeric reference, or a named reference).
    charrefpat = re.compile(r'&(#(\d+|x[\da-fA-F]+)|[\w.:-]+);?')
    
    # FIXME: What if we have something like this: &aacute ?!?!
    # I expected something like á , not a  '\xe1'
    '''
    >>> from encode_decode import *
    >>> htmldecode('&aacute;')
    '\xe1'
    '''
    #uchr = lambda value: value > 255 and unichr(value).encode('utf-8') or chr(value)
    uchr = lambda value: unichr(value).encode('utf-8')
    
    # Internal function to do the work
    def entitydecode(match, uchr=uchr):
        entity = match.group(1)
        if entity.startswith('#x'):
            return uchr(int(entity[2:], 16))
        elif entity.startswith('#'):
            return uchr(int(entity[1:]))
        elif entity in name2codepoint:
            return uchr(name2codepoint[entity])
        else:
            return match.group(0)
            
    # "main"
    return charrefpat.sub(entitydecode, text)


def urlencode(query, doseq=0, safe='/<>"\'=:()'):
    '''
    This is my version of urllib.urlencode , that adds "/" as a safe character and also adds support
    for "repeated parameter names".
    
    Note:
        This function is EXPERIMENTAL and should be used with care ;)
    
    Maybe this is the place to fix this bug:
        http://sourceforge.net/tracker2/?func=detail&aid=2675634&group_id=170274&atid=853652
        
    Original documentation:
        Encode a sequence of two-element tuples or dictionary into a URL query string.

        If any values in the query arg are sequences and doseq is true, each
        sequence element is converted to a separate parameter.

        If the query arg is a sequence of two-element tuples, the order of the
        parameters in the output will match the order of parameters in the
        input.
    '''

    if hasattr(query,"items"):
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
            ty,va,tb = sys.exc_info()
            raise TypeError, "not a valid non-string sequence or mapping object", tb

    l = []
    if not doseq:
        # preserve old behavior
        for k, v in query:
            
            # keys are easy
            k = urllib.quote_plus(str(k), safe)
            
            # Check for [] in the value
            if isinstance(v, list):
                for v_item in v:
                    v_item = urllib.quote_plus(str(v_item), safe)
                    l.append(k + '=' + v_item)
            else:
                v = urllib.quote_plus(str(v), safe)
                l.append(k + '=' + v)
    else:
        for k, v in query:
            # keys are easy...
            k = urllib.quote_plus(str(k), safe)
            
            # now the value...
            # is string
            if isinstance(v, str):
                v = urllib.quote_plus(v, safe)
                l.append(k + '=' + v)
    
            # is unicode...
            elif urllib._is_unicode(v):
                # is there a reasonable way to convert to ASCII?
                # encode generates a string, but "replace" or "ignore"
                # lose information and "strict" can raise UnicodeError
                v = urllib.quote_plus(v.encode("ASCII","replace"), safe)
                l.append(k + '=' + v)
                
            else:
                try:
                    # is this a sufficient test for sequence-ness?
                    x = len(v)
                except TypeError:
                    # not a sequence
                    v = urllib.quote_plus(str(v), safe)
                    l.append(k + '=' + v)
                else:
                    # loop over the sequence
                    for elt in v:
                        l.append(k + '=' + urllib.quote_plus(str(elt), safe))
                        
    return '&'.join(l)


if __name__ == '__main__':
    
    # htmldecode test
    print htmldecode('hola mundo')
    print htmldecode('hólá múndó')
    print htmldecode('hola mundo &#0443')
    
    # urlencode test
    import cgi
    print urlencode( cgi.parse_qs('a=1&a=c') )
