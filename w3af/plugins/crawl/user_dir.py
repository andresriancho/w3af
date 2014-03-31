"""
user_dir.py

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
import os
import csv

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af import ROOT_PATH

from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.dc.headers import Headers
from w3af.core.data.kb.info import Info

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.controllers.misc.levenshtein import relative_distance_lt


class user_dir(CrawlPlugin):
    """
    Try to find user directories like "http://test/~user/" and identify the remote OS based on them.
    
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    DB_PATH = os.path.join(ROOT_PATH, 'plugins', 'crawl', 'user_dir')

    def __init__(self):
        CrawlPlugin.__init__(self)

        # User configured variables
        self._identify_OS = True
        self._identify_applications = True

        # For testing
        self._do_fast_search = False

    @runonce(exc_class=RunOnce)
    def crawl(self, fuzzable_request):
        """
        Searches for user directories.

        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        base_url = fuzzable_request.get_url().base_url()
        self._headers = Headers([('Referer', base_url.url_string)])

        # Create a response body to compare with the others
        non_existent_user = '~_w_3_a_f_/'
        test_URL = base_url.url_join(non_existent_user)
        try:
            response = self._uri_opener.GET(test_URL, cache=True,
                                            headers=self._headers)
        except:
            msg = 'user_dir failed to create a non existent signature.'
            raise BaseFrameworkException(msg)

        response_body = response.get_body()
        self._non_existent = response_body.replace(non_existent_user, '')

        # Check the users to see if they exist
        url_user_list = self._create_dirs(base_url)
        #   Send the requests using threads:
        self.worker_pool.map_multi_args(self._do_request, url_user_list)

        # Only do this if I already know that users can be identified.
        if kb.kb.get('user_dir', 'users'):
            if self._identify_OS:
                self._advanced_identification(base_url, 'os')

            if self._identify_applications:
                self._advanced_identification(base_url, 'applications')

            # Report findings of remote OS, applications, users, etc.
            self._report_findings()

    def _do_request(self, mutated_url, user):
        """
        Perform the request and compare.

        :return: The HTTP response id if the mutated_url is a web user
                 directory, None otherwise.
        """
        response = self._uri_opener.GET(mutated_url, cache=True,
                                        headers=self._headers)
        
        path = mutated_url.get_path()
        response_body = response.get_body().replace(path, '')

        if relative_distance_lt(response_body, self._non_existent, 0.7):

            # Avoid duplicates
            if user not in [u['user'] for u in kb.kb.get('user_dir', 'users')]:
                desc = 'A user directory was found at: %s'
                desc = desc % response.get_url()
                
                i = Info('Web user home directory', desc, response.id,
                         self.get_name())
                i.set_url(response.get_url())
                i['user'] = user

                kb.kb.append(self, 'users', i)

                for fr in self._create_fuzzable_requests(response):
                    self.output_queue.put(fr)

            return response.id

        return None

    def _get_users_from_csv(self, ident):
        """
        :return: A list of users from the user dir database.
        """
        assert ident in ('applications', 'os'), 'Invalid identification'

        csv_db = os.path.join(self.DB_PATH, '%s.csv' % ident)
        file_handler = file(csv_db, 'rb')
        reader = csv.reader(file_handler)

        while True:
            try:
                csv_row = reader.next()
                desc, user = csv_row
            except StopIteration:
                break
            except csv.Error:
                # line contains NULL byte, and other similar things.
                # https://github.com/andresriancho/w3af/issues/1490
                msg = 'user_dir: Ignoring data with CSV error at line "%s"'
                om.out.debug(msg % reader.line_num)
            except ValueError:
                om.out.debug('Invalid user_dir input: "%r"' % csv_row)
            else:
                yield desc, user

    def _advanced_identification(self, url, ident):
        """
        :return: None, This method will save the results to the kb and print and
                 informational message to the user.
        """
        for data_related_to_user, user in self._get_users_from_csv(ident):
            url_user_list = self._create_dirs(url, user_list=[user, ])
            for user_dir, user in url_user_list:
                
                http_response_id = self._do_request(user_dir, user)
                
                if http_response_id is not None:

                    if ident == 'os':
                        desc = 'The remote OS can be identified as "%s" based'\
                               ' on the remote user "%s" information that is'\
                               ' exposed by the web server.'
                        desc = desc % (data_related_to_user, user)
                        
                        name = 'Fingerprinted operating system'
                    else:
                        desc = 'The remote server has "%s" installed, w3af'\
                               ' found this information based on the remote'\
                               ' user "%s".'
                        desc = desc % (data_related_to_user, user)
                        
                        name = 'Identified installed application'
                    
                    i = Info(name, desc, http_response_id, self.get_name())
                    i[ident] = data_related_to_user
                    kb.kb.append(self, ident, i)

    def _report_findings(self):
        """
        Print all the findings to the output manager.
        :return : None
        """
        apps = 'applications'

        user_list = [u['user'] for u in kb.kb.get('user_dir', 'users')]
        OS_list = [u['remote_os'] for u in kb.kb.get('user_dir', 'os')]
        app_list = [u[apps] for u in kb.kb.get('user_dir', apps)]

        def print_bullet_list(item_list):
            item_list = list(set(item_list))
            for i in item_list:
                om.out.information('- ' + i)

        if user_list:
            om.out.information('The following users were found on the remote'\
                               ' operating system:')
            print_bullet_list(user_list)

        if OS_list:
            om.out.information('The remote operating system was identified as:')
            print_bullet_list(OS_list)
        elif self._identify_OS:
            msg = 'Failed to identify the remote OS based on the users'\
                  ' available in the user_dir plugin database.'
            om.out.information(msg)

        if app_list:
            om.out.information('The remote server has the following'
                               ' applications installed:')
            print_bullet_list(app_list)
        elif self._identify_applications:
            msg = 'Failed to identify any installed applications based on the'\
                  ' users available in the user_dir plugin database.'
            om.out.information(msg)

    def _create_dirs(self, url, user_list=None):
        """
        Append the users to the URL.

        :param url: The original url
        :return: A list of URL objects with the username appended.
        """
        res = []

        if user_list is None:
            user_list = self._get_users()

        for user in user_list:
            res.append((url.url_join('/' + user + '/'), user))
            res.append((url.url_join('/~' + user + '/'), user))

        return res

    def _get_users(self):
        """
        :return: All usernames collected by other plugins.
        """
        res = []

        infoList = kb.kb.get('emails', 'emails')

        for i in infoList:
            res.append(i['user'])

        # Add some common users:
        res.extend(['www-data', 'www', 'nobody', 'root', 'admin',
                   'test', 'ftp', 'backup'])

        return res

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()
        
        d = 'Try to identify the remote operating system based on the'\
            ' remote users'
        o = opt_factory('identify_os', self._identify_OS, d, 'boolean')
        ol.add(o)
        
        d = 'Try to identify applications installed remotely using the'\
             ' available users'
        o = opt_factory('identify_apps', self._identify_applications, d,
                        'boolean')
        ol.add(o)
        
        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param options_list: An OptionList with the options for the plugin.
        :return: No value is returned.
        """
        self._identify_OS = options_list['identify_os'].get_value()
        self._identify_applications = options_list['identify_apps'].get_value()

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins that should be run before
                 the current one.
        """
        if self._do_fast_search:
            # This was left here for fast testing of the plugin.
            return []
        else:
            # This is the correct return value for this method.
            return ['infrastructure.finger_bing',
                    'infrastructure.finger_google',
                    'infrastructure.finger_pks']

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin will try to find user home directories based on the
        knowledge gained by other plugins, and an internal knowledge base. For
        example, if the target URL is:
            - http://test/

        And other plugins found this valid email accounts:
            - test@test.com
            - f00b4r@test.com

        This plugin will request:
            - http://test/~test/
            - http://test/test/
            - http://test/~f00b4r/
            - http://test/f00b4r/

        If the response is not a 404 error, then we have found a new URL. And
        confirmed the existence of a user in the remote system. This plugin
        will also identify the remote operating system and installed
        applications based on the user names that are available.
        """
