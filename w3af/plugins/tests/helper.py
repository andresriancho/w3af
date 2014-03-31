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
import os
import re
import unittest
import urllib2
import httpretty
import tempfile

from functools import wraps
from nose.plugins.skip import SkipTest
from nose.plugins.attrib import attr

import w3af.core.data.kb.knowledge_base as kb

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
    see http://stackoverflow.com/questions/6689537/nose-test-generators-inside-class ,
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
            
            url = URL(self.target_url)
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

        httpretty.register_uri(httpretty.GET,
                               re.compile(re_str),
                               body=self.request_callback)

    def tearDown(self):
        self.w3afcore.quit()
        self.kb.cleanup()

        if self.MOCK_RESPONSES:
            httpretty.disable()

    def request_callback(self, method, uri, headers):
        status = 404
        body = 'Not found'
        content_type = 'text/html'

        for mock_response in self.MOCK_RESPONSES:
            if isinstance(mock_response.url, basestring):
                if uri.endswith(mock_response.url):
                    status = mock_response.status
                    body = mock_response.body
                    content_type = mock_response.content_type

                    break
            elif isinstance(mock_response.url, RE_COMPILE_TYPE):
                if mock_response.url.match(uri):
                    status = mock_response.status
                    body = mock_response.body
                    content_type = mock_response.content_type

                    break

        headers['Content-Type'] = content_type
        headers['status'] = status

        return status, headers, body

    @retry(tries=3, delay=0.5, backoff=2)
    def _verify_targets_up(self, target_list):
        for target in target_list:
            msg = 'The target site "%s" is down' % target
            
            try:
                response = urllib2.urlopen(target.url_string)
                response.read()
            except urllib2.URLError, e:
                if hasattr(e, 'code') and e.code in (404, 401):
                    continue
                
                self.assertTrue(False, msg)
            
            except Exception, e:
                self.assertTrue(False, msg)

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
        if debug: self._configure_debug()

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
            msg = [e.get_summary() for e in caught_exceptions]
            self.assertEqual(len(caught_exceptions), 0, msg)

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
    def __init__(self, url, body, content_type='text/html', status=200): 
        self.url = url
        self.body = body
        self.content_type = content_type
        self.status = status

        assert isinstance(url, (basestring, RE_COMPILE_TYPE))

    def __repr__(self):
        return '<MockResponse (%s|%s)>' % (self.url, self.status)