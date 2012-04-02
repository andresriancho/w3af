# -*- encoding: utf-8 -*-
'''
esmre_multire.py

Copyright 2012 Andres Riancho

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

import esmre
import re

from core.data.constants.encodings import DEFAULT_ENCODING


class esmre_multire(object):
    '''
    This is a wrapper around esmre that provides the plugins (users) with an
    easy to use API to esmre.
    '''
    
    def __init__(self, re_list):
        '''
        
        @param re_list: A list with all the regular expressions that we want
        to match against one or more strings using the "query" function.
        
        This list might be [re_str_1, re_str_2 ... , re_str_N] or something like
        [ (re_str_1, obj1) , (re_str_2, obj2) ... , (re_str_N, objN)]. In the first
        case, if a match is found this class will return [ (match_obj, re_str_N), ]
        in the second case we'll return [ (match_obj, re_str_N, objN), ]
        
        '''
        self._index = esmre.Index()
        self._re_cache = {} 

        for item in re_list:
            
            if isinstance(item, tuple):
                regex = item[0]
                # TODO: What about re flags?
                self._re_cache[ regex ] = re.compile( regex )
                regex = regex.encode(DEFAULT_ENCODING)
                self._index.enter(regex, item)
            elif isinstance(item, basestring):
                self._re_cache[ item ] = re.compile( item )
                item = item.encode(DEFAULT_ENCODING)
                self._index.enter(item, (item,) )
            else:
                raise ValueError('Can NOT build esmre_multire with provided values.')
            
            
    def query(self, target_str):
        '''
        Apply the regular expressions to the target_str and return a list
        according to the class __init__ documentation. 
        
        @param target_str: The target string where the regular expressions are
        going to be applied. First we apply the esmre algorithm and then we do
        some magic of our own.

        >>> re_list = ['123','456','789']
        >>> mre = esmre_multire( re_list )
        >>> mre.query( '456' ) #doctest: +ELLIPSIS
        [[<_sre.SRE_Match object at 0x...>, '456', <_sre.SRE_Pattern object at 0x...>]]
        >>> mre.query( '789' ) #doctest: +ELLIPSIS
        [[<_sre.SRE_Match object at 0x...>, '789', <_sre.SRE_Pattern object at 0x...>]]
        
        >>> re_list = ['123.*456','abc.*def']
        >>> mre = esmre_multire( re_list )
        >>> mre.query( '456' ) #doctest: +ELLIPSIS
        []
        >>> mre.query( '123a456' ) #doctest: +ELLIPSIS
        [[<_sre.SRE_Match object at 0x...>, '123.*456', <_sre.SRE_Pattern object at 0x...>]]
        >>> mre.query( 'abcAAAdef' ) #doctest: +ELLIPSIS
        [[<_sre.SRE_Match object at 0x...>, 'abc.*def', <_sre.SRE_Pattern object at 0x...>]]

        >>> re_list = [ ('123.*456', None, None) , ('abc.*def', 1, 2) ]
        >>> mre = esmre_multire( re_list )
        >>> mre.query( '123A456' ) #doctest: +ELLIPSIS
        [[<_sre.SRE_Match object at 0x...>, '123.*456', <_sre.SRE_Pattern object at 0x...>, None, None]]
        >>> mre.query( 'abcAAAdef' ) #doctest: +ELLIPSIS
        [[<_sre.SRE_Match object at 0x...>, 'abc.*def', <_sre.SRE_Pattern object at 0x...>, 1, 2]]

        >>> re_list = [u'ñ', u'ý']
        >>> mre = esmre_multire( re_list )
        >>> mre.query( 'abcn' )
        []
        >>> mre.query( 'abcñ' ) #doctest: +ELLIPSIS
        [[<_sre.SRE_Match object at 0x...>, 'ñ', <_sre.SRE_Pattern object at 0x...>]]

        >>> re_list = [u'abc', u'def']
        >>> mre = esmre_multire( re_list )
        >>> mre.query( 'abcñ' ) #doctest: +ELLIPSIS
        [[<_sre.SRE_Match object at 0x...>, 'abc', <_sre.SRE_Pattern object at 0x...>]]
        >>> mre.query( 'abc\\x00def' ) #doctest: +ELLIPSIS
        [[<_sre.SRE_Match object at 0x...>, 'abc', <_sre.SRE_Pattern object at 0x...>], [<_sre.SRE_Match object at 0x...>, 'def', <_sre.SRE_Pattern object at 0x...>]]
        '''
        result = []
        
        if isinstance(target_str, unicode):
            target_str = target_str.encode(DEFAULT_ENCODING)
        
        query_result_list = self._index.query(target_str)
        
        for query_result in query_result_list:
            # query_result is a tuple with the regular expression that matched
            # as the first object and the associated objects following
            matched_regex = query_result[0]
            regex_comp = self._re_cache[ matched_regex ] 
            matchobj = regex_comp.search( target_str )
            if matchobj:
                resitem = [matchobj, matched_regex, regex_comp]
                resitem.extend( query_result[1:] )
                result.append( resitem )

        return result
