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

import thread
import time
import traceback
import sys
import unittest

from core.controllers.threads.threadpool import Pool, TimeoutError



def f(x):
    return x*x

def work(seconds):
    time.sleep(seconds)
    return (thread.get_ident(), seconds)


class TestThreadPool(unittest.TestCase):
    """
    Some tests that are based from the original recipe at
    http://code.activestate.com/recipes/576519-thread-pool-with-same-api-as-multiprocessingpool/
    """
    
    def setUp(self):
        self.callback_count = 0
        self.pool = Pool(9)
    
    def tearDown(self):
        self.pool.terminate()
    
    def test_basic(self):
        start = time.time()
        
        # evaluate "f(10)" asynchronously
        result = self.pool.apply_async(f, (10,))
        self.assertEqual( result.get(timeout=1) , 100 )   
    
        # prints "[0, 1, 4,..., 81]"
        self.assertEqual( self.pool.map(f, range(10)) , [f(x) for x in range(10)] )
    
        it = self.pool.imap(f, range(10))
        self.assertEqual( it.next() , 0 )
        self.assertEqual( it.next() , 1 )                 
        self.assertEqual( it.next(timeout=1) , 4 )


    def test_apply_sync_exceptions(self):

        result = self.pool.apply_async(time.sleep, (3,))
        try:
            # raises `TimeoutError`
            result.get(timeout=1)
        except TimeoutError:
            self.assertTrue( True, "Good. Got expected timeout exception." )
        else:
            self.assertTrue( False, "Expected exception !" )
        result.get()
    
    def test_imap(self):
        thread_ids = []
        start = time.time()
        
        for thread_id, wait_time in self.pool.imap(work, xrange(10, 3, -1),
                                                   chunksize=4):
            if thread_id not in thread_ids:
                thread_ids.append(thread_id)
        
        end = time.time()
        
        # Verify the chunksize parameter
        self.assertEquals( len(thread_ids) , 2)
        self.assertTrue( end-start > 34 )
        self.assertTrue( end-start < 34.3 )
    
    def test_imap_unordered(self):
        start = time.time()
        
        for res in self.pool.imap_unordered(work, xrange(10, 3, -1)):
            res
        
        end = time.time()
        
        self.assertTrue( end-start > 10 )
        self.assertTrue( end-start < 10.3 )
        
    def callback(self, s):
        self.callback_count += 1
    
    def test_map_async(self):
        result = self.pool.map_async(work, xrange(10), callback=self.callback)
        
        try:
            # raises `TimeoutError`
            result.get(timeout=1)
        except TimeoutError:
            self.assertTrue( True, "Good. Got expected timeout exception." )
        else:
            self.assertTrue( False, "Expected exception !" )
        result.get()
        
        self.assertEqual( self.callback_count, 1)
    
    def test_imap_async(self):
        result = self.pool.imap_async(work, xrange(3, 10), callback=self.callback)
        
        try:
            # raises `TimeoutError`
            result.get(timeout=1)
        except TimeoutError:
            self.assertTrue( True, "Good. Got expected timeout exception." )
        else:
            self.assertTrue( False, "Expected exception !" )
        
        wait_time = 2
        results = []
        for thread_id, t_wait_time in result.get():
            self.assertTrue( t_wait_time, wait_time + 1)
            wait_time += 1
            results.append((thread_id, t_wait_time))
        
        for thread_id, t_wait_time in result.get():
            self.assertTrue( (thread_id, t_wait_time) in results )
            
        self.assertEqual( self.callback_count, 1)
    
    def imap_unordered_async(self):
        result = self.pool.imap_unordered_async(work, xrange(10, 3, -1),
                                                callback=self.callback)
        try:
            # raises `TimeoutError`
            result.get(timeout=1)
        except TimeoutError:
            self.assertTrue( True, "Good. Got expected timeout exception." )
        else:
            self.assertTrue( False, "Expected exception !" )
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
        
        self.assertEqual( self.callback_count, 1)
    
    def test_exceptions_imap_unordered_async(self):
        result = self.pool.imap_unordered_async(work, xrange(2, -10, -1),
                                                callback=self.callback)
        time.sleep(3)
        try:
            [i for i in result.get()]
        except IOError:
            self.assertTrue( True, "Good. Got expected exception." )
            
            exc_type, exc_value, exc_traceback = sys.exc_info()
            last_call = traceback.extract_tb(exc_traceback)[-1]
            _,_,func,call = last_call
            
            self.assertEquals('work', func)
            self.assertEquals('time.sleep(seconds)', call)
    
    def test_exceptions_imap_async(self):
        result = self.pool.imap_async(work, xrange(2, -10, -1),
                                      callback=self.callback)
        time.sleep(3)
        try:
            [i for i in result.get()]
        except IOError:
            self.assertTrue( True, "Good. Got expected exception." )
            
            exc_type, exc_value, exc_traceback = sys.exc_info()
            last_call = traceback.extract_tb(exc_traceback)[-1]
            _,_,func,call = last_call
            
            self.assertEquals('work', func)
            self.assertEquals('time.sleep(seconds)', call)

