"""
fuzzer.py

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
import w3af.core.data.kb.config as cf
import w3af.core.controllers.output_manager as om

from w3af.core.data.fuzzer.mutants.querystring_mutant import QSMutant
from w3af.core.data.fuzzer.mutants.postdata_mutant import PostDataMutant
from w3af.core.data.fuzzer.mutants.filename_mutant import FileNameMutant
from w3af.core.data.fuzzer.mutants.urlparts_mutant import URLPartsMutant
from w3af.core.data.fuzzer.mutants.headers_mutant import HeadersMutant
from w3af.core.data.fuzzer.mutants.json_mutant import JSONMutant
from w3af.core.data.fuzzer.mutants.cookie_mutant import CookieMutant
from w3af.core.data.fuzzer.mutants.filecontent_mutant import FileContentMutant


def create_mutants(freq, mutant_str_list, append=False,
                   fuzzable_param_list=[], orig_resp=None):
    """
    :param freq: A fuzzable request with a DataContainer inside.
    :param mutant_str_list: a list with mutant strings to use
    :param append: This indicates if the content of mutant_str_list should
        be appended to the variable value
    :param fuzzable_param_list: If [] then all params are fuzzed. If ['a'],
        then only 'a' is fuzzed.
    :return: A Mutant object List.
    """
    result = []
    fuzzer_config = _get_fuzzer_config(freq)

    mutant_tuple = (QSMutant, PostDataMutant, FileNameMutant, URLPartsMutant,
                    HeadersMutant, JSONMutant, CookieMutant, FileContentMutant)

    for mutant_kls in mutant_tuple:
        new_mutants = mutant_kls.create_mutants(freq, mutant_str_list,
                                                fuzzable_param_list, append,
                                                fuzzer_config)

        
        mutant_name = mutant_kls.get_mutant_class()
        om.out.debug('%s created %s new mutants for "%s".' % (mutant_name,
                                                              len(new_mutants),
                                                              freq))
        
        result.extend(new_mutants)

    #
    # Improvement to reduce false positives with a double check:
    #    Get the original response and link it to each mutant.
    #
    # Improvement to reduce network traffic:
    #    If the original response has an "ETag" header, set a "If-None-Match"
    #    header with the same value. On a test that I ran, the difference was
    #    very noticeable:
    #        - Without sending ETag headers: 304046 bytes
    #        - Sending ETag headers:          55320 bytes
    #
    # This is very impressing, but the performance enhancement is only
    # possible IF the remote server sends the ETag header, and for example
    # Apache+PHP doesn't send that tag by default (only sent if the PHP developer
    # added some code to his PHP to do it).
    #
    if orig_resp is not None:

        headers = orig_resp.get_headers()
        etag = headers.get('ETag', None)

        for m in result:
            m.set_original_response_body(orig_resp.get_body())

            if etag is not None:
                orig_headers = m.get_headers()
                orig_headers['If-None-Match'] = etag
                m.set_headers(orig_headers)

    return result


def _get_fuzzer_config(freq):
    """
    :return: This function verifies the configuration, and creates a map of
             things that can be fuzzed.
    """
    config = cf.cf

    fuzzer_config = {}

    fuzzer_config['fuzzable_headers'] = config.get('fuzzable_headers')
    fuzzer_config['fuzz_cookies'] = config.get('fuzz_cookies', False)
    fuzzer_config['fuzz_url_filenames'] = config.get(
        'fuzz_url_filenames', False)
    fuzzer_config['fuzzed_files_extension'] = config.get(
        'fuzzed_files_extension', 'gif')
    fuzzer_config['fuzz_form_files'] = config.get('fuzz_form_files', False)
    fuzzer_config['fuzz_url_parts'] = config.get('fuzz_url_parts', False)

    return fuzzer_config
