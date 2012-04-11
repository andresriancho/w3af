'''
temp_shelve.py

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

from __future__ import with_statement
import shelve
import threading
import os
import sys
from random import choice
import string
import cPickle

from core.controllers.misc.temp_dir import get_temp_dir


class temp_shelve(object):
    '''
    It's a shelve wrapper which has the following features:
        - Automagically creates the file in the /tmp directory
        - Is thread safe
        - Deletes the file when the temp_shelve object is deleted
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        '''
        Create the shelve, and the thread lock.
        
        @return: None
        '''
        # Init some attributes
        self._shelve = None
        self._filename = None
        
        # Create the lock
        self._shelve_lock = threading.RLock()
        
        fail_count = 0
        while True:
            # Get the temp filename to use
            tempdir = get_temp_dir()
            filename = ''.join([choice(string.letters) for _ in range(12)]) + '.w3af.temp_shelve'
            self._filename = os.path.join(tempdir, filename)
            
            # https://sourceforge.net/tracker/?func=detail&aid=2828136&group_id=170274&atid=853652
            if (sys.platform=='win32') or (sys.platform=='cygwin'):
                self._filename = self._filename.decode( "MBCS" ).encode("utf-8" )

            try:
                # Create the shelve
                self._shelve = shelve.open(self._filename, flag='c')
            except Exception,  e:
                self._filename = None
                
                fail_count += 1
                if fail_count == 5:
                    msg = 'Failed to create shelve file "%s". Original exception: "%s"'
                    raise Exception( msg % (self._filename, e))
            else:
                break
                
            # Now we perform a small trick... we remove the temp file directory entry
            #
            # According to the python documentation: On Windows, attempting to remove a file that
            # is in use causes an exception to be raised; on Unix, the directory entry is removed
            # but the storage allocated to the file is not made available until the original file
            # is no longer in use
            try:
                os.remove(self._filename)
            except Exception:
                pass
        
    def __repr__(self):
        return repr(self)
    
    def keys(self):
        return [cPickle.loads(k) for k in self._shelve.keys()]
    
    def __contains__(self, key):
        return cPickle.dumps(key) in self._shelve
    
    def __setitem__(self, key, value):
        with self._shelve_lock:
            self._shelve[ cPickle.dumps(key) ] = value
    
    def __getitem__(self, key):
        return self._shelve[ cPickle.dumps(key) ]
        
    def __len__(self):
        return len(self._shelve)
    
    def get(self, key, default=-456):
        if key in self:
            return self[key]
        
        if default is not -456:
            return default
        
        raise KeyError()  
