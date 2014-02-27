"""
PostDataMutant.py

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
from w3af.core.data.request.HTTPPostDataRequest import HTTPPostDataRequest


class PostDataMutant(Mutant):
    """
    This class is a post data mutant.
    """
    def __init__(self, freq):
        Mutant.__init__(self, freq)

    def get_mutant_type(self):
        return 'post data'

    def found_at(self):
        """
        :return: A string representing WHAT was fuzzed.
        """
        res = '"' + self.get_uri() + '", using HTTP method '
        res += self.get_method() + '. The sent post-data was: "'

        # Depending on the data container, print different things:
        dc_length = len(str(self.get_dc()))

        if dc_length > 65:
            res += '...' + self.get_var() + '=' + self.get_mod_value() + '...'
        else:
            res += str(self.get_dc())

        res += '" which modifies the "%s" parameter.' % self.get_var()

        return res

    @staticmethod
    def create_mutants(freq, mutant_str_list, fuzzable_param_list,
                       append, fuzzer_config):
        """
        This is a very important method which is called in order to create
        mutants. Usually called from fuzzer.py module.
        """
        if not isinstance(freq, HTTPPostDataRequest):
            return []

        return Mutant._create_mutants_worker(freq, PostDataMutant,
                                             mutant_str_list,
                                             fuzzable_param_list,
                                             append, fuzzer_config)
