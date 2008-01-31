'''
install.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hoinstall that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''


import os
from core.controllers.w3afException import *
import core.controllers.outputManager as om
import shutil

def installVdaemon( msfDir ):
    '''
    Copy the virtual daemon module to the metasploit framework directory
    
    @parameter msfDir: The dir where the function will copy the module.
    '''
    filename = 'w3af_vdaemon.rb'
    dst = os.path.join( msfDir, 'modules' + os.path.sep + 'exploits' + os.path.sep + 'unix' + os.path.sep +'misc' + os.path.sep + filename )
    src = 'core' + os.path.sep + 'controllers' + os.path.sep + 'vdaemon' + os.path.sep + filename
    
    try:
        shutil.copyfile( src, dst )
    except Exception, e:
        om.out.error('Failed to install the virtual daemon module in the metasploit directory: "' + dst + '". Exception: "' + str(e) + '".' )
    else:
        om.out.console('Successfully installed Virtual Daemon.')
