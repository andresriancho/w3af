'''
io.py

Copyright 2011 Andres Riancho

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
from StringIO import StringIO

class NamedStringIO(StringIO):
    
    def __init__(self, str, name):
        StringIO.__init__(self, str)
        self._name = name
    
    @property
    def name(self):
        return self._name
    


FILE_ATTRS = ('read', 'write', 'name', 'seek', 'closed')

def is_file_like(f):
    # TODO: When w3af migrates to Python 3 this function will likely
    # disappear as we'll be able to do this check:
    # >>> isinstance(f, io.IOBase)
    return all(hasattr(f, at) for at in FILE_ATTRS)

