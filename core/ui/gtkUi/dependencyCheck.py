'''
dependencyCheck.py

Copyright 2008 Andres Riancho

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

import core.controllers.outputManager as om
import sys
import subprocess

def gtkui_dependency_check():
    '''
    This function verifies that the dependencies that are needed by the GTK user interface are met.
    '''
    om.out.debug('Checking GTK UI dependencies')
    
    try:
        import sqlite3
    except:
        print 'You have to install python sqlite3 library. On Debian based distributions: apt-get install python-pysqlite2'
        sys.exit( 1 )
        
    try:
        import pyparsing
    except:
        print 'You have to install pyparsing library. On Debian based distributions: apt-get install python-pyparsing'
        sys.exit( 1 )
        
    try:
        import pydot
    except:
        print 'You have to install pydot library. On Debian based distributions: apt-get install python-pydot'
        sys.exit( 1 )
    
    try:
        proc = subprocess.Popen('neato -V',shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        print 'You have to install graphviz. On Debian based distributions: apt-get install graphviz'
        sys.exit( 1 )
    else:
        if 'graphviz' not in proc.stderr.read().lower():
            print 'You have to install graphviz. On Debian based distributions: apt-get install graphviz'
            sys.exit( 1 )

    try:
        import pygtk
        pygtk.require('2.0')
        import gtk, gobject
        assert gtk.pygtk_version >= (2, 12) 
    except:
        print 'You have to install pygtk version >=2.12 to be able to run the GTK user interface.'
        print 'On Debian based distributions: apt-get install python-gtk2'
        sys.exit( 1 )

