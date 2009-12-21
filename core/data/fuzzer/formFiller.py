# -*- coding: utf8 -*-
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

def smartFill( variable_name ):
    '''
    This method returns a "smart" option for a variable name inside a form. For example, if the
    variable_name is "username" a smartFill response would be "john1309", not "0800-111-2233".
    This helps A LOT with server side validation.
    
    @return: The "most likely to be validated as a good value" string, OR a random str if no match is found.
    '''
    variable_name = variable_name.lower()
    
    handlers = [ (long_alpha, (createRandAlpha, 7)), 
                        (short_alpha, (createRandAlpha, 3)), 
                        (long_number, (createRandNum, 5)), 
                        (short_number, (createRandNum, 2)), 
                        (date, (createRandNum, 1)), 
                        (password, (lambda x: 'w3af-FrAmEW0rK.', None)), 
                        (mail, (lambda x: 'w3af@email.com', None)), 
                        (state, (lambda x: 'AK', None)) ]
    
    for name_function, (custom_generator, length) in handlers:
    
        for name_in_db in name_function():
            if variable_name.count( name_in_db ) or name_in_db.count( variable_name ):
                value = custom_generator( length )
                dbg = 'SmartFilling parameter ' + variable_name + ' of form with '
                dbg += repr(name_function) +' value: ' + value
                om.out.debug( dbg )
                return value
    
    # Well... nothing was found (this is bad!)
    # Its better to send numbers when nothing matches.
    return createRandNum( 4 )

def long_alpha():
    '''
    @return: A list of variables that should be filled with alpha strings.
    '''
    l = []
    
    # english
    l.append('username')
    l.append('user')
    l.append('name')    
    l.append('surname')
    l.append('lastname')
    l.append('location')
    l.append('city')
    l.append('country')    
    l.append('addr')
    l.append('address')
    l.append('residence')
    l.append('company')
    l.append('position')
    l.append('job')
    
    # spanish
    l.append('usuario')    
    l.append('nombre')
    l.append('apellido')
    l.append('ciudad')
    l.append('pais')
    l.append('país')
    l.append('dirección')
    l.append('direccion')
    l.append('residencia')
    l.append('empresa')
    l.append('cargo')
    
    # portugués
    l.append('nome')
    l.append('sobrenome')
    l.append('cidade')
    l.append('endereço')
    l.append('endereco')
    l.append('companhia')
    l.append('posição')
    l.append('residência')
    
    # German
    l.append('benutzername')
    l.append('benutzer')
    l.append('name')
    l.append('vorname')
    l.append('nachname')
    l.append('ort')
    l.append('stadt')
    l.append('land')
    l.append('addresse')
    l.append('wohnort')
    l.append('wohnsitz')
    l.append('unternehmen')
    l.append('unternehmung')
    l.append('position')
    
    # passwords need to be long in order to be "complex"
    l.append('pass')
    l.append('word')
    l.append('pswd')
    l.append('pwd')
    l.append('auth')
    l.append('password')
    l.append('contraseña')
    l.append('senha')
    
    return list(set(l))

def short_alpha():
    '''
    @return: A list of variables that should be filled with alpha strings.
    '''
    l = []
    return l

def short_number():
    l = []
    
    # english
    l.append('postal')
    l.append('zip')
    l.append('pin')
    l.append('id')
    l.append('floor')
    l.append('age')
    
    # spanish
    l.append('piso')
    l.append('edad')
    
    # german
    l.append('postleitzahl')
    l.append('plz')
    l.append('id')
    l.append('stock')
    l.append('alter')
    
    # portugués
    l.append('postais')
    
    return list(set(l))

def long_number():
    '''
    @return: A list of variables that should be filled with numeric strings.
    '''
    l = []
    
    # english
    l.append('phone')
    l.append('code')
    l.append('number')
    
    # spanish
    l.append('telefono')
    l.append('numero')
    l.append('número')
    l.append('código')
    l.append('codigo')
    
    # German
    l.append('telefon')
    l.append('tel')
    l.append('code')
    l.append('nummer')

    # portugués
    # equal to the spanish ones

    return list(set(l))

def mail():
    '''
    @return: A list of variables that should be filled with emails.
    '''
    l = []
    # english
    l.append('mail')
    l.append('email')
    l.append('e-mail') 
    
    #german
    # equal to the english ones
    
    # spanish
    l.append('correo')
    
    # portugués
    l.append('correio')
    return l

def state():
    '''
    @return: A list of form parameter names that may indicate that we have to input a state
    '''
    l = []
    # english
    l.append('state')
    
    # spanish and portugués
    l.append('estado')
    return l
    
    
def password():

    '''
    @return: A list of variables that should be filled with a password.
    '''
    
    l = []
    
    # password will be a constant
    l.append('pass')
    l.append('word')
    l.append('pswd')
    l.append('pwd')
    l.append('auth')
    l.append('password')
    
    # German
    l.append('passwort')
    
    # Spanish
    l.append('contraseña')
    
    # Portuguese
    l.append('senha')
    
    return l
    
def date():
    '''
    @return: A list of variables that should be filled with alpha strings.
    '''
    l = []
    # english
    l.append('year')
    l.append('month')
    l.append('day')
    l.append('birthday')
    l.append('birthyear')
    l.append('birthmonth')
    
    # spanish
    l.append('año')
    l.append('ano')
    l.append('mes')
    l.append('dia')
    l.append('día')
    
    # german
    l.append('jahr')
    l.append('monat')
    l.append('tag')
    l.append('geburts')
        
    # portugués
    l.append('mês')
    
    return l
    
from core.data.fuzzer.fuzzer import *

