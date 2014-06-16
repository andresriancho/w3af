"""
FileNameMutant.py

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
import urllib
import re
import copy

from w3af.core.data.fuzzer.mutants.urlparts_mutant import (URLPartsContainer,
                                                           URLPartsMutant,
                                                           TOKEN)


CHUNK_RE = re.compile(r'([a-zA-Z0-9]+)')
CHUNK_RE_2 = re.compile(r'[a-zA-Z0-9]')


class FileNameMutant(URLPartsMutant):
    """
    This class is a filename mutant.
    """
    @staticmethod
    def get_mutant_type():
        return 'url filename'

    def get_url(self):
        """
        :return: The URL, as modified by "set_token_value()"
        """
        domain_path = self._freq.get_url().get_domain_path()

        # Please note that this double encoding is needed if we want to work
        # with mod_rewrite
        encoded = urllib.quote_plus(self._url_parts_dc[TOKEN].get_value(),
                                    self._safe_encode_chars)
        if self._double_encoding:
            encoded = urllib.quote_plus(encoded, safe=self._safe_encode_chars)

        domain_path.set_file_name('%s%s%s' % (self._url_parts_dc.url_start,
                                              encoded,
                                              self._url_parts_dc.url_end))
        return domain_path

    get_uri = get_url

    def found_at(self):
        """
        :return: A string representing WHAT was fuzzed.
        """
        fmt = '"%s", using HTTP method %s. The modified parameter was the URL'\
              ' filename, with value: "%s".'
        return fmt % (self.get_url(), self.get_method(), self.get_token_value())

    @classmethod
    def create_mutants(cls, freq, mutant_str_list, fuzzable_param_list,
                       append, fuzzer_config):
        """
        This is a very important method which is called in order to create
        mutants. Usually called from fuzzer.py module.
        
        :param fuzzable_param_list: Please note that in this case the user
                                    specifies the chunk of the filename that
                                    he wants to fuzz. Chunks:
                                        foo.bar.html
                                        0   1   2
        """
        if not fuzzer_config['fuzz_url_filenames']:
            return []

        res = []
        fname = freq.get_url().get_file_name()
        fname_chunks = [x for x in CHUNK_RE.split(fname) if x]

        for idx, fn_chunk in enumerate(fname_chunks):

            if not (fuzzable_param_list == [] or idx in fuzzable_param_list):
                continue

            for mutant_str in mutant_str_list:

                if CHUNK_RE_2.match(fn_chunk):
                    fname_token = (fn_chunk if append else '') + mutant_str
                    fname_start = ''.join(fname_chunks[:idx])
                    fname_end = ''.join(fname_chunks[idx + 1:])

                    url_parts_container = URLPartsContainer(fname_start,
                                                            fname_token,
                                                            fname_end)

                    freq_copy = copy.deepcopy(freq)
                    m = cls(freq_copy)
                    m.set_dc(url_parts_container)
                    res.append(m)

                    # Same URLs but with different types of encoding!
                    freq_copy = copy.deepcopy(freq)
                    m2 = cls(freq_copy)
                    m2.set_dc(url_parts_container)
                    #m2.set_double_encoding(True)
                    m2.set_safe_encode_chars('/')

                    if m2.get_url() != m.get_url():
                        res.append(m2)

        return res
