"""
make_leet.py

Copyright 2009 Leonardo Jose Fishman

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
LEET_LETTERS = dict(zip("aAeEiIoO", "44331100"))
LEET_LETTERS_OPTIONALS = dict(zip("sStT", "5577"))


def basic_leet(string, LEETERS):
    outlist = []
    
    for letter in string:
        if letter in LEETERS:
            letter = LEETERS[letter]
        outlist.append(letter)

    leeted_basic = ''.join(outlist)

    return leeted_basic


def make_leet(original_string):
    leeted_pass = []

    if  basic_leet(original_string, LEET_LETTERS) != original_string:
        leeted_pass.append(basic_leet(original_string, LEET_LETTERS))

    if  basic_leet(original_string, LEET_LETTERS_OPTIONALS) != original_string:
        leeted_pass.append(basic_leet(original_string, LEET_LETTERS_OPTIONALS))

    if  basic_leet(basic_leet(original_string, LEET_LETTERS), LEET_LETTERS_OPTIONALS) != original_string:
        leeted_pass.append(basic_leet(basic_leet(
            original_string, LEET_LETTERS), LEET_LETTERS_OPTIONALS))

    leeted_pass = list(set(leeted_pass))

    return leeted_pass
