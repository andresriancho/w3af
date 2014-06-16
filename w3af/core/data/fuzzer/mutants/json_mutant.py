"""
JSONMutant.py

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
from w3af.core.data.fuzzer.mutants.postdata_mutant import PostDataMutant
from w3af.core.data.dc.json_container import JSONContainer


class JSONMutant(PostDataMutant):
    """
    This class is a JSON mutant.
    """
    @staticmethod
    def get_mutant_type():
        return 'JSON data'

    def get_headers(self):
        # TODO: Not working?
        #headers = super(XmlRpcMutant, self).get_headers()
        headers = self.get_fuzzable_request().get_headers()
        headers['Content-Type'] = 'application/json'
        return headers

    def found_at(self):
        """
        I had to implement this again here instead of just inheriting from
        PostDataMutant because of the duplicated parameter name support which
        I added to the framework.

        :return: A string representing WHAT was fuzzed.
        """
        fmt = '"%s", using HTTP method %s. The sent JSON-data was: "%s"'
        return fmt % (self.get_url(), self.get_method(),
                      self.get_dc().get_short_printable_repr())

    @classmethod
    def create_mutants(cls, freq, mutant_str_list, fuzzable_param_list,
                       append, fuzzer_config):
        """
        This is a very important method which is called in order to create
        mutants. Usually called from fuzzer.py module.
        """
        if not isinstance(freq.get_raw_data(), JSONContainer):
            return []

        return cls._create_mutants_worker(freq, cls, mutant_str_list,
                                          fuzzable_param_list,
                                          append, fuzzer_config)
