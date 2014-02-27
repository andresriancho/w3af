"""
utils.py

Copyright 2006 Andres Riancho

This file is part of w3af, http://w3af.org/ .

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

"""
from string import letters, digits
from random import choice, randint


def rand_alpha(length=0):
    """
    Create a random string ONLY with letters

    :return: A random string only composed by letters.
    """
    return ''.join(choice(letters) for _ in xrange(length or randint(10, 30)))


def rand_alnum(length=0):
    """
    Create a random string with random length

    :return: A random string of with length > 10 and length < 30.
    """
    jibber = ''.join([letters, digits])
    return ''.join(choice(jibber) for _ in xrange(length or randint(10, 30)))


def rand_number(length=0, exclude_numbers=[]):
    """
    Create a random string ONLY with numbers

    :return: A random string only composed by numbers.
    """
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
    """
    :return: A string with $length %s and a final %n
    """
    result = '%n' * length
    return result
