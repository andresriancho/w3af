"""
BruteforcePlugin.py

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
import os.path

from itertools import izip, repeat

import w3af.core.data.kb.knowledge_base as kb

from w3af import ROOT_PATH
from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import BOOL, STRING, INPUT_FILE, INT
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.misc.mask_password import mask_password_string
from w3af.core.controllers.misc.safe_deepcopy import safe_deepcopy
from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.controllers.bruteforce.bruteforcer import (UserPasswordBruteforcer,
                                                          PasswordBruteforcer)


class BruteforcePlugin(AuditPlugin):
    """
    This plugin is a superclass for plugins that want to bruteforce any type of
    login.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    BASE_CFG_PATH = os.path.join(ROOT_PATH, 'core', 'controllers', 'bruteforce')

    def __init__(self):
        AuditPlugin.__init__(self)

        # Config params
        self._users_file = os.path.join(self.BASE_CFG_PATH, 'users.txt')
        self._passwd_file = os.path.join(self.BASE_CFG_PATH, 'passwords.txt')
        self._combo_file = os.path.join(self.BASE_CFG_PATH, 'combo.txt')
        self._combo_separator = ":"
        self._use_emails = True
        self._use_SVN_users = True
        self._pass_eq_user = True
        self._l337_p4sswd = True
        self._use_profiling = True
        self._profiling_number = 50
        self._stop_on_first = True
        self._mask_password_in_report = False

        # Internal vars
        self._found = False
        self._already_reported = []
        self._already_tested = []

    def _create_user_pass_generator(self, url):
        up_bf = UserPasswordBruteforcer(url)
        up_bf.use_emails = self._use_emails
        up_bf.use_profiling = self._use_profiling
        up_bf.profiling_number = self._profiling_number
        up_bf.use_SVN_users = self._use_SVN_users
        up_bf.l337_p4sswd = self._l337_p4sswd
        up_bf.users_file = self._users_file
        up_bf.passwd_file = self._passwd_file
        up_bf.combo_file = self._combo_file
        up_bf.combo_separator = self._combo_separator
        up_bf.pass_eq_user = self._pass_eq_user
        return up_bf.generator()

    def _create_pass_generator(self, url):
        p_bf = PasswordBruteforcer(url)
        p_bf.use_profiling = self._use_profiling
        p_bf.profiling_number = self._profiling_number
        p_bf.l337_p4sswd = self._l337_p4sswd
        p_bf.passwd_file = self._passwd_file
        return p_bf.generator()

    def audit(self, freq, debugging_id=None):
        """
        This method MUST be implemented on every plugin.

        :param freq: A FuzzableRequest that is going to be modified and sent.
        :param debugging_id: The ID to use in the logs to be able to track this
                             call to audit(). Plugins need to send this ID to
                             the ExtendedUrllib to get improved logging.
        """
        msg = 'Plugin is not implementing required method audit'
        raise NotImplementedError(msg)

    def bruteforce_wrapper(self, fuzzable_request):
        """
        :param fuzzable_request: The FuzzableRequest instance to analyze
        :return: A list with FuzzableRequests (if we were able to bruteforce
                 any forms/basic auth present in fuzzable_request).
        """
        debugging_id = rand_alnum(8)

        self.audit(safe_deepcopy(fuzzable_request),
                   debugging_id=debugging_id)

        res = []

        for v in kb.kb.get(self.get_name(), 'auth'):

            if v.get_url() not in self._already_reported:
                self._already_reported.append(v.get_url())
                res.append(v['request'])

        return res

    def _bruteforce(self, url, combinations, debugging_id):
        """
        :param url: A string representation of an URL
        :param combinations: A generator with tuples that contain (user,pass)
        :param debugging_id: The ID to use in the logs to be able to track this
                             call to audit(). Plugins need to send this ID to
                             the ExtendedUrllib to get improved logging.
        """
        args_iter = izip(repeat(url),
                         combinations,
                         repeat(debugging_id))

        self.worker_pool.map_multi_args(self._brute_worker,
                                        args_iter,
                                        chunksize=100)

    def end(self):
        raise NotImplementedError('Bruteforce plugins MUST override the'
                                  ' end() method.')

    def _brute_worker(self, url, combination, debugging_id):
        """
        This is the method that sends the request to the remote server.

        :param url: A string representation of an URL
        :param combination: A list of tuples with (user,pass)
        """
        raise NotImplementedError('Bruteforce plugins MUST override method'
                                  ' _bruteWorker.')

    def _get_password_for_report(self, passwd):
        password_for_report = passwd
        if self._mask_password_in_report:
            password_for_report = mask_password_string(passwd)

        return password_for_report

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Users file to use in bruteforcing'
        o = opt_factory('users_file', self._users_file, d, INPUT_FILE)
        ol.add(o)

        d = 'Passwords file to use in bruteforcing'
        o = opt_factory('passwd_file', self._passwd_file, d, INPUT_FILE)
        ol.add(o)

        d = 'This indicates if we will use usernames from SVN headers collected by w3af plugins in bruteforce.'
        o = opt_factory('use_svn_users', self._use_SVN_users, d, BOOL)
        ol.add(o)

        d = 'This indicates if the bruteforce should stop after finding the first correct user and password.'
        o = opt_factory('stop_on_first', self._stop_on_first, d, BOOL)
        ol.add(o)

        d = 'This indicates if the bruteforce should try password equal user in logins.'
        o = opt_factory('pass_eq_user', self._pass_eq_user, d, BOOL)
        ol.add(o)

        d = 'This indicates if the bruteforce should try l337 passwords'
        o = opt_factory('use_leet_password', self._l337_p4sswd, d, BOOL)
        ol.add(o)

        d = 'This indicates if the bruteforcer should use emails collected by w3af plugins as users.'
        o = opt_factory('use_emails', self._use_emails, d, BOOL)
        ol.add(o)

        d = 'This indicates if the bruteforce should use password profiling to collect new passwords.'
        o = opt_factory('use_profiling', self._use_profiling, d, BOOL)
        ol.add(o)

        d = 'This indicates how many passwords from profiling will be used.'
        o = opt_factory('profiling_number', self._profiling_number, d, INT)
        ol.add(o)

        d = 'Mask valid passwords found via brute-force with * when writing to report'
        o = opt_factory('mask_password_report', self._mask_password_in_report, d, BOOL)
        ol.add(o)

        d = 'Combo of username and password, file to use in bruteforcing'
        o = opt_factory('combo_file', self._combo_file, d, INPUT_FILE)
        ol.add(o)

        d = 'Separator string used in Combo file to split username and password'
        o = opt_factory('combo_separator', self._combo_separator, d, STRING)
        ol.add(o)

        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user interface
        generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._users_file = options_list['users_file'].get_value()
        self._stop_on_first = options_list['stop_on_first'].get_value()
        self._passwd_file = options_list['passwd_file'].get_value()
        self._pass_eq_user = options_list['pass_eq_user'].get_value()
        self._l337_p4sswd = options_list['use_leet_password'].get_value()
        self._use_emails = options_list['use_emails'].get_value()
        self._use_SVN_users = options_list['use_svn_users'].get_value()
        self._use_profiling = options_list['use_profiling'].get_value()
        self._profiling_number = options_list['profiling_number'].get_value()
        self._combo_file = options_list['combo_file'].get_value()
        self._combo_separator = options_list['combo_separator'].get_value()
        self._mask_password_in_report = options_list['mask_password_report'].get_value()

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins that should be run before
                the current one.
        """
        return ['grep.password_profiling', 'grep.get_emails', 'grep.http_auth_detect']

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin bruteforces form authentication logins.

        Eleven configurable parameters exist:
            - users_file
            - stop_on_first
            - passwd_file
            - pass_eq_user
            - use_leet_password
            - use_svn_users
            - use_emails
            - use_profiling
            - profiling_number
            - combo_file
            - combo_separator

        This plugin will take users from the file pointed by "users_file", mail
        users found on the site ( if "useMailUsers" is set to True ), emails found
        on the site ( if "use_emails" is set to True ), and svn users found on the
        site ( if "use_svn_users" is set to True ).

        This plugin will take passwords from the file pointed by "passwd_file"
        and the result of the password profiling plugin (if "use_profiling"
        is set to True). The profiling_number sets the number of results from
        the password profiling plugin to use in the password field.

        This plugin will take a combination of user and password from the
        pointed file by "combo_file". The combo_separator set the string used to
        split each combination in the combo_file.

        The "stop_on_first" parameter indicates if the bruteforce will stop when
        finding the first valid credentials or not.
        """

    def get_type(self):
        return 'bruteforce'
