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
import json
import cgi
import copy

from w3af.core.data.fuzzer.mutants.postdata_mutant import PostDataMutant
from w3af.core.data.request.HTTPPostDataRequest import HTTPPostDataRequest


def is_json(postdata):
    # Only do the JSON stuff if this is really a JSON request...
    try:
        cgi.parse_qs(postdata, keep_blank_values=True,
                     strict_parsing=True)
    except Exception:
        # We have something that's not URL encoded in the postdata, it could
        # be something like JSON, XML, or multipart encoding. Let's try with
        # JSON
        try:
            json.loads(postdata)
        except:
            # It's not json, maybe XML or multipart, I don't really care
            # (at least not in this section of the code)
            return False
        else:
            # Now, fuzz the parsed JSON data...
            return True
    else:
        # No need to do any JSON stuff, the postdata is urlencoded
        return False


# We define a function that creates the mutants...
def _make_json_mutants(freq, mutant_str_list, fuzzable_param_list,
                       append, parsed_json_inst):
    res = []

    for fuzzed_json, original_value in _fuzz_json(mutant_str_list,
                                                  parsed_json_inst, append):
        freq_copy = freq.copy()
        m = JSONMutant(freq_copy)
        m.set_original_value(original_value)
        m.set_var('<JSON data>')
        m.set_dc(fuzzed_json)

        res.append(m)

    return res


# Now we define a function that does the work...
def _fuzz_json(mutant_str_list, parsed_json_inst, append):
    """
    :return: A list with tuples containing (fuzzed list/dict/string/int that
             represents a JSON object, original value)
    """
    res = []

    if isinstance(parsed_json_inst, int):
        for mutant_str in mutant_str_list:
            if mutant_str.isdigit():
                # This (a mutant str that really is an integer) will happend
                # once every 100000 years, but I wanted to be sure to cover all
                # cases. This will look something like:
                #
                # 1
                #
                # In the postdata.
                if append:
                    fuzzed = int('%s%s' % (parsed_json_inst, mutant_str))
                    res.append((fuzzed, parsed_json_inst))
                else:
                    fuzzed = int(mutant_str)
                    res.append((fuzzed, parsed_json_inst))

    elif isinstance(parsed_json_inst, basestring):
        # This will look something like:
        #
        # "abc"
        #
        # In the postdata.
        for mutant_str in mutant_str_list:
            if append:
                fuzzed = parsed_json_inst + mutant_str
                res.append((fuzzed, parsed_json_inst))
            else:
                res.append((mutant_str, parsed_json_inst))

    elif isinstance(parsed_json_inst, list):
        # This will look something like:
        #
        # ["abc", "def"]
        #
        # In the postdata.
        for item, i in zip(parsed_json_inst, xrange(len(parsed_json_inst))):
            fuzzed_item_list = _fuzz_json(
                mutant_str_list, parsed_json_inst[i], append)
            for fuzzed_item, original_value in fuzzed_item_list:
                json_postdata_copy = copy.deepcopy(parsed_json_inst)
                json_postdata_copy[i] = fuzzed_item
                res.append((json_postdata_copy, original_value))

    elif isinstance(parsed_json_inst, dict):
        for key in parsed_json_inst:
            fuzzed_item_list = _fuzz_json(
                mutant_str_list, parsed_json_inst[key], append)
            for fuzzed_item, original_value in fuzzed_item_list:
                json_postdata_copy = copy.deepcopy(parsed_json_inst)
                json_postdata_copy[key] = fuzzed_item
                res.append((json_postdata_copy, original_value))

    return res


class JSONMutant(PostDataMutant):
    """
    This class is a JSON mutant.
    """
    def __init__(self, freq):
        PostDataMutant.__init__(self, freq)

    def get_mutant_type(self):
        return 'JSON data'

    def get_headers(self):
        headers = self._headers
        # TODO: Verify this, I had no internet while adding the next line
        headers['Content-Type'] = 'application/json'
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

    @staticmethod
    def create_mutants(freq, mutant_str_list, fuzzable_param_list,
                       append, fuzzer_config):
        """
        This is a very important method which is called in order to create
        mutants. Usually called from fuzzer.py module.
        """
        if not isinstance(freq, HTTPPostDataRequest):
            return []

        if not is_json(freq.get_data()):
            return []

        # Now, fuzz the parsed JSON data...
        post_data = freq.get_data()
        parsed_json_inst = json.loads(post_data)
        return _make_json_mutants(freq, mutant_str_list,
                                  fuzzable_param_list,
                                  append, parsed_json_inst)
