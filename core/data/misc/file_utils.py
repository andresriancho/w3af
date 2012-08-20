'''
file_utils.py

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

import string

ALLOWED = string.digits + string.letters + '/.-_'

def replace_file_special_chars( filename_path ):
    '''This is a *very* incomplete function which I added to fix a bug:
    http://sourceforge.net/apps/trac/w3af/ticket/173308
    
    And after realizing that it was very hard to perform a replace
    that worked for all platforms and when the thing to sanitize was a
    path+filename and not only a filename.'''
    return filename_path.replace(':','_')
