'''
factory.py

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

'''
This module defines a factory function that is used around the project.

@author: Andres Riancho ( andres.riancho@gmail.com )
'''
import sys
from core.controllers.w3afException import w3afException
import traceback

def factory(moduleName, *args):
    '''
    This function creates an instance of a class thats inside a module
    with the same name.
    
    Example :
    >> f00 = factory( 'plugins.discovery.googleSpider' )
    >> print f00
    <googleSpider.googleSpider instance at 0xb7a1f28c>
    
    @parameter moduleName: What do you want to instanciate ?
    @return: An instance.
    '''
    try:
        __import__(moduleName)
    except ImportError,  ie:
        raise w3afException('There was an error while importing '+ moduleName + ': "' + str(ie) + '".')
    except Exception, e:
        raise w3afException('Error while loading plugin "'+ moduleName + '". Exception: ' + str(e) )
    else:
        
        className = moduleName.split('.')[-1]
        
        try:
            aModule = sys.modules[moduleName]
            aClass = getattr(aModule , className)
        except:
            raise w3afException('The requested plugin ("'+ moduleName + '") doesn\'t have a correct format.')
        else:
            try:
                inst = aClass(*args)
            except Exception, e:
                msg = 'Failed to get an instance of "' + className
                msg += '". Original exception: "' + str(e) + '".'
                msg += 'Traceback for this error: ' + str( traceback.format_exc() )
                raise w3afException(msg)
            return inst
