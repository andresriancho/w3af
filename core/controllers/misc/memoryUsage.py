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
    from core.data.parsers.urlParser import url_object
    from plugins.output.gtkOutput import message

    
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
        
        msg = ''
        
        if isinstance( byrcs, guppy.heapy.UniSet.IdentitySetMulti ):
            try:
                msg += 'Memory dump:\n'
                msg += '============\n'
                msg += str(byrcs) + '\n'
    
                for i in xrange(10):
                    msg += str(byrcs[i].byvia) + '\n'
                
            except:
                msg += 'Memory dump: Failed!'
            
            #om.out.debug( 'The one:' + repr(byrcs[0].byid[0].theone) )
        
        if DEBUGREFERENCES:
            classes_to_analyze = [url_object, message]
            
            for object_in_memory in gc.get_objects():
                ###
                ### Note: str objects CAN'T be analyzed this way. They can't create loops, so they arent
                ### handled by the gc ( __cycling__ garcage collector ) .
                ###
                for kls in classes_to_analyze:
                    if isinstance( object_in_memory, kls ):
                        tmp = 'Objects of class %s are referenced by:\n' % kls
                        tmp += str(hpy.iso(object_in_memory).sp) + '\n'
                        
                        #  Objects of class plugins.output.gtkOutput.message are referenced by:
                        #   0: hpy().Root.t140285309286144_exc_traceback.tb_frame.f_locals['object_in_memory']
                        if '1: ' in tmp:
                            msg += tmp

        om.out.debug( msg )

