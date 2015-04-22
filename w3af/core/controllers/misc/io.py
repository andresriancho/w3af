"""
io.py

Copyright 2011 Andres Riancho

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
from StringIO import StringIO


class NamedStringIO(StringIO, str):
    """
    A file-like string.
    """
    def __new__(cls, *args, **kwargs):
        return super(NamedStringIO, cls).__new__(cls, args[0])

    def __init__(self, the_str, name):
        super(NamedStringIO, self).__init__(the_str)
        self._name = name

    # pylint: disable=E0202
    @property
    def name(self):
        return self._name


FILE_ATTRS = ('read', 'write', 'name', 'seek', 'closed')


def is_file_like(f):
    # TODO: When w3af migrates to Python 3k this function will likely
    # disappear as it'll be possible to do this check:
    # >>> isinstance(f, io.IOBase)
    return all(hasattr(f, at) for at in FILE_ATTRS)
