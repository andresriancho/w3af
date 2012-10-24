'''
sniff.py

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
import sys

from ldtp import getwindowlist, getobjectlist
# These are two related functions that I might need in the future:
# getobjectinfo, getobjectproperty

USAGE = '''python sniff.py <filter>

sniff.py prints all window names in the current X session.

The filter is a string that will be matched against the window names in order
to print the internal window object information.
''' 
OBJECTS = True

def sniff(_filter):
    for window in getwindowlist():
        print '+', window
        
        if OBJECTS and _filter in window: 
            for window_object in getobjectlist(window):
                print '    -', window_object
    
    return 0

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print USAGE
        sys.exit(1)
    
    _filter = sys.argv[1]
    res = sniff(_filter)
    sys.exit(res)
    