'''
getResponseType.py

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

def isTextOrHtml( headers ):
    '''
    @return: Inspects if the type of the url passed as parameter and returns True
    if it is a Text of a html document.
    '''
    for key in headers.keys():
        if 'Content-Type'.lower() == key.lower():
            type = headers[ key ]
            if type.lower().count('txt') or type.lower().count('html'):
                return True
            else:
                return False
    
    return False

def isPDF( headers ):
    '''
    @return: Inspects if the type of the url passed as parameter and returns True
    if it is a PDF document.
    '''
    for key in headers.keys():
        if 'Content-Type'.lower() == key.lower():
            type = headers[ key ]
            if type.lower().count('pdf'):
                return True
            else:
                return False
    
    return False
