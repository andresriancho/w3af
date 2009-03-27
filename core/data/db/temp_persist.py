'''
temp_persist.py

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

from __future__ import with_statement
import shelve
import thread
import os
from random import choice
import string

try:
   import cPickle as pickle
except:
   import pickle

try:
    from core.controllers.misc.temp_dir import get_temp_dir
except:
    def get_temp_dir():
        return '/tmp/'


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
        self._shelve_lock = thread.allocate_lock()
        
        fail_count = 0
        while True:
            # Get the temp filename to use
            tempdir = get_temp_dir()
            filename = ''.join([choice(string.letters) for i in range(8)]) + '.w3af.temp_shelve'
            self._filename = os.path.join(tempdir, filename)
            
            try:
                # Create the shelve
                self._shelve = shelve.open(self._filename, flag='c')
            except:
                self._filename = None
                
                fail_count += 1
                if fail_count == 5:
                    raise Exception('Failed to create shelve file.')
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
        return self._shelve.keys()
    
    def __contains__(self, value):
        return value in self._shelve
    
    def __setitem__(self, key, value):
        # thread safe here!
        with self._shelve_lock:
            self._shelve[ key ] = value
    
    def __getitem__(self, key):
        return self._shelve[ key ]
        
    def __len__(self):
        return len(self._shelve)
        

class disk_list(object):
    '''
    This class represents a list that's going to be persisted in disk.
    '''
    def __init__(self):
        self._temp_shelve = temp_shelve()

    def append(self, value):
        self._temp_shelve[value] = 1
        return None
        
    def __repr__(self):
        return repr(self._temp_shelve.keys())
        
    def __contains__(self, value):
        return value in self._temp_shelve
        
    def __len__(self):
        return len(self._temp_shelve.keys())


if __name__ == '__main__':
    tshelve = temp_shelve()
    import time
    time.sleep(4)
    print 'Testing temp_shelve:'
    print '1- Loading...'
    for i in xrange(10000):
        tshelve[ str(i) ] = i
    assert len(tshelve) == 10000
    
    print '2- Retrieving...'
    for i in xrange(10000):
        assert i == tshelve[ str(i) ]
    
    print 'Done!', 
    print 'Please verify manually that the temp_shelve file inside the tempdir was removed.'
    
    print ''
    print 'Testing disk_list:'
    dlist = disk_list()
    
    print '1- Loading items...'
    for i in xrange(1000):
        dlist.append(str(i))
        '' in dlist
    
    print '2- Assert statements...'
    assert len(dlist) == 1000
    assert '5' in dlist
    assert not '5555' in dlist
    try:
        unicode('a') in dlist
    except:
        print 'Exception raised (ok).'
    print 'Done!'
