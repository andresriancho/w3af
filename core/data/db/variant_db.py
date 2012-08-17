'''
variant_db.py

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
import threading

from core.data.db.temp_shelve import temp_shelve as temp_shelve


class variant_db(object):
    def __init__(self, max_variants = 5):
        self._internal_dict = temp_shelve()
        self._db_lock = threading.RLock()
        self.max_variants = max_variants
        
    def append(self, reference):
        '''
        Called when a new reference is found and we proved that new
        variants are still needed.
        
        @param reference: The reference (as an url_object) to add. This method
        will "normalize" it before adding it to the internal dict.
        '''
        clean_reference = self._clean_reference( reference )
        
        with self._db_lock:
            count = self._internal_dict.get( clean_reference, None)
            
            if count is not None:
                self._internal_dict[ clean_reference ] = count + 1
            else:
                self._internal_dict[ clean_reference ] = 1
            
    def _clean_reference(self, reference):
        '''
        This method is VERY dependent on the are_variants method from
        core.data.request.variant_identification , make sure to remember that
        when changing stuff here or there.
        
        What this method does is to "normalize" any input reference string so
        that they can be compared very simply using string match.

        >>> from core.data.parsers.urlParser import url_object
        >>> from core.controllers.misc.temp_dir import create_temp_dir
        >>> _ = create_temp_dir()
        >>> URL = url_object
        
        >>> vdb = variant_db()
        
        >>> vdb._clean_reference(URL('http://w3af.org/'))
        u'http://w3af.org/'
        >>> vdb._clean_reference(URL('http://w3af.org/index.php'))
        u'http://w3af.org/index.php'
        >>> vdb._clean_reference(URL('http://w3af.org/index.php?id=2'))
        u'http://w3af.org/index.php?id=number'
        >>> vdb._clean_reference(URL('http://w3af.org/index.php?id=2&foo=bar'))
        u'http://w3af.org/index.php?id=number&foo=string'
        >>> vdb._clean_reference(URL('http://w3af.org/index.php?id=2&foo=bar&spam='))
        u'http://w3af.org/index.php?id=number&foo=string&spam=string'
         
        '''
        res = reference.getDomainPath() + reference.getFileName()
        
        if reference.hasQueryString():
            
            res += '?'
            qs = reference.querystring.copy()
            
            for key in qs:
                value_list = qs[key]
                for i, value in enumerate(value_list):
                    if value.isdigit():
                        qs[key][i] = 'number'
                    else:
                        qs[key][i] = 'string'
            
            res += str(qs)
            
        return res
    
    def need_more_variants(self, reference):
        '''
        @return: True if there are not enough variants associated with
        this reference in the DB.
        '''
        clean_reference = self._clean_reference( reference )
        # I believe this is atomic enough...
        count = self._internal_dict.get( clean_reference, 0 )
        if count >= self.max_variants:
            return False
        else:
            return True
