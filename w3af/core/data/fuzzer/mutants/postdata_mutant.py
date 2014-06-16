"""
postdata_mutant.py

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
from w3af.core.data.dc.generic.form import Form


class PostDataMutant(Mutant):
    """
    This class is a post data mutant.
    """
    def set_dc(self, data_container):
        self._freq.set_data(data_container)

    def get_dc(self):
        return self._freq.get_raw_data()

    @staticmethod
    def get_mutant_type():
        return 'post data'

    def found_at(self):
        """
        :return: A string representing WHAT was fuzzed.
        """
        fmt = '"%s", using HTTP method %s. The sent post-data was: "%s"'
        fmt += ' which modifies the "%s" parameter.'

        return fmt % (self.get_uri(), self.get_method(),
                      self.get_dc().get_short_printable_repr(),
                      self.get_token().get_name())

    @classmethod
    def create_mutants(cls, freq, mutant_str_list, fuzzable_param_list,
                       append, fuzzer_config):
        """
        This is a very important method which is called in order to create
        mutants. Usually called from fuzzer.py module.
        """
        if not isinstance(freq.get_raw_data(), Form):
            return []

        return cls._create_mutants_worker(freq, cls, mutant_str_list,
                                          fuzzable_param_list,
                                          append, fuzzer_config)
