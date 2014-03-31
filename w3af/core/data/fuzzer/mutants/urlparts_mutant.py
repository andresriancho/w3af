"""
urlparts_mutant.py

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

from w3af.core.data.fuzzer.mutants.mutant import Mutant
from w3af.core.data.request.HTTPQsRequest import HTTPQSRequest
from w3af.core.data.dc.data_container import DataContainer


class URLPartsMutant(Mutant):
    """
    This class is a urlparts mutant.
    """
    def __init__(self, freq):
        Mutant.__init__(self, freq)
        self._double_encoding = False
        self._safe_encode_chars = ''

    def get_mutant_type(self):
        return 'urlparts'

    def set_double_encoding(self, trueFalse):
        self._double_encoding = trueFalse

    def set_safe_encode_chars(self, safeChars):
        """
        :param safeChars: A string with characters we don't want to URL
                         encode in the filename. Example: '/&!'
        """
        self._safe_encode_chars = safeChars

    def get_url(self):
        """
        :return: The URL, as modified by "set_mod_value()"
        """
        domain_path = self._freq.get_url().get_domain_path()

        # Please note that this double encoding is needed if we want to work
        # with mod_rewrite
        encoded = urllib.quote_plus(self._mutant_dc['modified_part'],
                                    self._safe_encode_chars)
        if self._double_encoding:
            encoded = urllib.quote_plus(encoded, safe=self._safe_encode_chars)
        domain_path.set_path(
            self._mutant_dc['start'] + encoded + self._mutant_dc['end'])
        return domain_path

    get_uri = get_url

    def get_data(self):
        return None

    def print_mod_value(self):
        fmt = 'The sent %s is: "%s%s%s".'
        return fmt % (self.get_mutant_type(), self._mutant_dc['start'],
                      self._mutant_dc['modified_part'], self._mutant_dc['end'])

    def set_mod_value(self, val):
        self._mutant_dc['modified_part'] = val

    def get_mod_value(self):
        return self._mutant_dc['modified_part']

    def set_url(self, u):
        msg = 'You can\'t change the value of the URL in a URLPartsMutant'\
              ' instance.'
        raise ValueError(msg)

    def found_at(self):
        """
        :return: A string representing WHAT was fuzzed.
        """
        fmt = '"%s", using HTTP method %s. The modified parameter was the URL'\
              ' path, with value: "%s".'

        return fmt % (self.get_url(), self.get_method(), self.get_mod_value())

    @staticmethod
    def create_mutants(freq, mutant_str_list, fuzzable_param_list,
                       append, fuzzer_config, data_container=None):
        """
        This is a very important method which is called in order to create
        mutants. Usually called from fuzzer.py module.
        """
        if not fuzzer_config['fuzz_url_parts']:
            return []

        if not isinstance(freq, HTTPQSRequest):
            return []

        res = []
        path_sep = '/'
        path = freq.get_url().get_path()
        path_chunks = path.split(path_sep)
        for idx, p_chunk in enumerate(path_chunks):
            if not p_chunk:
                continue
            for mutant_str in mutant_str_list:
                divided_path = DataContainer()
                divided_path['start'] = path_sep.join(path_chunks[:idx] + [''])
                divided_path['end'] = path_sep.join([''] +
                                                    path_chunks[idx + 1:])
                divided_path['modified_part'] = \
                    (p_chunk if append else '') + urllib.quote_plus(mutant_str)
                freq_copy = freq.copy()
                freq_copy.set_url(freq.get_url())

                m = URLPartsMutant(freq_copy)
                m.set_original_value(p_chunk)
                m.set_var('modified_part')
                m.set_mutant_dc(divided_path)
                m.set_mod_value(mutant_str)
                res.append(m)

                # Same URLs but with different types of encoding!
                m2 = m.copy()
                m2.set_double_encoding(True)

                if m2.get_url() != m.get_url():
                    res.append(m2)

        return res
