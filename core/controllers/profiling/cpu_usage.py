'''
cpu_usage.py

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

DEBUG_CPU_USAGE = False
TOP_N_FUNCTIONS = 50

if DEBUG_CPU_USAGE:
    import core.controllers.outputManager as om
    
    try:
        import yappi
    except:
        DEBUG_CPU_USAGE = False
    else:
        DEBUG_CPU_USAGE = True
        import pprint
        yappi.start()
    
def dump_cpu_usage():
    '''
    This is a function that prints the memory usage of w3af in real time.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    if not DEBUG_CPU_USAGE:
        return
    else:
        
        # Where data is stored, entries look like:
        # ('/home/dz0/workspace/w3af/plugins/discovery/afd.py.getOptions:183', 
        #  1, 3.1150000000000002e-06, 2.4320000000000002e-06)
        entries = []
        
        # Load the data into entries
        yappi.enum_stats(entries.append)
        
        # Order it, put the function that takes more time in the first
        # position so we can understand why it is consuming so much time
        def sort_tsub(a, b):
            return cmp(a[2], b[2])
        
        entries.sort(sort_tsub)
        entries.reverse()
        
        # Print the information in an "easy to read" way
        pp = pprint.PrettyPrinter(indent=4)
        data = pp.pformat( entries[:TOP_N_FUNCTIONS] )
        om.out.debug( 'CPU usage information:\n' + data )
        
        # Filtered information example
        filter_string = 'sqli.py'
        filtered = [x for x in entries if filter_string in x[0]]
        data = pp.pformat( filtered )
        fmt = 'CPU usage for "%s":\n%s'
        om.out.debug( fmt % (filter_string, data) )
        
