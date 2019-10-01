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
from w3af.core.data.fuzzer.mutants.xmlrpc_mutant import XmlRpcMutant

ALL_MUTANTS = (QSMutant, PostDataMutant, FileNameMutant, URLPartsMutant,
               HeadersMutant, JSONMutant, CookieMutant, FileContentMutant,
               XmlRpcMutant)


def create_mutants(freq,
                   mutant_str_list,
                   append=False,
                   fuzzable_param_list=None,
                   orig_resp=None,
                   mutant_tuple=ALL_MUTANTS):
    """
    :param freq: A fuzzable request with a DataContainer inside.
    :param mutant_str_list: a list with mutant strings to use
    :param append: This indicates if the content of mutant_str_list should
                   be appended to the variable value
    :param fuzzable_param_list: If [] then all params are fuzzed. If ['a'],
                                then only 'a' is fuzzed.
    :param mutant_tuple: a tuple which contains classes of the mutants
                         to be returned
    :param orig_resp: The original HTTP response
    :return: A Mutant object List.
    """
    fuzzable_param_list = fuzzable_param_list or []
    result = []
    fuzzer_config = _get_fuzzer_config()

    for mutant_kls in mutant_tuple:
        new_mutants = mutant_kls.create_mutants(freq, mutant_str_list,
                                                fuzzable_param_list, append,
                                                fuzzer_config)
        result.extend(new_mutants)

    msg = 'Created %s mutants for "%s" (%s)'

    count_data = {}
    for mutant in result:
        if mutant.get_mutant_type() in count_data:
            count_data[mutant.get_mutant_type()] += 1
        else:
            count_data[mutant.get_mutant_type()] = 1

    count_summary = ', '.join(['%s: %s' % (i, j) for i, j in count_data.items()])
    om.out.debug(msg % (len(result), freq, count_summary))

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
    # Apache+PHP doesn't send that tag by default (only sent if the PHP
    # developer added some code to his PHP to do it).
    #
    if orig_resp is not None and result:

        headers = orig_resp.get_headers()
        etag, etag_header_name = headers.iget('ETag', None)

        for m in result:
            m.set_original_response_body(orig_resp.get_body())

            if etag is not None:
                orig_headers = m.get_headers()
                orig_headers['If-None-Match'] = etag
                m.set_headers(orig_headers)

    return result


CONF_KEYS = [('fuzzable_headers', []),
             ('fuzz_cookies', False),
             ('fuzz_url_filenames', False),
             ('fuzzed_files_extension', 'gif'),
             ('fuzz_form_files', False),
             ('fuzz_url_parts', False)]


def _get_fuzzer_config():
    """
    :return: This function verifies the configuration, and creates a map of
             things that can be fuzzed.
    """
    config = cf.cf
    fuzzer_config = {}

    for conf_name, default in CONF_KEYS:
        fuzzer_config[conf_name] = config.get(conf_name, default)

    return fuzzer_config
