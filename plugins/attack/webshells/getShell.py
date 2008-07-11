'''
getShell.py

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

import core.controllers.outputManager as om
import core.data.kb.knowledgeBase as kb
import core.data.parsers.urlParser as urlParser
from core.controllers.w3afException import w3afException
import os,time
import os.path
import urllib

def getShell( extension, forceExtension=False ):
    '''
    This method returns a webshell content to be used in exploits, based on the extension, or based on the
    x-powered-by header.
    
    Plugins calling this function, should depend on "discovery.serverHeader" if they want to use the complete power if this function.
    '''
    knownFramework = []
    uncertainFramework = []
    cmdPath = 'plugins' + os.path.sep + 'attack' + os.path.sep + 'webshells' + os.path.sep
    
    if forceExtension:
        filename =  cmdPath + 'cmd.' + extension
        realExtension = extension
        knownFramework.append( (filename, realExtension) )
    else:
        poweredByHeaders = kb.kb.getData( 'serverHeader' , 'poweredByString' )
        filename = ''
        
        shellList = [ x for x in os.listdir( cmdPath ) if x.startswith('cmd') ]
        for shellFilename in shellList:
                
            filename = cmdPath + shellFilename
            realExtension = shellFilename.split('.')[1]
                
            # Using the powered By headers
            # More than one header can have been sent by the server
            for h in poweredByHeaders:
                if h.lower().count( realExtension ):
                    knownFramework.append( (filename, realExtension) )
            
            # extension here is the parameter passed by the user, that can be '' , this happends in davShell
            uncertainFramework.append( (filename, extension or realExtension) )
    
    res = []
    knownFramework.extend( uncertainFramework )
    for filename, realExtension in knownFramework:
        try:
            cmdFile = open( filename )
        except:
            raise w3afException('Failed to open filename: ' + filename )
        else:
            fileContent = cmdFile.read()
            cmdFile.close()
            res.append( (fileContent, realExtension) )
    
    return res
