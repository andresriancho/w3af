'''
pykto.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''
import itertools
import os.path
import re

import core.controllers.output_manager as om
import core.data.kb.knowledge_base as kb
import core.data.constants.severity as severity

from core.controllers.plugins.crawl_plugin import CrawlPlugin
from core.controllers.exceptions import w3afException
from core.controllers.exceptions import w3afRunOnce
from core.controllers.core_helpers.fingerprint_404 import is_404

from core.data.fuzzer.utils import rand_alnum
from core.data.options.opt_factory import opt_factory
from core.data.options.option_types import INPUT_FILE, BOOL, LIST
from core.data.options.option_list import OptionList
from core.data.parsers.url import URL
from core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from core.data.kb.vuln import Vuln


class pykto(CrawlPlugin):
    '''
    A nikto port to python.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        CrawlPlugin.__init__(self)

        # internal variables
        self._exec = True
        self._already_analyzed = ScalableBloomFilter()
        self._show_remote_server = True

        # User configured parameters
        self._db_file = os.path.join(
            'plugins', 'crawl', 'pykto', 'scan_database.db')

        self._extra_db_file = os.path.join('plugins', 'crawl', 'pykto',
                                           'w3af_scan_database.db')

        self._cgi_dirs = ['/cgi-bin/']
        self._admin_dirs = ['/admin/', '/adm/']

        self._users = ['adm', 'bin', 'daemon', 'ftp', 'guest', 'listen', 'lp',
                       'mysql', 'noaccess', 'nobody', 'nobody4', 'nuucp', 'operator',
                       'root', 'smmsp', 'smtp', 'sshd', 'sys', 'test', 'unknown']

        self._nuke = ['/', '/postnuke/', '/postnuke/html/', '/modules/', '/phpBB/',
                      '/forum/']

        self._mutate_tests = False
        self._generic_scan = False
        self._update_scandb = False
        self._source = ''

    def crawl(self, fuzzable_request):
        '''
        Runs pykto to the site.

        @param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        '''
        if not self._exec and not self._mutate_tests:
            # dont run anymore
            raise w3afRunOnce()

        else:
            # run!
            if self._update_scandb:
                self._update_db()

            # Run the basic scan (only once)
            url = fuzzable_request.get_url().base_url()
            if url not in self._already_analyzed:
                self._already_analyzed.add(url)
                self._run(url)
                self._exec = False

            # And now mutate if the user configured it...
            if self._mutate_tests:

                # Tests need to be mutated
                url = fuzzable_request.get_url().get_domain_path()
                if url not in self._already_analyzed:
                    # Save the directories I already have tested in order to avoid
                    # testing them more than once...
                    self._already_analyzed.add(url)
                    self._run(url)

    def _run(self, url):
        '''
        Really run the plugin.

        @param url: The URL object I have to test.
        '''
        for fname in [self._db_file, self._extra_db_file]:
            try:
                db_file = open(fname, "r")
            except Exception, e:
                msg = 'Failed to open the scan database. Exception: "%s".'
                raise om.out.error(msg % e)
            else:

                test_generator = self._test_generator_method(db_file, url)

                # Send the requests using threads:
                self.worker_pool.map_multi_args(
                    self._send_and_check, test_generator,
                    chunksize=10)

    def _test_generator_method(self, scan_database_file, url):
        '''
        A helper function that takes a scan database file and yields tests.

        @param scan_database_file: The file object for a scan database
        @param url: The URL object (with the path) that I'm testing

        @return: (
            A modified url_object with the special query from the scan_database,
                   The parsed parameters from the scan database line)
        '''
        for line in scan_database_file:
            #om.out.debug( 'Read scan_database: '+ line[:len(line)-1] )
            if self._is_comment(line):
                continue

            # This is a sample scan_database.db line :
            # "apache","/docs/","200","GET","May give list of installed software"
            #
            # A line could generate more than one request...
            # (think about @CGIDIRS)
            for parameters in itertools.ifilter(self._filter_special,
                                                self._parse_db_line(line)):

                _, query, _, _, _ = parameters

                om.out.debug('Testing pykto signature: "%s".' % query)

                # I don't use url_join here because in some cases pykto needs to
                # send something like http://abc/../../../../etc/passwd
                # and after url_join the URL would be just http://abc/etc/passwd
                #
                # But I do want is to avoid URLs like this one being generated:
                # http://localhost//f00   <---- Note the double //
                if len(query) != 0 and len(url.get_path()) != 0:
                    if query[0] == '/' == url.get_path()[-1]:
                        query = query[1:]

                modified_url = url.copy()
                modified_url.set_path(modified_url.get_path() + query)

                yield modified_url, parameters

    def _filter_special(self, parameters):
        server, query, _, _, _ = parameters

        # Avoid directory self references
        if query.endswith('/./') or query.endswith('/%2e/'):
            return False

        if self._generic_scan or self._server_match(server):
            return True

        return False

    def _update_db(self):
        '''
        This method updates the scan_database from cirt.net .
        '''
        # Only update once
        self._update_scandb = False

        # Here we have the versions
        _version_file = 'plugins' + os.path.sep + 'crawl' + \
            os.path.sep + 'pykto'
        _version_file += os.path.sep + 'versions.txt'

        try:
            version_file = file(_version_file)
        except Exception, e:
            msg = 'Could not open: "' + _version_file + \
                '" while updating pykto scan_database.'
            msg += ' Exception message: "' + str(e) + '".'
            raise w3afException(msg)

        try:
            for line in version_file:
                if line.count('scan_database.db'):
                    _, local_version = line.strip().split(',')
                    break
        except:
            msg = 'Format error in file: ' + _version_file + \
                ' while updating pykto scan_database.'
            raise w3afException(msg)

        version_file.close()
        om.out.debug(
            'Local version of pykto scan_database.db is: ' + local_version)

        # fetching remote version
        versions_url = URL(
            'http://www.cirt.net/nikto/UPDATES/1.36/versions.txt')
        res_version = self._uri_opener.GET(versions_url)

        fetched_version = False
        for line in res_version.get_body().split():
            if line.count('scan_database.db'):
                _, remote_version = line.strip().split(',')
                fetched_version = True

        if not fetched_version:
            msg = 'pykto can\'t update the scan database, an error occurred while fetching the'
            msg += ' versions.txt file from cirt.net .'
            om.out.error(msg)
        else:
            om.out.debug('Remote version of nikto scan_database.db is: "' +
                         remote_version + '".')

            local_version = float(local_version)
            remote_version = float(remote_version)

            if local_version == remote_version:
                msg = 'Local and Remote version of nikto scan_database.db match, no update needed.'
                om.out.information(msg)
            elif local_version > remote_version:
                msg = 'Local version of scan_database.db is grater than remote version... this is'
                msg += ' odd... check this.'
                om.out.information(msg)
            else:
                msg = 'Updating to scan_database version: "' + \
                    str(remote_version) + '".'
                om.out.information(msg)
                scan_database_url = URL(
                    'http://www.cirt.net/nikto/UPDATES/1.36/scan_database.db')
                res = self._uri_opener.GET(scan_database_url)
                try:
                    # Write new scan_database
                    os.unlink(self._db_file)
                    fd_new_db = file(self._db_file, 'w')
                    fd_new_db.write(res.get_body())
                    fd_new_db.close()

                    # Write new version file
                    os.unlink(_version_file)
                    fd_new_version = file(_version_file, 'w')
                    fd_new_version.write(res_version.get_body())
                    fd_new_version.close()

                    msg = 'Successfully updated scan_database.db to version: ' + str(remote_version)
                    om.out.information(msg)

                except Exception, e:
                    msg = 'There was an error while writing the new scan_database.db file to disk.'
                    msg += ' Exception message: "' + str(e) + '".'
                    raise w3afException(msg)

    def _server_match(self, server):
        '''
        Reads the kb and compares the server parameter with the kb value.
        If they match true is returned.

        @param server: A server name like "apache"
        '''
        # Try to get the server type from hmap
        # it is the most accurate way to do it but hmap plugin
        if kb.kb.get('hmap', 'server_string') != []:
            kb_server = kb.kb.get('hmap', 'server_string')
            self._source = 'hmap'

        elif kb.kb.get('server_header', 'server_string') != []:
            # Get the server type from the server_header plugin. It gets this info
            # by reading the "server" header of request responses.
            kb_server = kb.kb.get('server_header', 'server_string')
            self._source = 'server_header'

        else:
            self._source = 'not available'
            kb_server = 'not available'

        if self._show_remote_server:
            msg = 'pykto plugin is using "' + kb_server + \
                '" as the remote server type.'
            msg += ' This information was obtained by ' + \
                self._source + ' plugin.'
            om.out.information(msg)
            self._show_remote_server = False

        if kb_server.upper().count(server.upper()) or server.upper() == 'GENERIC':
            return True
        else:
            return False

    def _is_comment(self, line):
        '''
        The simplest method ever.

        @return: Returns if a line is a comment or not.
        '''
        if line[0] == '"':
            return False
        return True

    def _parse_db_line(self, line):
        '''
        This method parses a line from the database file

        @return: Yield tuples where each tuple has the following data
            1. server
            2. query
            3. expected_response
            4. method
            5. desc
        '''
        splitted_line = line.split('","')

        server = splitted_line[0].replace('"', '')
        original_query = splitted_line[1].replace('"', '')
        expected_response = splitted_line[2].replace('"', '')
        method = splitted_line[3].replace('"', '').upper()
        desc = splitted_line[4].replace('"', '')
        desc = desc.replace('\\n', '')
        desc = desc.replace('\\r', '')

        if not original_query.count(' '):

            # Now I should replace the @CGIDIRS variable with the user settings
            # The same goes for every @* variable.
            VAR_LIST = (
                ('@CGIDIRS', self._cgi_dirs),
                ('@ADMINDIRS', self._admin_dirs),
                ('@NUKE', self._nuke),
                ('@USERS', self._users),
            )

            v_list_replace = [v_list for var, v_list in VAR_LIST
                              if var in original_query]

            variable_replace = [var for var, v_list in VAR_LIST
                                if var in original_query]

            for prod_result in apply(itertools.product, v_list_replace):

                query = self._replace_JUNK(original_query)

                for i, v_list_item in enumerate(prod_result):
                    query = query.replace(variable_replace[i], v_list_item)

                yield server, query, expected_response, method, desc

    def _replace_JUNK(self, query):
        # Replace the JUNK(x) variable:
        match_obj = re.findall('JUNK\((.*?)\)', query)
        if match_obj:
            query = re.sub('JUNK\((.*?)\)',
                           rand_alnum(int(match_obj[0])),
                           query)
        return query

    def _send_and_check(self, url, parameters):
        '''
        This method sends the request to the server.

        @return: True if the requested URI responded as expected.
        '''
        (server, query, expected_response, method, desc) = parameters

        #
        #    Small performance improvement. If all we want to know is if the
        #    file exists or not, lets use HEAD instead of GET. In 99% of the
        #    cases this will work as expected and we'll have a significant
        #    performance improvement.
        #
        if expected_response == '200' and method == 'GET':
            try:
                res = self._uri_opener.HEAD(url, follow_redir=False)
            except:
                pass
            else:
                if res.get_code() != int(expected_response):
                    #
                    #    If the response code is not 200, then there is nothing there.
                    #
                    return False

        #
        #    If we found a 200 with HEAD, or
        #    If the expected response was not 200, or
        #    If the request method is not GET, then
        #    perform the request, analyze the response, etc.
        #
        function_reference = getattr(self._uri_opener, method)

        try:
            response = function_reference(url, follow_redir=False)
        except w3afException, e:
            msg = 'An exception was raised while requesting "' + \
                url + '" , the error message is: '
            msg += str(e)
            om.out.error(msg)
            return False

        if self._analyze_result(response, expected_response, parameters, url):
            kb.kb.append(self, 'url', response.get_url())

            desc = 'pykto plugin found a vulnerability at URL: "%s".'\
                   ' Vulnerability description: "%s".'
            desc = desc % (response.get_url(), desc.strip())

            v = Vuln('Insecure resource', desc, severity.LOW,
                     response.id, self.get_name())
            v.set_uri(response.get_uri())
            v.set_method(method)

            kb.kb.append(self, 'vuln', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())

            fr_list = self._create_fuzzable_requests(response)
            [fr.get_uri().normalize_url() for fr in fr_list]
            for fr in fr_list:
                self.output_queue.put(fr)

    def _analyze_result(self, response, expected_response, parameters, uri):
        '''
        Analyzes the result of a _send()

        @return: True if vuln is found
        '''
        if expected_response.isdigit():
            int_er = int(expected_response)
            # This is used when expected_response is 200 , 401, 403, etc.
            if response.get_code() == int_er and not is_404(response):
                return True

        elif expected_response in response and not is_404(response):
            # If the content is found, and it's not in a 404 page, then we have a vuln.
            return True

        return False

    def get_options(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = OptionList()

        d = 'CGI-BIN dirs where to search for vulnerable scripts.'
        h = 'Pykto will search for vulnerable scripts in many places, one of them is inside'
        h += ' cgi-bin directory. The cgi-bin directory can be anything and change from install'
        h += ' to install, so its a good idea to make this a user setting. The directories should'
        h += ' be supplied comma separated and with a / at the beggining and one at the end.'
        h += ' Example: "/cgi/,/cgibin/,/bin/"'
        o = opt_factory('cgiDirs', self._cgi_dirs, d, LIST, help=h)
        ol.add(o)

        d = 'Admin directories where to search for vulnerable scripts.'
        h = 'Pykto will search for vulnerable scripts in many places, one of them is inside'
        h += ' administration directories. The admin directory can be anything and change'
        h += ' from install to install, so its a good idea to make this a user setting. The'
        h += ' directories should be supplied comma separated and with a / at the beggining and'
        h += ' one at the end. Example: "/admin/,/adm/"'
        o = opt_factory('adminDirs', self._admin_dirs, d, LIST, help=h)
        ol.add(o)

        d = 'PostNuke directories where to search for vulnerable scripts.'
        h = 'The directories should be supplied comma separated and with a / at the'
        h += ' beggining and one at the end. Example: "/forum/,/nuke/"'
        o = opt_factory('nukeDirs', self._nuke, d, LIST, help=h)
        ol.add(o)

        d = 'The path to the nikto scan_databse.db file.'
        h = 'The default scan database file is ok in most cases.'
        o = opt_factory('dbFile', self._db_file, d, INPUT_FILE, help=h)
        ol.add(o)

        d = 'The path to the w3af_scan_databse.db file.'
        h = 'This is a file which has some extra checks for files that are not present in the'
        h += ' nikto database.'
        o = opt_factory(
            'extra_db_file', self._extra_db_file, d, INPUT_FILE, help=h)
        ol.add(o)

        d = 'Test all files with all root directories'
        h = 'Define if we will test all files with all root directories.'
        o = opt_factory('mutateTests', self._mutate_tests, d, BOOL, help=h)
        ol.add(o)

        d = 'Verify that pykto is using the latest scan_database from cirt.net.'
        o = opt_factory('updateScandb', self._update_scandb, d, BOOL)
        ol.add(o)

        d = 'If generic scan is enabled all tests are sent to the remote server without'
        d += ' checking the server type.'
        h = 'Pykto will send all tests to the server if generic Scan is enabled. For example,'
        h += ' if a test in the database is marked as "apache" and the remote server reported'
        h += ' "iis" then the test is sent anyway.'
        o = opt_factory('genericScan', self._generic_scan, d, BOOL, help=h)
        ol.add(o)

        return ol

    def set_options(self, options_list):
        '''
        This method sets all the options that are configured using the user int_erface
        generated by the framework using the result of get_options().

        @param OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        '''
        self._update_scandb = options_list['updateScandb'].get_value()
        self._cgi_dirs = options_list['cgiDirs'].get_value()
        self._admin_dirs = options_list['adminDirs'].get_value()
        self._nuke = options_list['nukeDirs'].get_value()
        self._extra_db_file = options_list['extra_db_file'].get_value()
        self._db_file = options_list['dbFile'].get_value()
        self._mutate_tests = options_list['mutateTests'].get_value()
        self._generic_scan = options_list['genericScan'].get_value()

    def get_plugin_deps(self):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return ['infrastructure.server_header']

    def get_long_desc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin is a nikto port to python. It uses the scan_database file
        from nikto to search for new and vulnerable URL's.

        Seven configurable parameters exist:
            - updateScandb
            - cgiDirs
            - adminDirs
            - nukeDirs
            - dbFile
            - extra_db_file
            - mutateTests
            - genericScan

        This plugin reads every line in the scan_database (and extra_db_file)
        and based on the configuration ("cgiDirs", "adminDirs" , "nukeDirs"
        and "genericScan") it performs requests to the remote server searching
        for common files that may contain vulnerabilities.
        '''
