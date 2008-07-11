'''
memoryUsage.py

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
DEBUGREFERENCES = False

if DEBUGMEMORY:
    import core.controllers.outputManager as om
    try:
        import guppy
    except ImportError:
        DEBUGMEMORY = False

if DEBUGREFERENCES:
    import gc
    import core.data.request.fuzzableRequest as fuzzableRequest
    
def dumpMemoryUsage():
    '''
    This is a function that prints the memory usage of w3af in real time.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    if not DEBUGMEMORY:
        pass
    else:
        hpy = guppy.hpy()
        h = hpy.heap()

        byrcs = h.byrcs
        
        if isinstance( byrcs, guppy.heapy.UniSet.IdentitySetMulti ):
            om.out.debug( str(byrcs) )
            for i in xrange(10):
                om.out.debug( str(byrcs[i].byvia) )
            #om.out.debug( 'The one:' + repr(byrcs[0].byid[0].theone) )
        
        if DEBUGREFERENCES:
            for objMemoryUsage in gc.get_objects():
                ###
                ### Note: str objects CAN'T be analyzed this way. They can't create loops, so they arent
                ### handled by the gc ( __cycling__ garcage collector ) .
                ###
                if isinstance( objMemoryUsage, fuzzableRequest.fuzzableRequest ):
                    om.out.debug('Objects of class fuzzableRequest are referenced by:' )
                    om.out.debug( str(hpy.iso(objMemoryUsage).sp) )
