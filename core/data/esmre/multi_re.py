'''
multire.py

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

try:
    import esmre
except ImportError:
    USE_ESMRE = False
else:
    USE_ESMRE = True
    
import re


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
                self._index.enter(regex, item)
            elif isinstance(item, basestring):
                self._re_cache[ item ] = re.compile( item )
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
        '''
        result = []
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

class re_multire(object):
    '''
    This is a wrapper around the re object that provides the plugins (users)
    with an easy to use API. This is a transition class that will be used by
    w3af users which don't have the esmre package installed.
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
        self._re_cache = {}
        self._assoc_obj = {}

        for item in re_list:
            
            if isinstance(item, tuple):
                regex = item[0]
                # TODO: What about re flags?
                self._re_cache[ regex ] = re.compile( regex )
                self._assoc_obj[ regex ] = item[1:]
            elif isinstance(item, basestring):
                self._re_cache[ item ] = re.compile( item )
            else:
                raise ValueError('Can NOT build re_multire with provided values.')
            
            
    def query(self, target_str):
        '''
        Apply the regular expressions to the target_str and return a list
        according to the class __init__ documentation. 
        
        @param target_str: The target string where the regular expressions are
        going to be applied. First we apply the esmre algorithm and then we do
        some magic of our own.

        >>> re_list = ['123','456','789']
        >>> mre = re_multire( re_list )
        >>> mre.query( '456' ) #doctest: +ELLIPSIS
        [[<_sre.SRE_Match object at 0x...>, '456', <_sre.SRE_Pattern object at 0x...>]]
        >>> mre.query( '789' ) #doctest: +ELLIPSIS
        [[<_sre.SRE_Match object at 0x...>, '789', <_sre.SRE_Pattern object at 0x...>]]
        
        >>> re_list = ['123.*456','abc.*def']
        >>> mre = re_multire( re_list )
        >>> mre.query( '456' ) #doctest: +ELLIPSIS
        []
        >>> mre.query( '123a456' ) #doctest: +ELLIPSIS
        [[<_sre.SRE_Match object at 0x...>, '123.*456', <_sre.SRE_Pattern object at 0x...>]]
        >>> mre.query( 'abcAAAdef' ) #doctest: +ELLIPSIS
        [[<_sre.SRE_Match object at 0x...>, 'abc.*def', <_sre.SRE_Pattern object at 0x...>]]

        >>> re_list = [ ('123.*456', None, None) , ('abc.*def', 1, 2) ]
        >>> mre = re_multire( re_list )
        >>> mre.query( '123A456' ) #doctest: +ELLIPSIS
        [[<_sre.SRE_Match object at 0x...>, '123.*456', <_sre.SRE_Pattern object at 0x...>, None, None]]
        >>> mre.query( 'abcAAAdef' ) #doctest: +ELLIPSIS
        [[<_sre.SRE_Match object at 0x...>, 'abc.*def', <_sre.SRE_Pattern object at 0x...>, 1, 2]]
        '''
        result = []
        
        for regex_str, compiled_regex in self._re_cache.iteritems():
             
            matchobj = compiled_regex.search( target_str )
            if matchobj:
                resitem = [matchobj, regex_str, compiled_regex]
                
                if regex_str in self._assoc_obj:
                    resitem.extend( self._assoc_obj[ regex_str ] )
                    
                result.append( resitem )

        return result


if USE_ESMRE:
    multire = esmre_multire
else:
    multire = re_multire
