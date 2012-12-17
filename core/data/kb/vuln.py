'''
vuln.py

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
from core.data.kb.info import info as info
from core.data.fuzzer.mutants.mutant import Mutant


class vuln(info):
    '''
    This class represents a web vulnerability.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    def __init__(self, data_obj=None):
        info.__init__(self, data_obj)

        # Default values
        self._method = None
        self._id = None
        self._dc = None
        self._severity = None
        self._variable = None
        self._mutant = None

        if isinstance(data_obj, Mutant) or \
        isinstance(data_obj, vuln):
            self.set_method(data_obj.get_method())
            self.set_dc(data_obj.get_dc())
            self.set_var(data_obj.get_var())
            self.set_uri(data_obj.get_uri())
            self.set_mutant(data_obj)

    def set_mutant(self, mutant):
        '''
        Sets the mutant that created this vuln.
        '''
        self._mutant = mutant

    def get_mutant(self):
        return self._mutant

    def set_var(self, variable):
        self._variable = variable

    def set_dc(self, dc):
        self._dc = dc

    def set_severity(self, severity):
        self._severity = severity

    def get_method(self):
        if self._mutant:
            return self._mutant.get_method()
        else:
            return self._method

    def get_var(self):
        if self._mutant:
            return self._mutant.get_var()
        else:
            return self._variable

    def get_dc(self):
        if self._mutant:
            return self._mutant.get_dc()
        else:
            return self._dc

    def get_severity(self):
        return self._severity

    def get_desc(self):
        if self._id is not None and self._id != 0:
            if not self._desc.endswith('.'):
                self._desc += '.'

            # One request OR more than one request
            desc_to_return = self._desc
            if len(self._id) > 1:
                desc_to_return += ' This vulnerability was found in the'\
                                  ' requests with ids %s.'
                id_range = self._convert_to_range_wrapper(self._id)
                desc_to_return = desc_to_return % id_range
            else:
                desc_to_return += ' This vulnerability was found in the'\
                                  ' request with id %s.'
                desc_to_return = desc_to_return % self._id[0]
            return desc_to_return
        else:
            return self._desc

    def __repr__(self):
        return '<vuln object for vulnerability: "' + self._desc + '">'
