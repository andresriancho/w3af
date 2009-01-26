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

def htmldecode(text):
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

if __name__ == '__main__':
    print htmldecode('hola mundo')
    print htmldecode('hólá múndó')
    print htmldecode('hola mundo &#0443')
