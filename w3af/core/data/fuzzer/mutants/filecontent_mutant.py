"""
filecontent_mutant.py

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
from w3af.core.data.dc.generic.form import Form
from w3af.core.data.dc.utils.file_token import FileDataToken
from w3af.core.data.dc.utils.token import DataToken
from w3af.core.data.dc.multipart_container import MultipartContainer


class FileContentMutant(PostDataMutant):
    """
    This class is a file content mutant, this means that the payload is sent
    in the content of a file which is uploaded over multipart/post
    """
    @staticmethod
    def get_mutant_type():
        return 'file content'

    def found_at(self):
        """
        :return: A string representing WHAT was fuzzed.
        """
        dc = self.get_dc()
        dc_short = dc.get_short_printable_repr()

        msg = '"%s", using HTTP method %s. The sent post-data was: "%s"' \
              " which modified the uploaded file content."

        return msg % (self.get_url(), self.get_method(), dc_short)

    @classmethod
    def create_mutants(cls, freq, payload_list, fuzzable_param_list,
                       append, fuzzer_config):
        """
        This is a very important method which is called in order to create
        mutants. Usually called from fuzzer.py module.
        """
        if not fuzzer_config['fuzz_form_files']:
            return []

        if not freq.get_file_vars():
            return []

        if not isinstance(freq.get_raw_data(), Form):
            return []

        form = freq.get_raw_data()
        multipart_container = OnlyTokenFilesMultipartContainer(form)
        freq.set_data(multipart_container)

        res = cls._create_mutants_worker(freq, cls, payload_list,
                                         freq.get_file_vars(),
                                         append, fuzzer_config)
        return res


class OnlyTokenFilesMultipartContainer(MultipartContainer):
    """
    A MultipartContainer which only allows me to tokenize (and then modify) the
    parameters which are going to be later send as files by multipart/encoding.

    Also, when fuzzing I'll be creating my tokens using FileDataToken: a great
    way to abstract the fact that payloads are sent in the content of a file.
    """
    def set_token(self, token_path):
        """
        Modified to pass the filename to the FileDataToken
        """
        for key, val, ipath, setter in self.iter_setters():

            if ipath == token_path:
                if isinstance(val, (DataToken, FileDataToken)):
                    # Avoid double-wrapping
                    token = val
                else:
                    if key in self.get_file_vars():
                        fname = val.filename if hasattr(val, 'filename') else None
                        token = FileDataToken(key, val, fname, ipath)
                    else:
                        token = DataToken(key, val, ipath)

                setter(token)
                self.token = token

                return token