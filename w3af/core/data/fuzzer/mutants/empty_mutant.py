"""
empty_mutant.py

Copyright 2014 Andres Riancho

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
from w3af.core.data.request.empty_request import EmptyFuzzableRequest
from w3af.core.data.dc.generic.nr_kv_container import NonRepeatKeyValueContainer


class EmptyMutant(Mutant):
    """
    A Mutant which points its set_dc and get_dc to an internal container, not
    related with a FuzzableRequest
    """
    def __init__(self, freq=None):
        self._dc = NonRepeatKeyValueContainer()

        freq = freq or EmptyFuzzableRequest()
        super(EmptyMutant, self).__init__(freq)

    def set_dc(self, data_container):
        self._dc = data_container

    def get_dc(self):
        return self._dc