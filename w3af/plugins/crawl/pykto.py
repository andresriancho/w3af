"""
pykto.py

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
import re
import codecs
import os.path
import itertools

from collections import namedtuple

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity

from w3af import ROOT_PATH
from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import INPUT_FILE, BOOL, LIST
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.request.fuzzable_request import FuzzableRequest


class pykto(CrawlPlugin):
    """
    A nikto port to python.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):
        CrawlPlugin.__init__(self)

        # internal variables
        self._exec = True
        self._already_analyzed = ScalableBloomFilter()

        # User configured parameters
        self._db_file = os.path.join(ROOT_PATH, 'plugins', 'crawl', 'pykto',
                                     'scan_database.db')
        self._extra_db_file = os.path.join(ROOT_PATH, 'plugins', 'crawl',
                                           'pykto', 'w3af_scan_database.db')

        self._cgi_dirs = ['/cgi-bin/']
        self._admin_dirs = ['/admin/', '/adm/']

        self._users = ['adm', 'bin', 'daemon', 'ftp', 'guest', 'listen', 'lp',
                       'mysql', 'noaccess', 'nobody', 'nobody4', 'nuucp',
                       'operator', 'root', 'smmsp', 'smtp', 'sshd', 'sys',
                       'test', 'unknown']

        self._nuke = ['/', '/postnuke/', '/postnuke/html/', '/modules/',
                      '/phpBB/', '/forum/']

        self._mutate_tests = False

    def crawl(self, fuzzable_request, debugging_id):
        """
        Runs pykto to the site.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                 (among other things) the URL to test.
        """
        if not self._exec and not self._mutate_tests:
            # dont run anymore
            raise RunOnce()

        else:
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
                    # Save the directories I already have tested in order to
                    # avoid testing them more than once...
                    self._already_analyzed.add(url)
                    self._run(url)

    def _run(self, url):
        """
        Really run the plugin.

        :param url: The URL object I have to test.
        """
        config = Config(self._cgi_dirs, self._admin_dirs, self._nuke,
                        self._mutate_tests, self._users)
                
        for db_file in [self._db_file, self._extra_db_file]:
            
            parser = NiktoTestParser(db_file, config, url)
            
            # Send the requests using threads:
            self.worker_pool.map_multi_args(self._send_and_check,
                                            parser.test_generator(),
                                            chunksize=10)

    def _send_and_check(self, nikto_test):
        """
        This method sends the request to the server.

        :return: True if the requested URI responded as expected.
        """
        #
        #    Small performance improvement. If all we want to know is if the
        #    file exists or not, lets use HEAD instead of GET. In 99% of the
        #    cases this will work as expected and we'll have a significant
        #    performance improvement.
        #
        if nikto_test.is_vulnerable.checks_only_response_code():
            try:
                http_response = self._uri_opener.HEAD(nikto_test.uri)
            except Exception:
                return
            else:
                if not nikto_test.is_vulnerable.check(http_response):
                    return False

        function_ptr = getattr(self._uri_opener, nikto_test.method)

        try:
            http_response = function_ptr(nikto_test.uri)
        except BaseFrameworkException, e:
            msg = ('An exception was raised while requesting "%s", the error'
                   ' message is: "%s".')
            om.out.error(msg % (nikto_test.uri, e))
            return False

        if nikto_test.is_vulnerable.check(http_response) and \
        not is_404(http_response):
            
            vdesc = ('pykto plugin found a vulnerability at URL: "%s".'
                     ' Vulnerability description: "%s".')
            vdesc = vdesc % (http_response.get_url(), nikto_test.message)

            v = Vuln('Insecure URL', vdesc, severity.LOW,
                     http_response.id, self.get_name())
            v.set_uri(http_response.get_uri())
            v.set_method(nikto_test.method)

            kb.kb.append(self, 'vuln', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())

            fr = FuzzableRequest.from_http_response(http_response)
            self.output_queue.put(fr)

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'CGI-BIN dirs where to search for vulnerable scripts.'
        h = ('Pykto will search for vulnerable scripts in many places, one of'
             ' them is inside cgi-bin directory. The cgi-bin directory can be'
             ' anything and change from install to install, so its a good idea'
             ' to make this a user setting. The directories should be supplied'
             ' comma separated and with a / at the beginning and one at the end.'
             ' Example: "/cgi/,/cgibin/,/bin/"')
        o = opt_factory('cgi_dirs', self._cgi_dirs, d, LIST, help=h)
        ol.add(o)

        d = 'Admin directories where to search for vulnerable scripts.'
        h = ('Pykto will search for vulnerable scripts in many places, one of'
             ' them is inside administration directories. The admin directory'
             ' can be anything and change from install to install, so its a'
             ' good idea to make this a user setting. The directories should'
             ' be supplied comma separated and with a / at the beginning and'
             ' one at the end. Example: "/admin/,/adm/"')
        o = opt_factory('admin_dirs', self._admin_dirs, d, LIST, help=h)
        ol.add(o)

        d = 'PostNuke directories where to search for vulnerable scripts.'
        h = ('The directories should be supplied comma separated and with a'
             ' forward slash at the beginning and one at the end. Example:'
             ' "/forum/,/nuke/"')
        o = opt_factory('nuke_dirs', self._nuke, d, LIST, help=h)
        ol.add(o)

        d = 'The path to the nikto scan_databse.db file.'
        h = 'The default scan database file is fine in most cases.'
        o = opt_factory('db_file', self._db_file, d, INPUT_FILE, help=h)
        ol.add(o)

        d = 'The path to the w3af_scan_database.db file.'
        h = ('This is a file which has some extra checks for files that are not'
             ' present in the nikto database.')
        o = opt_factory('extra_db_file', self._extra_db_file, d,
                        INPUT_FILE, help=h)
        ol.add(o)

        d = 'Test all files with all root directories'
        h = 'Define if we will test all files with all root directories.'
        o = opt_factory('mutate_tests', self._mutate_tests, d, BOOL, help=h)
        ol.add(o)

        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._cgi_dirs = options_list['cgi_dirs'].get_value()
        self._admin_dirs = options_list['admin_dirs'].get_value()
        self._nuke = options_list['nuke_dirs'].get_value()
        self._extra_db_file = options_list['extra_db_file'].get_value()
        self._db_file = options_list['db_file'].get_value()
        self._mutate_tests = options_list['mutate_tests'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin is a nikto port to python. It uses the scan_database file
        from nikto to search for new and vulnerable URLs.

        The following configurable parameters exist:
            - db_file
            - extra_db_file
            - cgi_dirs
            - admin_dirs
            - nuke_dirs
            - mutate_tests

        This plugin reads every line in the scan_database (and extra_db_file)
        and based on the configuration ("cgi_dirs", "admin_dirs" , "nuke_dirs")
        it performs requests to the remote server searching for common files
        that may contain vulnerabilities.
        """

Config = namedtuple('Config', ['cgi_dirs', 'admin_dirs', 'nuke_dirs',
                               'mutate_tests', 'users'])

NiktoTest = namedtuple('NiktoTest', ['id', 'osvdb', 'tune', 'uri', 'method',
                                     'match_1', 'match_1_or', 'match_1_and',
                                     'fail_1', 'fail_2', 'message', 'data',
                                     'headers', 'is_vulnerable'])


class IsVulnerableHelper(object):
    def __init__(self, match_1, match_1_or, match_1_and, fail_1, fail_2):
        self.match_1 = match_1
        self.match_1_or = match_1_or
        self.match_1_and = match_1_and
        self.fail_1 = fail_1
        self.fail_2 = fail_2
    
    def checks_only_response_code(self):
        return isinstance(self.match_1, int) and \
               (isinstance(self.match_1_or, int) or self.match_1_or is None) and \
               (isinstance(self.match_1_and, int) or self.match_1_and is None) and \
               (isinstance(self.fail_1, int) or self.fail_1 is None) and\
               (isinstance(self.fail_2, int) or self.fail_2 is None)
    
    def _matches(self, what, http_response, if_none=False):
        if what is None:
            return if_none
        
        if isinstance(what, int):
            if http_response.get_code() == what: 
                return True
        elif what.search(http_response.body):
            return True
        
        return False
    
    def check(self, http_response):
        """
        :return: True if the http_response is vulnerable to whatever we're
                 checking with self.match_1 ... self.fail_2
        """
        is_vuln = self._matches(self.match_1, http_response) or \
                  self._matches(self.match_1_or, http_response)
        
        # reduce known false positives
        if is_vuln:
            
            if not self._matches(self.match_1_and, http_response, if_none=True):
                is_vuln = False
            
            if self._matches(self.fail_1, http_response) or \
            self._matches(self.fail_2, http_response):
                is_vuln = False
        
        return is_vuln
    
    def __eq__(self, other):
        return True
            

class NiktoTestParser(object):
    """
    A parser for the nikto tests file.
    """
    def __init__(self, filename, config, url):
        self.filename = filename
        self.config = config
        self.url = url
        
        self._kb_server = None
        self._junk_re = re.compile('JUNK\((.*?)\)')
        self.ignored = []
    
    def test_generator(self):
        """
        A helper function that takes a scan database file and yields tests.

        :return: (A modified url_object with the special query from the
                  scan_database,
                  The parsed parameters from the scan database line)
        """
        try:
            db_file = codecs.open(self.filename, "r", "utf-8" )
        except Exception, e:
            msg = 'Failed to open the scan database. Exception: "%s".'
            om.out.error(msg % e)
            raise StopIteration
        
        for line in db_file:
            
            if self._is_comment(line):
                continue

            # This is a sample scan_database.db line :
            # "apache","/docs/","200","GET","May give list of installed software"
            #
            # A line could generate more than one request...
            # (think about @CGIDIRS)
            for nikto_test in itertools.ifilter(self._filter_special,
                                                self._parse_db_line(line)):
                yield (nikto_test,)
                
    def _filter_special(self, nikto_test):
        if not nikto_test.uri:
            return False
        
        return True

    def _is_comment(self, line):
        """
        The simplest method ever.

        :return: Returns if a line is a comment or not.
        """
        if line.startswith('"'):
            return False
        
        if line.startswith('#'):
            return True
        
        return True

    def _parse_db_line(self, line):
        """
        This method parses a line from the database file, lines look line this:
        
        "000001","0","b","/TiVoConnect?Command=QueryServer","GET",
        "Calypso Server","","","","","The Tivo Calypso server is running...",
        "",""        

        The information in each line contains the following information:
            0. 'id'
            1. 'osvdb'
            2. 'tune'
                   1     Interesting File / Seen in logs
                   2     Misconfiguration / Default File
                   3     Information Disclosure
                   4     Injection (XSS/Script/HTML)
                   5     Remote File Retrieval - Inside Web Root
                   6     Denial of Service
                   7     Remote File Retrieval - Server Wide
                   8     Command Execution / Remote Shell
                   9     SQL Injection
                   0     File Upload
                   a     Authentication Bypass
                   b     Software Identification
                   c     Remote Source Inclusion
            3. 'uri'
            4. 'method'
            5. 'match_1'
            6. 'match_1_or'
            7. 'match_1_and'
            8. 'fail_1'
            9. 'fail_2'
            10. 'message'
            11. 'data'
            12. 'headers'
        
        :param line: A unicode string     
        :return: Yield NiktoTests which contain the information above and has
                 the final URI with all @VARS replaced.
                 
                 The NiktoTest object also contains a helper function which
                 takes an http_response as parameter and returns True if the
                 response matched (match_1, match_1_or, match_1_and, fail_1,
                 fail_2).
        """
        if not isinstance(line, unicode):
            raise TypeError('Database information needs to be sent as unicode.')
        
        line = line.strip()
        splitted_line = line.split('","')

        if len(splitted_line) != 13:
            self.ignored.append(line)
            raise StopIteration

        # Remove those ugly double quotes which I get after splitting by '","'
        splitted_line[0] = splitted_line[0][1:]
        splitted_line[12] = splitted_line[12][:-1]

        # Compile the regular expressions for these variables:
        #    match_1 = splitted_line[5]
        #    match_1_or = splitted_line[6]
        #    match_1_and = splitted_line[7]
        #    fail_1 = splitted_line[8]
        #    fail_2 = splitted_line[9]
        #
        # If and only if they aren't response codes
        for test_index in xrange(5,10):
            test_value = splitted_line[test_index]
            
            if len(test_value) == 3 and test_value.isdigit():
                splitted_line[test_index] = int(test_value)

            elif test_value:
                flags = re.I | re.M | re.S
                try:
                    splitted_line[test_index] = re.compile(test_value, flags)
                except:
                    # Protect myself against buggy regular expressions
                    raise StopIteration
            
            else:
                splitted_line[test_index] = None

        _id = splitted_line[0]
        osvdb = splitted_line[1]
        tune = splitted_line[2]
        uri = splitted_line[3]
        method = splitted_line[4]
        match_1 = splitted_line[5]
        match_1_or = splitted_line[6]
        match_1_and = splitted_line[7]
        fail_1 = splitted_line[8]
        fail_2 = splitted_line[9]
        message = splitted_line[10]
        data = splitted_line[11]
        headers = splitted_line[12]

        message = message.replace('\n', '')
        message = message.replace('\r', '')
        message = message.strip()

        if uri.count(' '):
            self.ignored.append(line)
            raise StopIteration

        # Now I should replace the @CGIDIRS variable with the user settings
        # The same goes for every @* variable.
        VAR_LIST = (
            ('@CGIDIRS', self.config.cgi_dirs),
            ('@ADMIN', self.config.admin_dirs),
            ('@NUKE', self.config.nuke_dirs),
            ('@USERS', self.config.users),
            ('@RFIURL', ['http://cirt.net/rfiinc.txt']),
        )

        v_list_replace = [v_list for var, v_list in VAR_LIST if var in uri]
        variable_replace = [var for var, v_list in VAR_LIST if var in uri]

        for prod_result in apply(itertools.product, v_list_replace):

            current_uri = self._replace_JUNK(uri)

            for i, v_list_item in enumerate(prod_result):
                current_uri = current_uri.replace(variable_replace[i],
                                                  v_list_item)

            # I don't use url_join here because in some cases pykto needs to
            # send something like http://abc/../../../../etc/passwd
            # and after url_join the URL would be just http://abc/etc/passwd
            #
            # But I do want is to avoid URLs like this one being generated:
            # http://localhost//f00   <---- Note the double //
            if current_uri.startswith('/') and self.url.get_path().endswith('/'):
                current_uri = current_uri[1:]

            modified_url_str = self.url.uri2url().url_string
            modified_url_str += current_uri
            modified_url = URL(modified_url_str)

            is_vuln_helper = IsVulnerableHelper(match_1, match_1_or, match_1_and,
                                                fail_1, fail_2,)

            yield NiktoTest(_id, osvdb, tune, modified_url, method, match_1,
                            match_1_or, match_1_and, fail_1, fail_2, message,
                            data, headers, is_vuln_helper)

    def _replace_JUNK(self, query):
        """
        Replace the JUNK(x) variable with random alphanum.
        """
        match_obj = self._junk_re.search(query)
        
        if match_obj is not None:
            if match_obj.group(1).isdigit():
                
                length = int(match_obj.group(1))
                query = self._junk_re.sub(rand_alnum(length), query)
                
        return query