"""
CookieMutant.py

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


class CookieMutant(Mutant):
    """
    This class is a headers mutant.
    """
    @staticmethod
    def get_mutant_type():
        return 'cookie'

    def set_dc(self, c):
        self._freq.set_cookie(c)

    def get_dc(self):
        return self._freq.get_cookie()

    def found_at(self):
        """
        Return a string representing WHAT was fuzzed. This string
        is used like this:
            - v.set_desc('SQL injection was found at: ' + mutant.found_at())
        """
        dc = self.get_dc()
        dc_short = dc.get_short_printable_repr()

        msg = '"%s", using HTTP method %s. The modified parameter was the'\
              ' session cookie with value: "%s".'

        return msg % (self.get_url(), self.get_method(), dc_short)

    @classmethod
    def create_mutants(cls, freq, mutant_str_list, fuzzable_param_list,
                       append, fuzzer_config):
        """
        This is a very important method which is called in order to create
        mutants. Usually called from fuzzer.py module.
        """
        if not fuzzer_config['fuzz_cookies']:
            return []

        return cls._create_mutants_worker(freq, cls, mutant_str_list,
                                          fuzzable_param_list, append,
                                          fuzzer_config)
