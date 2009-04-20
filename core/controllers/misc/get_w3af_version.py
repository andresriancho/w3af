'''
get_w3af_version.py

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

import os
import re


def get_w3af_version():
    '''
    @return: A string with the w3af version.
    '''
    # Let's check if the user is using a version from SVN
    revision = -1
    
    if os.path.exists( os.path.join('.svn', 'entries') ):
        try:
            for line in file('.svn' + os.path.sep +'entries').readlines()[:4]:
                line = line.strip()
                if re.match('^\d+$', line ):
                    if int(line) > int(revision):
                        revision = int(line)
        except (IOError, ValueError):
            revision = 'unknown'

    res = 'w3af - Web Application Attack and Audit Framework'
    res += '\nVersion: 1.1'
    if revision != -1:
        res += ' (from SVN server)'
        res += '\nRevision: ' + str(revision)
    else:
        res += ' (from tgz)'
    res += '\nAuthor: Andres Riancho and the w3af team.'
    return res
