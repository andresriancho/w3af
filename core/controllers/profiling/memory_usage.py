'''
memory_usage.py

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

DEBUGMEMORY = False

if DEBUGMEMORY:
    import core.controllers.outputManager as om
    import random
    import inspect
    import sys
    import gc
    
    try:
        import objgraph
    except ImportError:
        DEBUGMEMORY = False
    
def dump_memory_usage():
    '''
    This is a function that prints the memory usage of w3af in real time.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    if not DEBUGMEMORY:
        return
    else:
        print 'Object References:'
        print '=================='
        interesting = ['HTTPQSRequest', 'url_object', 'list', 'tuple', 'httpResponse']
        for interesting_klass in interesting:
            interesting_instances = objgraph.by_type(interesting_klass)
            
            l = len(interesting_instances)
            if l < 10:
                sample = random.sample(interesting_instances, l)
            else:
                sample = random.sample(interesting_instances, 10)
            
            for s in sample:
                fmt = 'memory-refs/%s-backref-graph-%s.png'
                fname = fmt % (interesting_klass, id(s))
                
                ignores = [id(interesting_instances), id(s), id(sample)]
                ignores.extend( [id(v) for v in locals().values()] )
                ignores.extend( [id(v) for v in globals().values()] )
                ignores.append( id(locals()) )
                ignores.append( id(globals()) )
                objgraph.show_backrefs(s, highlight=inspect.isclass,
                                       extra_ignore=ignores,filename=fname,
                                       extra_info=_extra_info)
        
        print
        
        print 'Most common:'
        print '============'
        objgraph.show_most_common_types()

        print 
                
        print 'Memory delta:'
        print '============='
        objgraph.show_growth(limit=25)
        
        
        
def _extra_info( obj_ignore ):
    '''
    Takes an object and returns some extra information about it depending on the
    object type.
    '''
    try:
        if isinstance(obj_ignore, dict):
            name = find_names(obj_ignore)
            data = ','.join( [str(x) for x in obj_ignore.keys()] )[:50]
            return '%s:{%s}' % (name, data)
        
        if isinstance(obj_ignore, tuple):
            name = find_names(obj_ignore)
            data = str(obj_ignore)[1:-1][:50]
            return '%s:(%s)' % (name, data)

        if isinstance(obj_ignore, list):
            name = find_names(obj_ignore)
            data = ','.join( [str(x) for x in obj_ignore] )[:50]
            return '%s:[%s]' % (name, data) 
        
        return str(obj_ignore)[:50]
    except:
        return None

def find_names(obj_ignore):
    frame = sys._getframe()
    for frame in iter(lambda: frame.f_back, None):
        frame.f_locals
    result = []
    for referrer in gc.get_referrers(obj_ignore):
        if isinstance(referrer, dict):
            for k, v in referrer.iteritems():
                if v is obj_ignore and k != 'obj_ignore':
                    result.append(k)
    return result