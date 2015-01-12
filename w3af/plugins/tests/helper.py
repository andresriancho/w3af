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
import unittest
import urllib2
import httpretty
import tempfile
import pprint
import time

from functools import wraps
from nose.plugins.skip import SkipTest
from nose.plugins.attrib import attr

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.w3afCore import w3afCore
from w3af.core.controllers.misc.homeDir import W3AF_LOCAL_PATH
from w3af.core.controllers.misc.decorators import retry

from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import URL_LIST
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.parsers.url import URL
from w3af.core.data.kb.read_shell import ReadShell 

os.chdir(W3AF_LOCAL_PATH)
RE_COMPILE_TYPE = type(re.compile(''))


@attr('moth')
class PluginTest(unittest.TestCase):
    """
    Remember that nosetests can't find test generators in unittest.TestCase,
    http://stackoverflow.com/questions/6689537/nose-test-generators-inside-class
    """
    MOCK_RESPONSES = []
    runconfig = {}
    kb = kb.kb
    target_url = None
    
    def setUp(self):
        self.kb.cleanup()
        self.w3afcore = w3afCore()
        
        if self.MOCK_RESPONSES:
            httpretty.enable()
            
            try:
                url = URL(self.target_url)
            except ValueError, ve:
                msg = 'When using MOCK_RESPONSES you need to set the'\
                      ' target_url attribute to a valid URL, exception was:'\
                      ' "%s".'
                raise Exception(msg % ve)

            domain = url.get_domain()
            proto = url.get_protocol()
            port = url.get_port()

            self._register_httpretty_uri(proto, domain, port)

    def _register_httpretty_uri(self, proto, domain, port):
        assert isinstance(port, int), 'Port needs to be an integer'

        if (port == 80 and proto == 'http') or\
        (port == 443 and proto == 'https'):
            re_str = "%s://%s/(.*)" % (proto, domain)
        else:
            re_str = "%s://%s:%s/(.*)" % (proto, domain, port)

        all_methods = set(mock_resp.method for mock_resp in self.MOCK_RESPONSES)

        for http_method in all_methods:
            httpretty.register_uri(http_method,
                                   re.compile(re_str),
                                   body=self.request_callback)

    def tearDown(self):
        self.w3afcore.quit()
        self.kb.cleanup()

        if self.MOCK_RESPONSES:
            httpretty.disable()
            httpretty.reset()

    def assertAllVulnNamesEqual(self, vuln_name, vulns):
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
        all_info = self.kb.get_all_infos()
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

    def request_callback(self, method, uri, headers):
        match = None

        for mock_response in self.MOCK_RESPONSES:

            if mock_response.method != method.command:
                continue

            if self._mock_url_matches(mock_response, uri):
                match = mock_response
                break

        if match is not None:
            fmt = (uri, match)
            om.out.debug('[request_callback] URI %s matched %s' % fmt)

            headers.update({'status': match.status})
            headers.update(match.headers)

            if match.delay is not None:
                time.sleep(match.delay)

            return (match.status,
                    headers,
                    match.get_body(method, uri, headers))

        else:
            om.out.debug('[request_callback] URI %s will return 404' % uri)

            status = 404
            body = 'Not found'
            headers.update({'Content-Type': 'text/html', 'status': status})

            return status, headers, body

    def _mock_url_matches(self, mock_response, request_uri):
        """
        :param mock_response: A MockResponse instance configured by dev
        :param request_uri: The http request URI sent by the plugin
        :return: True if the request_uri matches this mock_response
        """
        if isinstance(mock_response.url, basestring):
            if request_uri.endswith(mock_response.url):
                return True

        elif isinstance(mock_response.url, RE_COMPILE_TYPE):
            if mock_response.url.match(request_uri):
                return True

        return False

    @retry(tries=3, delay=0.5, backoff=2)
    def _verify_targets_up(self, target_list):
        msg = 'The target site "%s" is down: "%s"'

        for target in target_list:
            try:
                response = urllib2.urlopen(target.url_string)
                response.read()
            except urllib2.URLError, e:
                if hasattr(e, 'code') and e.code in (404, 403, 401):
                    continue

                no_code = 'Unexpected code %s' % e.code
                self.assertTrue(False, msg % (target, no_code))
            
            except Exception, e:
                self.assertTrue(False, msg % (target, e))

    def _scan(self, target, plugins, debug=False, assert_exceptions=True,
              verify_targets=True):
        """
        Setup env and start scan. Typically called from children's
        test methods.

        :param target: The target to scan.
        :param plugins: PluginConfig objects to activate and setup before
            the test runs.
        """
        if not isinstance(target, (basestring, tuple)):
            raise TypeError('Expected basestring or tuple in scan target.')
        
        if isinstance(target, tuple):
            target = tuple([URL(u) for u in target])
            
        elif isinstance(target, basestring):
            target = (URL(target),)
        
        if verify_targets:
            self._verify_targets_up(target)
        
        target_opts = create_target_option_list(*target)
        self.w3afcore.target.set_options(target_opts)

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

        # Enable text output plugin for debugging
        environ_debug = os.environ.get('DEBUG', '0') == '1'
        if debug or environ_debug:
            self._configure_debug()

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

    def _formatMessage(self, msg, standardMsg):
        """Honour the longMessage attribute when generating failure messages.
        If longMessage is False this means:
        * Use only an explicit message if it is provided
        * Otherwise use the standard message for the assert

        If longMessage is True:
        * Use the standard message
        * If an explicit message is provided, plus ' : ' and the explicit message
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
        text_output = os.path.join(output_dir, 'output.txt')
        http_output = os.path.join(output_dir, 'output-http.txt')

        text_file_inst = self.w3afcore.plugins.get_plugin_inst(ptype, pname)

        default_opts = text_file_inst.get_options()
        default_opts['output_file'].set_value(text_output)
        default_opts['http_output_file'].set_value(http_output)
        default_opts['verbose'].set_value(True)

        self.w3afcore.plugins.set_plugin_options(ptype, pname, default_opts)


class PluginConfig(object):

    BOOL = 'boolean'
    STR = 'string'
    LIST = 'list'
    INT = 'integer'
    URL = 'url'
    INPUT_FILE = 'input_file'

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
        plugin = self.w3afcore.plugins.get_plugin_inst('attack', exploit_plugin)

        self.assertTrue(plugin.can_exploit(vuln_to_exploit_id))

        exploit_result = plugin.exploit(vuln_to_exploit_id)

        self.assertEqual(len(exploit_result), 1, exploit_result)

        #
        # Now I start testing the shell itself!
        #
        shell = exploit_result[0]
        etc_passwd = shell.generic_user_input('read', ['/etc/passwd',])
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
        
        etc_passwd = shell.generic_user_input('e', ['cat', '/etc/passwd',])
        self.assertTrue('root' in etc_passwd)
        self.assertTrue('/bin/bash' in etc_passwd)
        
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

        assert method in ('GET', 'PUT', 'POST', 'DELETE', 'HEAD', 'PATCH',
                          'OPTIONS', 'CONNECT'), 'httpretty can not mock this'\
                                                 ' method'
        assert isinstance(url, (basestring, RE_COMPILE_TYPE))

    def __repr__(self):
        return '<MockResponse (%s|%s)>' % (self.url, self.status)

    def get_body(self, method, uri, headers):
        """
        :param method: HTTP method sent by plugin
        :param uri: The http request URI sent by the plugin
        :param headers: The http headers sent by plugin
        :return: Tuple with the response we'll send to the plugin
        """
        if not callable(self.body):
            # A string
            return self.body

        return self.body(method, uri, headers)