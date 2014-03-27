"""
MutantXMLRPC.py

Copyright 2009 Andres Riancho

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


class MutantXMLRPC(PostDataMutant):
    """
    This class is a XMLRPC mutant.

    *** IMPORTANT ***
    Not in use in any section of the code!
    *** IMPORTANT ***
    """
    def __init__(self, freq):
        PostDataMutant.__init__(self, freq)

    def get_mutant_type(self):
        return 'XMLRPC data'

    def get_headers(self):
        headers = self._headers
        # TODO: Verify this, I had no internet while adding the next line
        headers['Content-Type'] = 'application/xml'
        return headers

    def found_at(self):
        """
        I had to implement this again here instead of just inheriting from
        PostDataMutant because of the duplicated parameter name support which
        I added to the framework.

        :return: A string representing WHAT was fuzzed.
        """
        res = ''
        res += '"' + self.get_url() + '", using HTTP method '
        res += self.get_method() + '. The sent JSON-data was: "'
        res += str(self.get_dc())
        res += '"'
        return res
