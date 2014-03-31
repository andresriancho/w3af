"""
HeadersMutant.py

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
from w3af.core.data.fuzzer.mutants.mutant import Mutant
from w3af.core.data.dc.headers import Headers


class HeadersMutant(Mutant):
    """
    This class is a headers mutant.
    """
    def __init__(self, freq):
        Mutant.__init__(self, freq)

    def get_mutant_type(self):
        return 'headers'

    def get_dc(self):
        return self._headers

    def set_dc(self, dc):
        # See comment below (search for __HERE__).
        fixed_headers = Headers()

        for key, value in dc.iteritems():
            if isinstance(value, list):
                value = value[0]

            fixed_headers[key] = value

        self._headers = fixed_headers

    def found_at(self):
        """
        :return: A string representing WHAT was fuzzed.
        """
        fmt = '"%s", using HTTP method %s. The modified header was: "%s"'\
              ' and it\'s value was: "%s".'

        return fmt % (self.get_url(), self.get_method(), self.get_var(),
                      self.get_mod_value())

    def set_mod_value(self, val):
        """
        Set the value of the variable that this mutant modifies.
        """
        try:
            self._freq._headers[self.get_var()] = val
        except:
            msg = 'The headers mutant object wasn\'t  correctly initialized.'
            raise ValueError(msg)

    def get_mod_value(self):
        try:
            return self._freq._headers[self.get_var()]
        except:
            msg = 'The headers mutant object wasn\'t  correctly initialized.'
            raise ValueError(msg)

    @staticmethod
    def create_mutants(freq, mutant_str_list, fuzzable_param_list,
                       append, fuzzer_config, data_container=None):
        """
        This is a very important method which is called in order to create
        mutants. Usually called from fuzzer.py module.
        """
        if not fuzzer_config['fuzzable_headers']:
            return []

        # Generate a list with the headers we'll fuzz
        fuzzable_param_list = fuzzable_param_list + fuzzer_config[
            'fuzzable_headers']

        # Generate a dummy object that we'll use for fixing the "impedance mismtach"
        # between the Headers() object that doesn't have the same form as a
        # generic DataContainer. Headers look like:
        #    {'a':'b'}
        # While data containers look like
        #    {'a': ['b',]}
        #
        # Note that I'm undoing this in the set_dc method above.
        # (search for __HERE__)
        #
        orig_headers = freq.get_headers()
        headers_copy = orig_headers.copy()
        for header_name in fuzzer_config['fuzzable_headers']:
            headers_copy[header_name] = ''
        cloned_headers = headers_copy.clone_with_list_values()

        return Mutant._create_mutants_worker(
            freq, HeadersMutant, mutant_str_list,
            fuzzable_param_list,
            append, fuzzer_config,
            data_container=cloned_headers)
