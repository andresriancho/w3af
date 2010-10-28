'''
LRU.py

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
from __future__ import with_statement

import threading

class Node(object):
    __slots__ = ['prev', 'next', 'me']
    def __init__(self, prev, me):
        self.prev = prev
        self.me = me
        self.next = None

class LRU:
    """
    Implementation of a length-limited O(1) LRU queue.
    Built for and used by PyPE:
    http://pype.sourceforge.net
    Copyright 2003 Josiah Carlson.
    
    These is a list of the modifications that I (Andres Riancho) introduced to the code:
        - Thread safety
    """
    def __init__(self, count, pairs=[]):
        self.lock = threading.RLock()
        self.count = max(count, 1)
        self.d = {}
        self.first = None
        self.last = None
        for key, value in pairs:
            self[key] = value
            
    def __contains__(self, obj):
        return obj in self.d
        
    def __getitem__(self, obj):
        with self.lock:
            item = self.d[obj].me
            self[item[0]] = item[1]
            return item[1]
        
    def __setitem__(self, obj, val):
        with self.lock:
            if obj in self.d:
                del self[obj]
            nobj = Node(self.last, (obj, val))
            if self.first is None:
                self.first = nobj
            if self.last:
                self.last.next = nobj
            self.last = nobj
            self.d[obj] = nobj
            if len(self.d) > self.count:
                if self.first == self.last:
                    self.first = None
                    self.last = None
                    return
                item = self.first
                item.next.prev = None
                self.first = item.next
                item.next = None
                del self.d[item.me[0]]
                del item
        
    def __delitem__(self, obj):
        with self.lock:
            nobj = self.d[obj]
            if nobj.prev:
                nobj.prev.next = nobj.next
            else:
                self.first = nobj.next
            if nobj.next:
                nobj.next.prev = nobj.prev
            else:
                self.last = nobj.prev
            del self.d[obj]
    
    '''
    @w3af note: I think that the following methods are never used in the framework.
    '''
    def __iter__(self):
        cur = self.first
        while cur is not None:
            cur2 = cur.next
            yield cur.me[1]
            cur = cur2
    
    def iteritems(self):
        cur = self.first
        while cur is not None:
            cur2 = cur.next
            yield cur.me
            cur = cur2
    
    def iterkeys(self):
        return iter(self.d)
    
    def itervalues(self):
        for i, j in self.iteritems():
            yield j
    
    def keys(self):
        return self.d.keys()
        
    def __len__(self):
        return len(self.d)
        
    def values(self):
        return [i.me[1] for i in self.d.values()]

def main(): 
    lruTest = LRU(4)
    lruTest['1'] = 1
    lruTest['2'] = 1
    lruTest['3'] = 1
    lruTest['4'] = 1
    print 'Original:'
    for i in lruTest.iteritems():
        print i
    
    lruTest['5'] = 1
    print 'Agrego 5, se va 1:'
    for i in lruTest.iteritems():
        print i
    
    print 'El dos paso a estar en el primer puesto para irse. Pero si le asigno algo a 2...'
    lruTest['2'] = 1
    for i in lruTest.iteritems():
        print i
    print 'Paso de nuevo al ultimo puesto para irse.'
    
if __name__ == "__main__":
    main()
