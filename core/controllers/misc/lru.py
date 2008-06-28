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

'''
Important note: Original version found in pype.sourceforge.net and the python cookbook.
Not coded by me.
'''
import thread

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
    """
    def __init__(self, count, pairs=[]):
        self.count = max(count, 1)
        self.d = {}
        self.first = None
        self.last = None
        for key, value in pairs:
            self[key] = value
        self.createLock()
    
    def destroyLock( self ):
        self._lruLock = None
    
    def createLock( self ):
        self._lruLock = thread.allocate_lock()
        
    def getLock(self):
        try:
            self._lruLock.acquire()
        except:
            return False
        else:
            return True
    
    def releaseLock(self):
        try:
            self._lruLock.release()
        except:
            return False
        else:
            return True            
            
    def __contains__(self, obj):
        return obj in self.d
        
    def __getitem__(self, obj):
        a = self.d[obj].me
        self[a[0]] = a[1]
        return a[1]
        
    def __setitem__(self, obj, val):
        self.getLock()
        
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
                # releasing lock
                self.releaseLock()
                return
            a = self.first
            a.next.prev = None
            self.first = a.next
            a.next = None
            del self.d[a.me[0]]
            del a
        
        # releasing lock
        self.releaseLock()
        
    def __delitem__(self, obj):
        self.getLock()
        
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
        
        # releasing lock
        self.releaseLock()        
        
    def __iter__(self):
        cur = self.first
        while cur != None:
            cur2 = cur.next
            yield cur.me[1]
            cur = cur2
    
    def iteritems(self):
        cur = self.first
        while cur != None:
            cur2 = cur.next
            yield cur.me
            cur = cur2
    
    def iterkeys(self):
        return iter(self.d)
    
    def itervalues(self):
        for i,j in self.iteritems():
            yield j
    
    def keys(self):
        return self.d.keys()

def main(): 
    a = LRU(4)
    a['1']=1
    a['2']=1
    a['3']=1
    a['4']=1
    print 'Original:'
    for i in a.iteritems():
        print i
    
    a['5']=1
    print 'Agrego 5, se va 1:'
    for i in a.iteritems():
        print i
    
    print 'El dos paso a estar en el primer puesto para irse. Pero si le asigno algo a 2...'
    a['2']=1
    for i in a.iteritems():
        print i
    print 'Paso de nuevo al ultimo puesto para irse.'
    
if __name__ == "__main__":
    main()
