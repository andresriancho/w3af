"""
vuln.py

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
from w3af.core.data.kb.info import Info
from w3af.core.data.constants.severity import INFORMATION, LOW, MEDIUM, HIGH
from w3af.core.data.fuzzer.mutants.mutant import Mutant
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.fuzzer.mutants.empty_mutant import EmptyMutant


class Vuln(Info):
    """
    This class represents a web vulnerability.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, name, desc, severity, response_ids, plugin_name,
                 vulndb_id=None):
        """
        :param name: The vulnerability name, will be checked against the values
                     in core.data.constants.vulns.
        :param desc: The vulnerability description
        :param severity: The severity for this object
        :param response_ids: A list of response ids associated with this vuln
        :param plugin_name: The name of the plugin which identified the vuln
        :param vulndb_id: The vulnerability ID in the vulndb that is associated
                          with this Info instance.

        :see: https://github.com/vulndb/data
        """
        Info.__init__(self, name, desc, response_ids, plugin_name,
                      vulndb_id=vulndb_id)

        self._severity = None
        self.set_severity(severity)

    @classmethod
    def from_mutant(cls, name, desc, severity, response_ids, plugin_name, mutant):
        """
        TODO: I wanted to use super(Vuln, cls).from_mutant here but I was
        unable to make it work. Refactoring required to avoid code duplication
        with info.py. The same applies to all classmethods
        
        :return: A vuln instance with the proper data set based on the values
                 taken from the mutant.
        """
        if not isinstance(mutant, Mutant):
            raise TypeError('Mutant expected in from_mutant.')
        
        inst = cls(name, desc, severity, response_ids, plugin_name)

        inst.set_uri(mutant.get_uri())
        inst.set_method(mutant.get_method())
        inst.set_mutant(mutant)
            
        return inst
        
    @classmethod
    def from_fr(cls, name, desc, severity, response_ids, plugin_name, freq):
        """
        :return: A vuln instance with the proper data set based on the values
                 taken from the fuzzable request.
        """
        if not isinstance(freq, FuzzableRequest):
            raise TypeError('FuzzableRequest expected in from_fr.')
        
        mutant = EmptyMutant(freq)
            
        return Vuln.from_mutant(name, desc, severity, response_ids, plugin_name,
                                mutant)
    
    @classmethod
    def from_vuln(cls, other_vuln):
        """
        :return: A clone of other_vuln. 
        """
        if not isinstance(other_vuln, Vuln):
            raise TypeError('Vuln expected in from_vuln.')
        
        name = other_vuln.get_name()
        desc = other_vuln.get_desc()
        response_ids = other_vuln.get_id()
        plugin_name = other_vuln.get_plugin_name()
        severity = other_vuln.get_severity()
        
        inst = cls(name, desc, severity, response_ids, plugin_name)
        inst._string_matches = other_vuln.get_to_highlight()
        inst._mutant = other_vuln.get_mutant()

        for k in other_vuln.keys():
            inst[k] = other_vuln[k]

        return inst        
        
    def get_severity(self):
        return self._severity

    def set_severity(self, severity):
        if severity not in (INFORMATION, LOW, MEDIUM, HIGH):
            raise ValueError('Invalid severity value: %s' % severity)

        self._severity = severity

    def get_desc(self, with_id=True):
        return self._get_desc_impl('vulnerability', with_id)

    def __repr__(self):
        fmt = '<vuln object for vulnerability: "%s">'
        return fmt % self._desc
