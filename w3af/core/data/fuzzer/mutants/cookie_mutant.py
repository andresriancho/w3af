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

    def get_url(self):
        """
        The next methods (get_url and get_uri) are really simple, but they override
        the URL creation algorithm of HTTPQSRequest, that uses the self._dc
        attribute. If I don't have these methods, I end up with something like
        this:

        ========================================Request 15 - Sat Oct 27 21:05:34 2007========================================
        GET http://localhost/w3af/cookieFuzzing/cf.php?domain=%3CSCRIPT%3Ealert2%28%27bzbbw1R8AJ9ALQEM5jKI50fZn%27%29%3C%2FSCRIPT%3E HTTP/1.1
        Host: localhost
        Cookie: path=/~rasmus/; domain=<SCRIPT>alert2('bzbbw1R8AJ9ALQEM5jKI50fZn')</SCRIPT>; expires=Sun, 28-Oct-2007 01:05:34 GMT; TestCookie=something+from+somewh
        Accept-encoding: identity
        Accept: */*
        User-agent: w3af.org
        """
        return self._url

    def get_uri(self):
        return self._uri

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
        :return: A string representing WHAT was fuzzed.
        """
        fmt = '"%s", using HTTP method %s. The modified parameter was the'\
              ' session cookie with value: "%s".'

        # Depending on the data container, print different things:
        dc_length = len(self._freq._dc)

        if dc_length > 65:
            cookie_str = '...%s=%s...' % (self.get_var(), self.get_mod_value())
        else:
            cookie_str = str(self.get_dc())

        return fmt % (self.get_uri(), self.get_method(), cookie_str)

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

        return Mutant._create_mutants_worker(
            freq, CookieMutant, mutant_str_list,
            fuzzable_param_list,
            append, fuzzer_config,
            data_container=orig_cookie)
