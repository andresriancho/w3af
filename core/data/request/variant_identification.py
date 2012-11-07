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
from itertools import chain, izip_longest


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

    '''
    if uri.getDomain() != other_uri.getDomain():
        return False
    
    if uri.getPath() != other_uri.getPath():
        return False
    
    if not uri.hasQueryString() and not other_uri.hasQueryString():
        # No QS and same Domain
        return True
    
    if uri.hasQueryString() and other_uri.hasQueryString():
        dc = uri.querystring
        odc = other_uri.querystring

        if dc.keys() != odc.keys():
            return False
        
        for vself, vother in izip_longest(
                                  chain(*dc.values()),
                                  chain(*odc.values()),
                                  fillvalue=None
                                  ):
            if None in (vself, vother) or \
                vself.isdigit() != vother.isdigit():
                return False
        
        return True
    
    return False    

