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
from w3af.core.data.request.HTTPQsRequest import HTTPQSRequest


class CookieMutant(Mutant):
    """
    This class is a headers mutant.
    """
    def __init__(self, freq):
        Mutant.__init__(self, freq)

    def get_mutant_type(self):
        return 'cookie'

    def set_dc(self, c):
        self.set_cookie(c)

    def get_dc(self):
        return self.get_cookie()

    def set_mod_value(self, val):
        """
        Set the value of the variable that this mutant modifies.
        """
        try:
            self._freq._cookie[self.get_var()][self._index] = val
        except Exception:
            msg = 'The mutant object wasn\'t correctly initialized.'
            raise ValueError(msg)

    def get_mod_value(self):
        try:
            return self._freq._cookie[self.get_var()][self._index]
        except:
            msg = 'The mutant object wasn\'t correctly initialized.'
            raise ValueError(msg)

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

    def print_mod_value(self):
        fmt = 'The cookie data that was sent is: "%s".'
        return fmt % self.get_dc()

    @staticmethod
    def create_mutants(freq, mutant_str_list, fuzzable_param_list,
                       append, fuzzer_config, data_container=None):
        """
        This is a very important method which is called in order to create
        mutants. Usually called from fuzzer.py module.
        """
        if not isinstance(freq, HTTPQSRequest):
            return []

        if not fuzzer_config['fuzz_cookies']:
            return []

        orig_cookie = freq.get_cookie()

        return Mutant._create_mutants_worker(freq, CookieMutant,
                                             mutant_str_list,
                                             fuzzable_param_list,
                                             append, fuzzer_config,
                                             data_container=orig_cookie)
