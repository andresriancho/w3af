'''
utils.py

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

from core.controllers.w3afException import w3afException


def rand_alpha(length=0):
    '''
    Create a random string ONLY with letters
    
    @return: A random string only composed by letters.

    >>> x = rand_alpha( length=10 )
    >>> len(x) == 10
    True
    >>> x = rand_alpha( length=20 )
    >>> len(x) == 20
    True
    >>> x = rand_alpha( length=5 )
    >>> y = rand_alpha( length=5 )
    >>> z = rand_alpha( length=5 )
    >>> w = rand_alpha( length=5 )
    >>> x != y != z != w
    True
    '''
    return ''.join(choice(letters) for _ in xrange(length or randint(10, 30)))
    
def rand_alnum(length=0):
    '''
    Create a random string with random length
    
    @return: A random string of with length > 10 and length < 30.

    >>> x = rand_number( length=10 )
    >>> len(x) == 10
    True
    >>> x = rand_number( length=20 )
    >>> len(x) == 20
    True
    >>> x = rand_number( length=5 )
    >>> y = rand_number( length=5 )
    >>> z = rand_number( length=5 )
    >>> w = rand_number( length=5 )
    >>> x != y != z != w
    True
    '''
    jibber = ''.join([letters, digits])
    return ''.join(choice(jibber) for _ in xrange(length or randint(10, 30)))

def rand_number(length=0, exclude_numbers=[]):
    '''
    Create a random string ONLY with numbers
    
    @return: A random string only composed by numbers.

    >>> x = rand_number( length=1 )
    >>> int(x) in range(10)
    True
    >>> x = rand_number( length=2 )
    >>> int(x) in range(100)
    True
    >>> x = rand_number( length=3 )
    >>> int(x) in range(1000)
    True
    '''
    max_tries = 100
    while True:
                
        ru = ''.join(choice(digits) for _ in xrange(length or randint(10, 30)))
        if int(ru) not in exclude_numbers:
            return ru
        
        max_tries -= 1
        if max_tries == 0:
            raise ValueError('Failed return random number.')        
        
    return ru
    
def create_format_string(length):
    '''
    @return: A string with $length %s and a final %n
    '''
    result = '%n' * length
    return result
