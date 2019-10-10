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
import shlex
import hashlib
import tempfile
import subprocess32 as subprocess

import w3af.core.controllers.output_manager as om
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.misc.temp_dir import get_temp_dir
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.controllers.misc.which import which
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.misc.encoding import smart_str_ignore
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import URL as URL_OPTION
from w3af.core.data.options.option_list import OptionList


class retirejs(GrepPlugin):
    """
    Uses retirejs to identify javascript libraries with known vulnerabilities

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    METHODS = ('GET',)
    HTTP_CODES = (200,)

    RETIRE_CMD = 'retire -j --outputformat json --outputpath %s --jspath %s'
    RETIRE_CMD_VERSION = 'retire --version'
    RETIRE_CMD_JSREPO = 'retire -j --outputformat json --outputpath %s --jsrepo %s --jspath %s'

    RETIRE_VERSION = '2.'

    RETIRE_TIMEOUT = 5
    RETIRE_DB_URL = URL('https://raw.githubusercontent.com/RetireJS/retire.js/master/repository/jsrepository.json')
    BATCH_SIZE = 20

    def __init__(self):
        GrepPlugin.__init__(self)

        self._analyzed_hashes = ScalableBloomFilter()
        self._retirejs_path = self._get_retirejs_path()

        self._is_valid_retire_version = None
        self._is_valid_retirejs_exit_code = None
        self._should_run_retirejs_install_check = True

        self._retire_db_filename = None
        self._batch = []
        self._js_temp_directory = None

        # User-configured parameters
        self._retire_db_url = self.RETIRE_DB_URL

    def grep(self, request, response):
        """
        Send HTTP responses to retirejs and parse JSON output.

        For performance, avoid running retirejs on the same file more than once.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        if not self._retirejs_is_installed():
            return

        if request.get_method() not in self.METHODS:
            return

        if response.get_code() not in self.HTTP_CODES:
            return

        if 'javascript' not in response.content_type:
            return

        if not self._should_analyze(response):
            return

        self._download_retire_db()

        if self._retire_db_filename is None:
            return

        with self._plugin_lock:
            batch = self._add_response_to_batch(response)

            if not self._should_analyze_batch(batch):
                return

            self._analyze_batch(batch)
            self._remove_batch(batch)

    def _remove_batch(self, batch):
        for url, response_id, filename in batch:
            self._remove_file(filename)

    def _should_analyze_batch(self, batch):
        return len(batch) == self.BATCH_SIZE

    def _add_response_to_batch(self, response):
        """
        Save the HTTP response body to a file and save (url, filename) to the
        batch.

        :param response: HTTP response body
        :return: A copy of the batch
        """
        response_filename = self._save_response_to_file(response)
        data = (response.get_uri(), response.get_id(), response_filename)
        self._batch.append(data)
        return self._batch[:]

    def _analyze_batch(self, batch):
        """
        1. Run retirejs on all the files in the batch
        2. Parse the JSON file and associate files with URLs

        :param batch: The batch to run on
        :return: None, any vulnerabilities are saved to the KB.
        """
        json_doc = self._run_retire_on_batch(batch)
        self._json_to_kb(batch, json_doc)

    def end(self):
        """
        There might be some pending tasks to analyze in the batch, analyze
        them and then clear the batch.

        :return: None
        """
        self._analyze_batch(self._batch)
        self._remove_batch(self._batch)
        self._batch = []

    def _download_retire_db(self):
        """
        Downloads RETIRE_DB_URL, saves it to the w3af temp directory and
        saves the full path to the DB in self._retire_db_filename

        :return: None
        """
        # Only download once (even when threads are used)
        with self._plugin_lock:

            if self._retire_db_filename is not None:
                return

            # w3af grep plugins shouldn't (by definition) perform HTTP requests
            # But in this case we're breaking that general rule to retrieve the
            # DB at the beginning of the scan
            try:
                http_response = self._uri_opener.GET(self._retire_db_url,
                                                     binary_response=True,
                                                     respect_size_limit=False)
            except Exception, e:
                msg = 'Failed to download the retirejs database: "%s"'
                om.out.error(msg % e)
                return

            if http_response.get_code() != 200:
                msg = ('Failed to download the retirejs database, unexpected'
                       ' HTTP response code %s')
                om.out.error(msg % http_response.get_code())
                return

            om.out.debug('Successfully downloaded the latest retirejs DB')

            db = tempfile.NamedTemporaryFile(dir=get_temp_dir(),
                                             prefix='retirejs-db-',
                                             suffix='.json',
                                             delete=False,
                                             mode='wb')

            json_db = http_response.get_raw_body()
            db.write(json_db)
            db.close()

            self._retire_db_filename = db.name

    def _retirejs_is_installed(self):
        """
        Runs retirejs on an empty file to check that the return code is 0, this
        is just a safety check to make sure everything is working. It is only
        run once.

        :return: True if everything works
        """
        with self._plugin_lock:
            if self._should_run_retirejs_install_check:
                # Only run once
                self._should_run_retirejs_install_check = False

                self._is_valid_retire_version = self._get_is_valid_retire_version()
                self._is_valid_retirejs_exit_code = self._retire_smoke_test()

        return self._is_valid_retire_version and self._is_valid_retirejs_exit_code

    def _get_is_valid_retire_version(self):
        cmd = shlex.split(self.RETIRE_CMD_VERSION)

        retire_version_fd = tempfile.NamedTemporaryFile(prefix='retirejs-version-',
                                                        suffix='.out',
                                                        delete=False,
                                                        mode='w')

        try:
            subprocess.check_call(cmd,
                                  stderr=subprocess.DEVNULL,
                                  stdout=retire_version_fd)
        except subprocess.CalledProcessError:
            msg = 'Unexpected retire.js exit code. Disabling grep.retirejs plugin.'
            om.out.error(msg)
            return False

        retire_version_fd.close()
        current_retire_version = open(retire_version_fd.name).read()
        self._remove_file(retire_version_fd.name)

        if current_retire_version.startswith(self.RETIRE_VERSION):
            om.out.debug('Using a supported retirejs version')
            return True

        om.out.error('Please install a supported retirejs version (2.x)')
        return False

    def _retire_smoke_test(self):
        check_file = tempfile.NamedTemporaryFile(prefix='retirejs-check-',
                                                 suffix='.js',
                                                 delete=False,
                                                 dir=get_temp_dir())
        check_file.write('')
        check_file.close()

        output_file = tempfile.NamedTemporaryFile(prefix='retirejs-output-',
                                                  suffix='.json',
                                                  delete=False,
                                                  dir=get_temp_dir())
        output_file.close()

        args = (output_file.name, check_file.name)
        cmd = self.RETIRE_CMD % args

        process = subprocess.Popen(shlex.split(cmd),
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)

        process.wait()

        self._remove_file(output_file.name)
        self._remove_file(check_file.name)

        if process.returncode != 0:
            msg = 'Unexpected retire.js exit code. Disabling grep.retirejs plugin.'
            om.out.error(msg)
            return False

        else:
            om.out.debug('retire.js returned the expected exit code.')
            return True

    def _should_analyze(self, response):
        """
        :param response: HTTP response
        :return: True if we should analyze this HTTP response
        """
        #
        # Avoid running this plugin twice on the same URL
        #
        url_hash = hashlib.md5(response.get_url().url_string).hexdigest()
        if url_hash in self._analyzed_hashes:
            return False

        self._analyzed_hashes.add(url_hash)

        #
        # Avoid running this plugin twice on the same file content
        #
        body = smart_str_ignore(response.get_body())
        response_hash = hashlib.md5(body).hexdigest()

        if response_hash in self._analyzed_hashes:
            return False

        self._analyzed_hashes.add(response_hash)
        return True

    def _get_js_temp_directory(self):
        if self._js_temp_directory is None:
            self._js_temp_directory = tempfile.mkdtemp(dir=get_temp_dir())

        return self._js_temp_directory

    def _save_response_to_file(self, response):
        # Note: The file needs to have .js extension to force retirejs to
        #       scan it. Any other extension will be ignored.
        response_file = tempfile.NamedTemporaryFile(prefix='retirejs-response-',
                                                    suffix='.w3af.js',
                                                    delete=False,
                                                    dir=self._get_js_temp_directory())

        body = smart_str_ignore(response.get_body())
        response_file.write(body)
        response_file.close()

        return response_file.name

    def _run_retire_on_batch(self, batch):
        """
        Analyze a set of files and return the result as JSON

        :param batch: The batch of file to analyze (url, filename)
        :return: JSON document
        """
        json_file = tempfile.NamedTemporaryFile(prefix='retirejs-output-',
                                                suffix='.json',
                                                delete=False,
                                                dir=get_temp_dir())
        json_file.close()

        args = (json_file.name,
                self._retire_db_filename,
                self._get_js_temp_directory())
        cmd = self.RETIRE_CMD_JSREPO % args

        try:
            returncode = subprocess.call(shlex.split(cmd),
                                         stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL,
                                         timeout=self.RETIRE_TIMEOUT)
        except subprocess.TimeoutExpired:
            # The process timed out and the returncode was never set
            om.out.debug('The retirejs process for batch %s timeout out' % batch)
            return dict()

        # retirejs will return code != 0 when a vulnerability is found
        # we use this to decide when we need to parse the output
        if returncode == 0:
            self._remove_file(json_file.name)
            return dict()

        try:
            file_contents = file(json_file.name).read()
        except Exception:
            msg = 'Failed to read retirejs output file at %s'
            om.out.debug(msg % json_file.name)

            self._remove_file(json_file.name)
            return dict()

        try:
            json_doc = json.loads(file_contents)
        except Exception, e:
            msg = ('Failed to parse retirejs output as JSON.'
                   ' Exception is "%s" and file content: "%s..."')
            args = (e, file_contents[:20])
            om.out.debug(msg % args)

            self._remove_file(json_file.name)
            return dict()
        else:
            self._remove_file(json_file.name)
            return json_doc

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

    def _json_to_kb(self, batch, json_doc):
        """
        Write the findings which are in JSON retirejs format to the KB.

        :param batch: Batch of (url, filename) that was analyzed and generated
                      the JSON document passed in json_doc
        :param json_doc: The whole JSON document as returned by retirejs
        :return: None, everything is written to the KB.
        """
        data = json_doc.get('data', [])

        for json_finding in data:
            self._handle_finding(batch, json_finding)

    def _handle_finding(self, batch, json_finding):
        """
        Write a finding to the KB.

        :param batch: Batch of (url, filename) that was analyzed and generated
                      the JSON document passed in json_doc
        :param json_finding: A finding from retirejs JSON document
        :return: None, everything is written to the KB.
        """
        results = json_finding.get('results', [])

        # Find the URL that triggered this vulnerability
        finding_file = json_finding.get('file')
        url = None
        response_id = None

        for url, response_id, batch_filename in batch:
            if batch_filename == finding_file:
                break

        if url is None:
            om.out.debug('Batch filename mismatch in retirejs.')
            return

        for json_result in results:
            self._handle_result(url, response_id, json_result)

    def _handle_result(self, url, response_id, json_result):
        """
        Write a result to the KB.

        :param url: The URL associated with this result
        :param json_result: A finding from retirejs JSON document
        :return: None, everything is written to the KB.
        """
        version = json_result.get('version', None)
        component = json_result.get('component', None)
        vulnerabilities = json_result.get('vulnerabilities', [])

        if version is None or component is None:
            om.out.debug('The retirejs generated JSON document is invalid.'
                         ' Either the version or the component attribute is'
                         ' missing. Will ignore this result and continue with'
                         ' the next.')
            return

        if not vulnerabilities:
            om.out.debug('The retirejs generated JSON document is invalid. No'
                         ' vulnerabilities were found. Will ignore this result'
                         ' and continue with the next.')
            return

        message = VulnerabilityMessage(url, component, version)

        for vulnerability in vulnerabilities:
            vuln_severity = vulnerability.get('severity', 'unknown')
            summary = vulnerability.get('identifiers', {}).get('summary', 'unknown')
            info_urls = vulnerability.get('info', [])

            retire_vuln = RetireJSVulnerability(vuln_severity, summary, info_urls)
            message.add_vulnerability(retire_vuln)

        desc = message.to_string()
        real_severity = message.get_severity()

        v = Vuln('Vulnerable JavaScript library in use',
                 desc,
                 real_severity,
                 response_id,
                 self.get_name())

        v.set_uri(url)

        self.kb_append_uniq(self, 'js', v, filter_by='URL')

    def _get_retirejs_path(self):
        """
        :return: Path to the retirejs binary
        """
        paths_to_retire = which('retire')

        # The dependency check script guarantees that there will always be
        # at least one installation of the retirejs command.
        return paths_to_retire[0]

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'URL to download the retirejs database from'
        o = opt_factory('retire_db_url', self._retire_db_url, d, URL_OPTION)
        ol.add(o)

        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._retire_db_url = options_list['retire_db_url'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        Uses retirejs [0] to identify vulnerable javascript libraries in HTTP
        responses.
        
        [0] https://github.com/retirejs/retire.js/
        """


class VulnerabilityMessage(object):
    def __init__(self, url, component, version):
        self.url = url
        self.component = component
        self.version = version
        self.vulnerabilities = []

    def add_vulnerability(self, vulnerability):
        self.vulnerabilities.append(vulnerability)

    def get_severity(self):
        """
        The severity which is shown by retirejs is, IMHO, too high. For example
        a reDoS vulnerability in a JavaScript library is sometimes tagged as
        high.

        We reduce the vulnerability associated with the vulnerabilities a
        little bit here, to match what we find in other plugins.

        :return: severity.MEDIUM if there is at least one high in
                 self.vulnerabilities, otherwise just return severity.LOW
        """
        for vulnerability in self.vulnerabilities:
            if vulnerability.severity.lower() == 'high':
                return severity.MEDIUM

        return severity.LOW

    def to_string(self):
        message = ('A JavaScript library with known vulnerabilities was'
                   ' identified at %(url)s. The library was identified as'
                   ' "%(component)s" version %(version)s and has these known'
                   ' vulnerabilities:\n'
                   '\n'
                   '%(summaries)s\n'
                   '\n'
                   'Consider updating to the latest stable release of the'
                   ' affected library.')

        summaries = '\n'.join(' - %s' % vuln.summary for vuln in self.vulnerabilities)

        args = {'url': self.url,
                'component': self.component,
                'version': self.version,
                'summaries': summaries}

        return message % args


class RetireJSVulnerability(object):
    def __init__(self, vuln_severity, summary, info_urls):
        self.severity = vuln_severity
        self.summary = summary
        self.info_urls = info_urls
