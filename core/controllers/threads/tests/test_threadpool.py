'''
test_threadpool.py

Copyright 2006 Andres Riancho

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
import unittest
import thread
import time
import traceback
from core.controllers.threads.threadpool import Pool, TimeoutError



class TestThreadPool(unittest.TestCase):
    
    def test_all(self):
        """
        Some tests that are based from the original recipe at
        http://code.activestate.com/recipes/576519-thread-pool-with-same-api-as-multiprocessingpool/
        """
        def f(x):
            return x*x
        
        def work(seconds):
            print "[%d] Start to work for %fs..." % (thread.get_ident(), seconds)
            time.sleep(seconds)
            print "[%d] Work done (%fs)." % (thread.get_ident(), seconds)
            return "%d slept %fs" % (thread.get_ident(), seconds)
    
        ### Test copy/pasted from multiprocessing
        # start 9 worker threads
        pool = Pool(9)                
    
        # evaluate "f(10)" asynchronously
        result = pool.apply_async(f, (10,))
        assert result.get(timeout=1) == 100   
    
        # prints "[0, 1, 4,..., 81]"
        assert pool.map(f, range(10)) == [f(x) for x in range(10)]     
    
        it = pool.imap(f, range(10))
        # prints "0"
        assert it.next() == 0
        # prints "1"
        assert it.next() == 1    
        # prints "4" unless slow computer             
        assert it.next(timeout=1) == 4
    
        # Test apply_sync exceptions
        result = pool.apply_async(time.sleep, (3,))
        try:
            print result.get(timeout=1)           # raises `TimeoutError`
        except TimeoutError:
            assert True, "Good. Got expected timeout exception."
        else:
            assert False, "Expected exception !"
        print result.get()
    
        def cb(s):
            print "Result ready: %s" % s
    
        # Test imap()
        for res in pool.imap(work, xrange(10, 3, -1), chunksize=4):
            print "Item:", res
    
        # Test imap_unordered()
        for res in pool.imap_unordered(work, xrange(10, 3, -1)):
            print "Item:", res
    
        # Test map_async()
        result = pool.map_async(work, xrange(10), callback=cb)
        try:
            print result.get(timeout=1)           # raises `TimeoutError`
        except TimeoutError:
            assert True, "Good. Got expected timeout exception."
        else:
            assert False, "Expected exception !"
        print result.get()
    
        # Test imap_async()
        result = pool.imap_async(work, xrange(3, 10), callback=cb)
        try:
            print result.get(timeout=1)           # raises `TimeoutError`
        except TimeoutError:
            assert True, "Good. Got expected timeout exception."
        else:
            assert False, "Expected exception !"
        for i in result.get():
            print "Item:", i
        print "### Loop again:"
        for i in result.get():
            print "Item2:", i
    
        # Test imap_unordered_async()
        result = pool.imap_unordered_async(work, xrange(10, 3, -1), callback=cb)
        try:
            print result.get(timeout=1)           # raises `TimeoutError`
        except TimeoutError:
            print "Good. Got expected timeout exception."
        else:
            assert False, "Expected exception !"
        for i in result.get():
            print "Item1:", i
        for i in result.get():
            print "Item2:", i
        r = result.get()
        for i in r:
            print "Item3:", i
        for i in r:
            print "Item4:", i
        for i in r:
            print "Item5:", i
    
        #
        # The case for the exceptions
        #
    
        # Exceptions in imap_unordered_async()
        result = pool.imap_unordered_async(work, xrange(2, -10, -1), callback=cb)
        time.sleep(3)
        try:
            for i in result.get():
                print "Got item:", i
        except IOError:
            print "Good. Got expected exception:"
            traceback.print_exc()
    
        # Exceptions in imap_async()
        result = pool.imap_async(work, xrange(2, -10, -1), callback=cb)
        time.sleep(3)
        try:
            for i in result.get():
                print "Got item:", i
        except IOError:
            print "Good. Got expected exception:"
            traceback.print_exc()
    
        # Stop the test: need to stop the pool !!!
        pool.terminate()
        print "End of tests"
    
