"""
helper.py

Copyright 2012 Andres Riancho

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
from __future__ import print_function

import os
import re
import time
import pprint
import urllib2
import unittest
import tempfile
import httpretty

from functools import wraps
from nose.plugins.skip import SkipTest
from nose.plugins.attrib import attr

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.w3afCore import w3afCore
from w3af.core.controllers.misc.home_dir import W3AF_LOCAL_PATH
from w3af.core.controllers.misc.decorators import retry
from w3af.core.controllers.misc_settings import MiscSettings
from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import URL_LIST
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.kb.read_shell import ReadShell
from w3af.core.data.kb.info_set import InfoSet


os.chdir(W3AF_LOCAL_PATH)
RE_COMPILE_TYPE = type(re.compile(''))


@attr('moth')
class PluginTest(unittest.TestCase):
    """
    These tests can be configured using two environment variables:

        * HTTP_PROXY=127.0.0.1:8080 , route HTTP traffic through a local proxy
        * HTTPS_PROXY=127.0.0.1:8080 , route HTTPS traffic through a local proxy
        * DEBUG=1 , enable logging

    For example:

        HTTP_PROXY=127.0.0.1:8080 nosetests -s w3af/plugins/tests/infrastructure/test_allowed_methods.py

    Remember that nosetests can't find test generators in unittest.TestCase,
    http://stackoverflow.com/questions/6689537/nose-test-generators-inside-class
    """
    MOCK_RESPONSES = []
    runconfig = {}
    kb = kb.kb
    target_url = None
    base_path = None

    def setUp(self):
        self.kb.cleanup()
        self.w3afcore = w3afCore()
        self.misc_settings = MiscSettings()

        self.request_callback_call_count = 0
        self.request_callback_match = 0

        if self.MOCK_RESPONSES:
            httpretty.reset()
            httpretty.enable()
            
            try:
                url = URL(self.target_url)
            except ValueError, ve:
                msg = ('When using MOCK_RESPONSES you need to set the'
                       ' target_url attribute to a valid URL, exception was:'
                       ' "%s".')
                raise Exception(msg % ve)

            domain = url.get_domain()
            proto = url.get_protocol()
            port = url.get_port()

            self._register_httpretty_uri(proto, domain, port)

    def _register_httpretty_uri(self, proto, domain, port):
        assert isinstance(port, int), 'Port needs to be an integer'

        if (port == 80 and proto == 'http') or \
           (port == 443 and proto == 'https'):
            re_str = "%s://%s/(.*)" % (proto, domain)
        else:
            re_str = "%s://%s:%s/(.*)" % (proto, domain, port)

        all_methods = set(mock_resp.method for mock_resp in self.MOCK_RESPONSES)

        for http_method in all_methods:
            httpretty.register_uri(http_method,
                                   re.compile(re_str),
                                   body=self.__internal_request_callback)

    def tearDown(self):
        self.w3afcore.quit()
        self.kb.cleanup()
        self.assert_all_get_desc_work()

        if self.MOCK_RESPONSES:
            httpretty.disable()
            httpretty.reset()

    def assert_all_get_desc_work(self):
        """
        Since the InfoSet does some custom rendering at get_desc(), I want to
        make sure that any InfoSets render properly, some of my tests might not
        be calling it implicitly, so we call it here.
        """
        for info in self.kb.get_all_findings():
            if isinstance(info, InfoSet):
                info.get_desc()

    def assertAllVulnNamesEqual(self, vuln_name, vulns):
        if not vulns:
            self.assertTrue(False, 'No vulnerabilities found to match')

        for vuln in vulns:
            self.assertEqual(vuln.get_name(), vuln_name)

    def assertExpectedVulnsFound(self, expected, found_vulns):
        found_tokens = [(v.get_url().get_file_name(),
                         v.get_token_name()) for v in found_vulns]

        self.assertEquals(
            set(found_tokens),
            set(expected)
        )

    def tokenize_kb_vulns(self):
        all_info = self.kb.get_all_findings()
        info_tokens = set()

        for info in all_info:

            url = None if info.get_url() is None else info.get_url().get_path()
            token_name = None if info.get_token() is None else info.get_token_name()

            info_tokens.add((info.get_name(), url, token_name))

        return info_tokens

    def assertMostExpectedVulnsFound(self, expected, percentage=0.85):
        """
        Assert that at least :percentage: of the expected vulnerabilities were
        found during the current scan.
        """
        len_exp_found = len(expected.intersection(self.tokenize_kb_vulns()))
        found_perc = float(len_exp_found) / len(expected)
        self.assertGreater(found_perc, percentage)

    def assertAllExpectedVulnsFound(self, expected):
        self.assertEqual(expected, self.tokenize_kb_vulns())

    def assertAllURLsFound(self, expected):
        frs = self.kb.get_all_known_fuzzable_requests()

        found = []

        for fr in frs:
            uri = fr.get_uri()
            path = uri.get_path()
            qs = str(uri.get_querystring())

            if qs:
                data = path + '?' + qs
            else:
                data = path

            found.append(data)

        self.assertEquals(set(found),
                          set(expected))

    def __internal_request_callback(self, http_request, uri, headers):
        self.request_callback_call_count += 1
        match = None

        for mock_response in self.MOCK_RESPONSES:
            if mock_response.matches(http_request, uri, headers):
                match = mock_response
                break

        if match is not None:
            self.request_callback_match += 1

            fmt = (uri, match)
            om.out.debug('[request_callback] URI %s matched %s' % fmt)

            return match.get_response(http_request, uri, headers)

        else:
            om.out.debug('[request_callback] URI %s will return 404' % uri)
            return MockResponse.get_404(http_request, uri, headers)

    @retry(tries=3, delay=0.5, backoff=2)
    def _verify_targets_up(self, target_list):
        msg = 'The target site "%s" is down: "%s"'

        for target in target_list:
            try:
                response = urllib2.urlopen(target.url_string)
                response.read()
            except urllib2.URLError, e:
                if hasattr(e, 'code'):
                    # pylint: disable=E1101
                    if e.code in (404, 403, 401):
                        continue
                    else:
                        no_code = 'Unexpected code %s' % e.code
                        self.assertTrue(False, msg % (target, no_code))
                    # pylint: enable=E1101

                self.assertTrue(False, msg % (target, e.reason))
            
            except Exception, e:
                self.assertTrue(False, msg % (target, e))

    def _scan(self,
              target,
              plugins,
              debug=False,
              assert_exceptions=True,
              verify_targets=True,
              misc_settings=None):
        """
        Setup env and start scan. Typically called from children's
        test methods.

        :param target: The target to scan.
        :param plugins: PluginConfig objects to activate and setup before
            the test runs.
        """
        self._set_target(target, verify_targets)
        self._set_enabled_plugins(plugins)
        self._set_output_manager(debug)
        self._set_uri_opener_settings()
        self._set_misc_settings(misc_settings)

        try:
            self._init_and_start(assert_exceptions)
        finally:
            # This prevents configurations from one test affecting the others
            self.misc_settings.set_default_values()

    def _set_target(self, target, verify_targets):
        if not isinstance(target, (basestring, tuple)):
            raise TypeError('Expected basestring or tuple in scan target.')
        
        if isinstance(target, tuple):
            target = tuple([URL(u) for u in target])
            
        elif isinstance(target, basestring):
            target = (URL(target),)
        
        if verify_targets and not self.MOCK_RESPONSES:
            self._verify_targets_up(target)
        
        target_opts = create_target_option_list(*target)
        self.w3afcore.target.set_options(target_opts)

    def _set_enabled_plugins(self, plugins):
        # Enable plugins to be tested
        for ptype, plugincfgs in plugins.items():
            self.w3afcore.plugins.set_plugins([p.name for p in plugincfgs],
                                              ptype)

            for pcfg in plugincfgs:

                if pcfg.name == 'all':
                    continue

                plugin_instance = self.w3afcore.plugins.get_plugin_inst(ptype,
                                                                        pcfg.name)
                default_option_list = plugin_instance.get_options()
                unit_test_options = pcfg.options

                for option in default_option_list:
                    if option.get_name() not in unit_test_options:
                        unit_test_options.add(option)

                self.w3afcore.plugins.set_plugin_options(ptype, pcfg.name,
                                                         unit_test_options)

    def _set_output_manager(self, debug):
        # Enable text output plugin for debugging
        environ_debug = os.environ.get('DEBUG', '0') == '1'
        if debug or environ_debug:
            self._configure_debug()

    def _set_uri_opener_settings(self):
        # Set a special user agent to be able to grep the logs and identify
        # requests sent by each test
        custom_test_agent = self.get_custom_agent()
        self.w3afcore.uri_opener.settings.set_user_agent(custom_test_agent)

    def _set_misc_settings(self, misc_settings):
        if misc_settings is None:
            return

        options = self.misc_settings.get_options()

        for setting, value in misc_settings.iteritems():
            options[setting].set_value(value)

        self.misc_settings.set_options(options)

    def _init_and_start(self, assert_exceptions):
        # Verify env and start the scan
        self.w3afcore.plugins.init_plugins()
        self.w3afcore.verify_environment()
        self.w3afcore.start()

        #
        # I want to make sure that we don't have *any hidden* exceptions in our
        # tests. This was in tearDown before, but moved here because I was
        # getting failed assertions in my test code that were because of
        # exceptions in the scan and they were hidden.
        #
        if assert_exceptions:
            caught_exceptions = self.w3afcore.exception_handler.get_all_exceptions()
            tracebacks = [e.get_details() for e in caught_exceptions]
            self.assertEqual(len(caught_exceptions), 0, tracebacks)

    def _scan_assert(self, config, expected_path_param, ok_to_miss,
                     kb_addresses, skip_startwith=(), debug=False):

        # Make sure the subclass is properly configured
        self.assertIsNotNone(self.target_url)
        self.assertIsNotNone(self.base_path)

        # Scan
        self._scan(self.target_url, config, debug=debug)

        # Get the results
        vulns = []
        for kb_address in kb_addresses:
            vulns.extend(self.kb.get(*kb_address))

        found_path_param = set()
        for vuln in vulns:
            path = vuln.get_url().get_path().replace(self.base_path, '')
            found_path_param.add((path, vuln.get_token_name()))

        self.assertEqual(expected_path_param, found_path_param)

        #
        #   Now we assert the unknowns
        #
        all_known_urls = self.kb.get_all_known_urls()
        all_known_files = [u.get_path().replace(self.base_path, '') for u in all_known_urls]

        expected = [path for path, param in expected_path_param]

        missing = []

        for path in all_known_files:

            should_continue = False

            for skip_start in skip_startwith:
                if path.startswith(skip_start):
                    should_continue = True
                    break

            if should_continue:
                continue

            if path == u'':
                continue

            if path in ok_to_miss:
                continue

            if path in expected:
                # Already checked this one
                continue

            missing.append(path)

        missing.sort()
        self.assertEqual(missing, [])

    def get_custom_agent(self):
        """
        :return: The test agent for easier log grep
        """
        return 'Mozilla/4.0 (compatible; w3af.org; TestCase: %s)' % self.id()

    def _formatMessage(self, msg, standardMsg):
        """Honour the longMessage attribute when generating failure messages.
        If longMessage is False this means:
            * Use only an explicit message if it is provided
            * Otherwise use the standard message for the assert

        If longMessage is True:
            * Use the standard message
            * If an explicit message is provided, plus ' : ' and the explicit
              message
        """
        if msg:
            data = '%s:\n%s' % (standardMsg, pprint.pformat(msg))
            return data.replace('\\n', '\n')

        return standardMsg

    def _configure_debug(self):
        """
        Configure debugging for the scans to be run.
        """
        ptype = 'output'
        pname = 'text_file'

        enabled_output = self.w3afcore.plugins.get_enabled_plugins(ptype)
        enabled_output += [pname]
        self.w3afcore.plugins.set_plugins(enabled_output, ptype)

        # Now we configure the output file to point to CircleCI's artifact
        # directory (when run on circle) and /tmp/ when run on our
        # workstation
        output_dir = os.environ.get('CIRCLE_ARTIFACTS', tempfile.gettempdir())
        rnd = rand_alnum(6)
        text_output = os.path.join(output_dir, 'output-%s.txt' % rnd)
        http_output = os.path.join(output_dir, 'output-http-%s.txt' % rnd)

        text_file_inst = self.w3afcore.plugins.get_plugin_inst(ptype, pname)

        default_opts = text_file_inst.get_options()
        default_opts['output_file'].set_value(text_output)
        default_opts['http_output_file'].set_value(http_output)
        default_opts['verbose'].set_value(True)

        print('Logging to %s' % text_output)

        self.w3afcore.plugins.set_plugin_options(ptype, pname, default_opts)


class PluginConfig(object):

    BOOL = 'boolean'
    STR = 'string'
    LIST = 'list'
    INT = 'integer'
    URL = 'url'
    INPUT_FILE = 'input_file'
    QUERY_STRING = 'query_string'
    HEADER = 'header'

    def __init__(self, name, *opts):
        self._name = name
        self._options = OptionList()
        for optname, optval, optty in opts:
            self._options.append(opt_factory(optname, str(optval), '', optty))

    @property
    def name(self):
        return self._name

    @property
    def options(self):
        return self._options


class ReadExploitTest(PluginTest):
    def _exploit_vuln(self, vuln_to_exploit_id, exploit_plugin):
        self.w3afcore.uri_opener.set_exploit_mode(True)
        plugin = self.w3afcore.plugins.get_plugin_inst('attack', exploit_plugin)

        self.assertTrue(plugin.can_exploit(vuln_to_exploit_id))

        exploit_result = plugin.exploit(vuln_to_exploit_id)

        self.assertEqual(len(exploit_result), 1, exploit_result)

        #
        # Now I start testing the shell itself!
        #
        shell = exploit_result[0]
        etc_passwd = shell.generic_user_input('read', ['/etc/passwd'])
        self.assertIn('root', etc_passwd)
        self.assertIn('/bin/bash', etc_passwd)

        lsp = shell.generic_user_input('lsp', [])
        self.assertTrue('apache_config_directory' in lsp)

        payload = shell.generic_user_input('payload',
                                           ['apache_config_directory'])
        self.assertTrue(payload is None)
        
        if isinstance(shell, ReadShell):
            _help = shell.help(None)
            self.assertNotIn('execute', _help)
            self.assertNotIn('upload', _help)
            self.assertIn('read', _help)
            
            _help = shell.help('read')
            self.assertIn('read', _help)
            self.assertIn('/etc/passwd', _help)
        
        return shell


class ExecExploitTest(ReadExploitTest):
    def _exploit_vuln(self, vuln_to_exploit_id, exploit_plugin):
        shell = super(ExecExploitTest, self)._exploit_vuln(vuln_to_exploit_id,
                                                           exploit_plugin)
        
        etc_passwd = shell.generic_user_input('e', ['cat', '/etc/passwd'])
        self.assertIn('root', etc_passwd)
        self.assertIn('/bin/bash', etc_passwd)
        
        _help = shell.help(None)
        self.assertIn('execute', _help)
        self.assertIn('upload', _help)
        self.assertIn('read', _help)
        
        _help = shell.help('read')
        self.assertIn('read', _help)
        self.assertIn('/etc/passwd', _help)

        
@attr('root')
def onlyroot(meth):
    """
    Function to decorate tests that should be called as root.

    Raises a nose SkipTest exception if the user doesn't have root permissions.
    """
    @wraps(meth)
    def test_inner_onlyroot(self, *args, **kwds):
        """Note that this method needs to start with test_ in order for nose
        to run it!"""
        if os.geteuid() == 0 or os.getuid() == 0:
            return meth(self, *args, **kwds)
        else:
            raise SkipTest('This test requires root privileges.')
    test_inner_onlyroot.root = True
    return test_inner_onlyroot


def create_target_option_list(*target):
    opts = OptionList()

    opt = opt_factory('target', '', '', URL_LIST)
    opt.set_value(','.join([u.url_string for u in target]))
    opts.add(opt)
    
    opt = opt_factory('target_os', ('unknown', 'unix', 'windows'), '', 'combo')
    opts.add(opt)
    
    opt = opt_factory('target_framework',
                      ('unknown', 'php', 'asp', 'asp.net',
                       'java', 'jsp', 'cfm', 'ruby', 'perl'),
                      '', 'combo')
    opts.add(opt)
    
    return opts


class MockResponse(object):
    NO_MOCK = 'httpretty can not mock this method'
    KNOWN_METHODS = ('GET', 'PUT', 'POST', 'DELETE', 'HEAD', 'PATCH',
                     'OPTIONS', 'CONNECT')

    def __init__(self, url, body, content_type='text/html', status=200,
                 method='GET', headers=None, delay=None):
        self.url = url
        self.body = body
        self.status = status
        self.method = method
        self.delay = delay

        self.content_type = content_type
        self.headers = {'Content-Type': content_type}

        if headers is not None:
            self.headers.update(headers)

        assert method in self.KNOWN_METHODS, self.NO_MOCK
        assert isinstance(url, (basestring, RE_COMPILE_TYPE))

        if isinstance(url, basestring):
            url = URL(url)
            assert url.get_domain(), 'Need to specify the MockResponse domain'

    def __repr__(self):
        if isinstance(self.url, RE_COMPILE_TYPE):
            match = 're:"%s"' % self.url.pattern
        else:
            match = self.url

        return '<MockResponse (%s|%s)>' % (match, self.status)

    @staticmethod
    def get_404(http_request, uri, headers):
        status = 404
        body = 'Not found'
        headers.update({'Content-Type': 'text/html', 'status': status})
        return status, headers, body

    def get_response(self, http_request, uri, response_headers):
        """
        :return: A response containing:
                    * HTTP status code
                    * Headers dict
                    * Response body string
        """
        if callable(self.body):
            return self.body(self, http_request, uri, response_headers)

        response_headers.update({'status': self.status})
        response_headers.update(self.headers)

        if self.delay is not None:
            time.sleep(self.delay)

        return self.status, response_headers, self.body

    def matches(self, http_request, uri, headers):
        if self.method != http_request.command:
            return False

        if not self.url_matches(uri):
            return False

        return True

    def url_matches(self, request_uri):
        """
        :param request_uri: The http request URI sent by the plugin
        :return: True if the request_uri matches this mock_response
        """
        if isinstance(self.url, basestring):
            request_uri = URL(request_uri)
            response_uri = URL(self.url)

            request_path = request_uri.get_path_qs()
            request_domain = request_uri.get_domain()

            response_path = response_uri.get_path_qs()
            response_domain = response_uri.get_domain()

            if response_domain != request_domain:
                return False

            if request_path != response_path:
                return False

            return True

        elif isinstance(self.url, RE_COMPILE_TYPE):
            if self.url.match(request_uri):
                return True

        return False


LOREM = """Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Integer
        eu lacus accumsan arcu fermentum euismod. Donec pulvinar porttitor
        tellus. Aliquam venenatis. Donec facilisis pharetra tortor.  In nec
        mauris eget magna consequat convallis. Nam sed sem vitae odio
        pellentesque interdum. Sed consequat viverra nisl. Suspendisse arcu
        metus, blandit quis, rhoncus, pharetra eget, velit. Mauris
        urna. Morbi nonummy molestie orci. Praesent nisi elit, fringilla ac,
        suscipit non, tristique vel, mauris. Curabitur vel lorem id nisl porta
        adipiscing. Suspendisse eu lectus. In nunc. Duis vulputate tristique
        enim. Donec quis lectus a justo imperdiet tempus."""
