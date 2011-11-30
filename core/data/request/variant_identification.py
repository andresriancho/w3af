'''
variant_identification.py

Copyright 2010 Andres Riancho

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
from core.data.request.httpQsRequest import HTTPQSRequest

def are_variants(uri, other_uri):
    '''
    This function analyzes if two URLs are variants. Two requests are
    variants if the[y|ir]:
        - have the same URL
        - have the same method
        - have the same parameters
        - values for each parameter have the same type (int/string)
    
    @parameter uri: The URI we want to analyze
    @parameter other_uri: The other URI we want to analyze
    @return: True if the URLs are variants.

    >>> from core.data.parsers.urlParser import url_object
    >>> a = url_object('http://www.w3af.com/foo.php')
    >>> b = url_object('http://www.w3af.com/foo.php')
    >>> are_variants(a, b)
    True

    >>> a = url_object('http://www.w3af.com/foo.php?id=1')
    >>> b = url_object('http://www.w3af.com/foo.php?foo=1')
    >>> are_variants(a, b)
    False

    >>> a = url_object('http://www.w3af.com/bar.php?id=1')
    >>> b = url_object('http://www.w3af.com/foo.php?foo=1')
    >>> are_variants(a, b)
    False

    >>> a = url_object('http://www.w3af.com/foo.php?id=1')
    >>> b = url_object('http://www.rapid7.com/foo.php?id=1')
    >>> are_variants(a, b)
    False

    >>> a = url_object('http://www.w3af.com/foo.php?id=1&foo=bar')
    >>> b = url_object('http://www.rapid7.com/foo.php?id=1')
    >>> are_variants(a, b)
    False

    >>> a = 'http://www.w3af.com/foo.php?id=1'
    >>> b = 'http://www.rapid7.com/foo.php?id=1'
    >>> are_variants(a, b)
    Traceback (most recent call last):
      ...
    ValueError: The "uri" parameter of a HTTPQSRequest must be of urlParser.url_object type.
    '''
    return HTTPQSRequest(uri).is_variant_of(HTTPQSRequest(other_uri))
