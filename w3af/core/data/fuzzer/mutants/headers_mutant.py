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


class HeadersMutant(Mutant):
    """
    This class is a headers mutant.
    """
    @staticmethod
    def get_mutant_type():
        return 'headers'

    def get_dc(self):
        return self._freq.get_headers()

    def set_dc(self, new_headers):
        return self._freq.set_headers(new_headers)

    def found_at(self):
        """
        :return: A string representing WHAT was fuzzed.
        """
        fmt = '"%s", using HTTP method %s. The modified header was: "%s"'\
              ' and it\'s value was: "%s".'

        return fmt % (self.get_url(), self.get_method(), self.get_token_name(),
                      self.get_token_value())

    @classmethod
    def create_mutants(cls, freq, mutant_str_list, fuzzable_param_list,
                       append, fuzzer_config, data_container=None):
        """
        This is a very important method which is called in order to create
        mutants. Usually called from fuzzer.py module.
        """
        fuzzable_headers = fuzzer_config['fuzzable_headers'] + freq.get_force_fuzzing_headers()

        if not fuzzable_headers:
            return []

        # Generate a list with the headers we'll fuzz
        fuzzable_param_list = fuzzable_param_list + fuzzable_headers

        return cls._create_mutants_worker(freq, cls, mutant_str_list,
                                          fuzzable_param_list,
                                          append, fuzzer_config)
