'''
formFiller.py

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

from string import letters, digits
from random import choice, randint
import core.controllers.outputManager as om

def smartFill( variableName ):
    '''
    This method returns a "smart" option for a variable name inside a form. For example, if the
    variableName is "username" a smartFill response would be "john1309", not "0800-111-2233".
    This helps A LOT with server side validation.
    
    @return: The "most likely to be validated as a good value" string, OR a random str if no match is found.
    '''
    for alphaVarName in _getAlphaVarNames(): 
        if variableName.count( alphaVarName ) or alphaVarName.count( variableName ):
            value = createRandAlpha( 7 )
            om.out.debug('SmartFilling parameter ' + variableName + ' of form with alpha value: ' + value)
            return value
    
    for numericVarName in _getNumericVarNames(): 
        if variableName.count( numericVarName ) or numericVarName.count( variableName ):
            value = createRandNum( 7 )
            om.out.debug('SmartFilling parameter ' + variableName + ' of form with numeric value: ' + value)
            return value
    
    # Well... nothing was found, i'm soooo sad.
    # Its better to send numbers when nothing matches.
    return createRandNum( 6 )

def _getAlphaVarNames():
    '''
    @return: A list of variables that should be filled with alpha strings.
    '''
    l = []
    l.append('username')
    l.append('user')
    l.append('usuario')
    l.append('nombre')
    l.append('apellido')
    l.append('location')
    l.append('city')
    l.append('ciudad')
    l.append('name')
    return l

def _getNumericVarNames():
    '''
    @return: A list of variables that should be filled with numeric strings.
    '''
    l = []
    l.append('phone')
    l.append('telefono')
    l.append('numero')
    l.append('postal')
    l.append('code')
    l.append('number')
    l.append('pin')
    l.append('piso')
    l.append('floor')
    l.append('id')
    return l
    
from core.data.fuzzer.fuzzer import *
