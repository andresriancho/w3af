'''
homeDir.py

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

import user
import os

def createHomeDir():
    '''
    Creates the w3af home directory, on linux: /home/user/.w3af/
    @return: True if success.
    '''
    # Create .w3af inside home directory
    homeLocation = getHomeDir()
    if not os.path.exists(homeLocation):
        try:
            os.makedirs(homeLocation)
        except:
            return False
    return True
    
def getHomeDir():
    '''
    @return: The location of the w3af directory inside the home directory of the current user.
    '''
    homeLocation = user.home + os.path.sep + '.w3af'
    return homeLocation
