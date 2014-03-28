"""
elf.py

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


class elf:
    """
    This class represents a tiny ELF file. I created this ELF file with the GREAT paper that
    can be read at http://www.muppetlabs.com/~breadbox/software/tiny/teensy.html .

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, arch='32bit'):
        self._arch = arch
        self._shellcode = '\x90'

    def set_shell_code(self, sc):
        self._shellcode = sc

    def get_shell_code(self):
        return self._shellcode

    def dump(self):
        """
        :return: A string with the complete ELF file.
        """
        _header = ''
        _header = '\x7f\x45\x4c\x46\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        _header += '\x02\x00\x03\x00\x01\x00\x00\x00\x54\x80\x04\x08\x34\x00\x00\x00'
        _header += '\x00\x00\x00\x00\x00\x00\x00\x00\x34\x00\x20\x00\x01\x00\x00\x00'
        _header += '\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x80\x04\x08\x00'
        _header += '\x80\x04\x08\x5e\x00\x00\x00\x5e\x00\x00\x00\x05\x00\x00\x00\x00\x10\x00\x00'
        _exit = '\x31\xc0\x40\xcd\x80'

        return _header + self._shellcode + _exit

if __name__ == '__main__':
    e = elf()
    f = file('genElf', 'w')
    f.write(e.dump())
    f.close()
