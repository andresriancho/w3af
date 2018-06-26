"""
retirejs.py

Copyright 2018 Andres Riancho

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
import os
import json
import hashlib
import tempfile
import subprocess

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.controllers.misc.which import which
from w3af.core.data.db.disk_set import DiskSet
from w3af.core.data.kb.info import Info


class retirejs(GrepPlugin):
    """
    Uses retirejs to identify javascript libraries with known vulnerabilities

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    METHODS = ('GET',)
    HTTP_CODES = (200,)
    RETIRE_CMD = 'retire --outputformat json --outputpath %s --jspath %s'

    def __init__(self):
        GrepPlugin.__init__(self)

        self._analyzed_hashes = DiskSet(table_prefix='retirejs')
        self._retirejs_path = self._get_retirejs_path()
        self._retirejs_exit_code_result = None
        self._retirejs_exit_code_was_run = False

    def grep(self, request, response):
        """
        Send HTTP responses to retirejs and parse JSON output.

        For performance, avoid running retirejs on the same file more than once.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        if not self._retirejs_exit_code():
            return

        if request.get_method() not in self.METHODS:
            return

        if response.get_code() not in self.HTTP_CODES:
            return

        if not response.is_text_or_html():
            return

        if not self._should_analyze(response):
            return

        self._analyze_response(response)

    def end(self):
        self._analyzed_hashes.cleanup()

    def _retirejs_exit_code(self):
        """
        Runs retirejs on an empty file to check that the return code is 0, this
        is just a safety check to make sure everything is working. It is only
        run once.

        :return: True if everything works
        """
        if self._retirejs_exit_code_was_run:
            return self._retirejs_exit_code_result

        check_file = tempfile.NamedTemporaryFile(suffix='retirejs-check-',
                                                 prefix='.w3af',
                                                 delete=False)
        check_file.write('')
        check_file.close()

        output_file = tempfile.NamedTemporaryFile(suffix='retirejs-output-',
                                                  prefix='.w3af',
                                                  delete=False)
        output_file.close()

        args = (output_file.name, check_file.name)
        cmd = self.RETIRE_CMD % args

        try:
            subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError:
            self._retirejs_exit_code_result = False
        else:
            self._retirejs_exit_code_result = True
        finally:
            self._remove_file(output_file.name)
            self._remove_file(check_file.name)

        return self._retirejs_exit_code_result

    def _should_analyze(self, response):
        """
        :param response: HTTP response
        :return: True if we should analyze this HTTP response
        """
        response_hash = hashlib.md5(response.get_body()).hexdigest()

        if response_hash in self._analyzed_hashes:
            return False

        self._analyzed_hashes.add(response_hash)
        return True

    def _analyze_response(self, response):
        """
        :return: None, save the findings to the KB.
        """
        response_file = self._save_response_to_file(response)
        json_doc = self._analyze_file(response_file)
        self._remove_file(response_file)
        self._json_to_kb(response, json_doc)

    def _save_response_to_file(self, response):
        response_file = tempfile.NamedTemporaryFile(suffix='retirejs-response-',
                                                    prefix='.w3af',
                                                    delete=False)

        response_file.write(response.get_body())
        response_file.close()

        return response_file.name

    def _analyze_file(self, response_file):
        """
        Analyze a file and return the result as JSON

        :param response_file: File holding HTTP response body
        :return: JSON document
        """
        json_file = tempfile.NamedTemporaryFile(suffix='retirejs-output-',
                                                prefix='.w3af',
                                                delete=False)
        json_file.close()

        args = (json_file.name, response_file)
        cmd = self.RETIRE_CMD % args

        try:
            subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError:
            # retirejs will return code != 0 when a vulnerability is found
            # we use this to decide when we need to parse the output
            try:
                return json.loads(json_file.name)
            except Exception, e:
                msg = 'Failed to parse retirejs output. Exception: "%s"'
                om.out.debug(msg % e)
                return []
        else:
            return []
        finally:
            self._remove_file(json_file.name)

    def _remove_file(self, response_file):
        """
        Remove a file from disk. Don't fail if the file doesn't exist
        :param response_file: The file path to remove
        :return: None
        """
        try:
            os.remove(response_file)
        except:
            pass

    def _json_to_kb(self, response, json_doc):
        raise NotImplementedError

    def _get_retirejs_path(self):
        """
        :return: Path to the retirejs binary
        """
        paths_to_retire = which('retire')

        # The dependency check script guarantees that there will always be
        # at least one installation of the retirejs command.
        return paths_to_retire[0]

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        Uses retirejs [0] to identify vulnerable javascript libraries in HTTP
        responses.
        
        [0] https://github.com/retirejs/retire.js/
        """
