'''
FileLock.py

Copyright 2011 Andres Riancho

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

import os
import time
import errno
 
class FileLockException(Exception):
    pass
 

class FileLock(object):
    """ A file locking mechanism that has context-manager support so 
        you can use it in a with statement. This should be relatively cross
        compatible as it doesn't rely on msvcrt or fcntl for the locking.
        
        Original recipe:
        http://www.evanfosmark.com/2009/01/cross-platform-file-locking-support-in-python/
    """
 
    def __init__(self, file_name, timeout=10, delay=.05):
        """ Prepare the file locker. Specify the file to lock and optionally
            the maximum timeout and the delay between each attempt to lock.
        """
        self.is_locked = False
        self.lockfile = os.path.join(os.getcwd(), "%s.lock" % file_name)
        self.file_name = file_name
        self.timeout = timeout
        self.delay = delay
 
 
    def acquire(self):
        """ Acquire the lock, if possible. If the lock is in use, it check again
            every `wait` seconds. It does this until it either gets the lock or
            exceeds `timeout` number of seconds, in which case it throws 
            an exception.
        """
        for _ in xrange( int(self.timeout / self.delay) ):
            try:
                self.fd = os.open(self.lockfile, os.O_CREAT|os.O_EXCL|os.O_RDWR)
                break;
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
                time.sleep(self.delay)
        else: 
            raise FileLockException("Timeout occurred.")
                
        self.is_locked = True
 
 
    def release(self):
        """ Get rid of the lock by deleting the lockfile. 
            When working in a `with` statement, this gets automatically 
            called at the end.
        """
        if self.is_locked:
            os.close(self.fd)
            os.unlink(self.lockfile)
            self.is_locked = False
 
 
    def __enter__(self):
        """ Activated when used in the with statement. 
            Should automatically acquire a lock to be used in the with block.
        """
        if not self.is_locked:
            self.acquire()
        return self
 
 
    def __exit__(self, type, value, traceback):
        """ Activated at the end of the with statement.
            It automatically releases the lock if it isn't locked.
        """
        if self.is_locked:
            self.release()
 
 
    def __del__(self):
        """ Make sure that the FileLock instance doesn't leave a lockfile
            lying around.
        """
        self.release()
        
class FileLockRead(FileLock):
    """ A file locking mechanism that has context-manager support so 
        you can use it in a with statement. This should be relatively cross
        compatible as it doesn't rely on msvcrt or fcntl for the locking.
        
        This lock allows multiple threads to access the file for reading.
        
        Original recipe:
        http://www.evanfosmark.com/2009/01/cross-platform-file-locking-support-in-python/
    """
    def __init__(self, file_name, timeout=10, delay=.05):
        FileLock.__init__( self, file_name, timeout, delay )
  
    def acquire(self):
        """ 
            Wait until the write finishes and then access the file. No lock
            file is created, since we want to have the possibility of reading
            the same file from multiple threads.
            
            If `timeout` number of seconds is exceeded it throws 
            an exception.
        """
        
        for _ in xrange( int(self.timeout / self.delay) ):
            if not os.path.exists(self.lockfile):
                break
            time.sleep(self.delay)
        else:
            raise FileLockException("Timeout occurred.")
                
        self.is_locked = True
 
 
    def release(self):
        """
        Do nothing, as we don't create a lock in acquire()
        """
        pass
 
