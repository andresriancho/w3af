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
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.controllers.output_manager as om

from w3af.core.data.dc.headers import Headers
from w3af.core.data.kb.info import Info
from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.controllers.misc.fuzzy_string_cmp import fuzzy_not_equal
from w3af.plugins.crawl.user_db.user_db import (OS, APPLICATION,
                                                get_users_from_csv)


class user_dir(CrawlPlugin):
    """
    Identify user directories like "http://test/~user/" and infer the remote OS.
    
    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    EMAIL_TAG = 'email'
    COMMON_TAG = 'common'
    EMAIL_USER_DESC = 'username extracted from email'
    COMMON_USER_DESC = 'common operating system username'
    COMMON_USERS = ['www-data', 'www', 'nobody', 'root', 'admin', 'test', 'ftp',
                    'backup']

    @runonce(exc_class=RunOnce)
    def crawl(self, fuzzable_request, debugging_id):
        """
        Searches for user directories.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        base_url = fuzzable_request.get_url().base_url()
        non_existent = self._create_non_existent_signature(base_url)

        # Send all the HTTP requests to identify the potential home directories
        test_generator = self._create_tests(base_url, non_existent)
        self.worker_pool.map_multi_args(self._check_user_dir, test_generator)

    def _create_non_existent_signature(self, base_url):
        """
        :param base_url: Something like http://target.com/
        :return: An HTTPResponse for GET http://target.com/~_w_3_a_f_/
        """
        headers = Headers([('Referer', base_url.url_string)])

        # Create a response body to compare with the others
        non_existent_user = '~_w_3_a_f_/'
        test_url = base_url.url_join(non_existent_user)
        try:
            response = self._uri_opener.GET(test_url, cache=True,
                                            headers=headers)
        except:
            msg = 'user_dir failed to create a non existent signature.'
            raise BaseFrameworkException(msg)

        response_body = response.get_body()

        return response_body.replace(non_existent_user, '')

    def _check_user_dir(self, mutated_url, user, user_desc, user_tag,
                        non_existent):
        """
        Perform the request and compare with non_existent

        :see _create_tests: For parameter description
        :return: The HTTP response id if the mutated_url is a web user
                 directory, None otherwise.
        """
        resp = self.http_get_and_parse(mutated_url)
        
        path = mutated_url.get_path()
        response_body = resp.get_body().replace(path, '')

        if fuzzy_not_equal(response_body, non_existent, 0.7):

            # Avoid duplicates
            user_infos = kb.kb.get('user_dir', 'users')
            known_users = [u.get('user', None) for u in user_infos]
            if user in known_users:
                return

            # Save the finding to the KB
            desc = 'An operating system user directory was found at: "%s"'
            desc %= resp.get_url()

            i = Info('Web user home directory', desc, resp.id, self.get_name())
            i.set_url(resp.get_url())
            i['user'] = user
            i['user_desc'] = user_desc
            i['user_tag'] = user_tag

            self.kb_append_uniq(self, 'users', i)

            # Analyze if we can get more information from this finding
            self._analyze_finding(i)

    def _analyze_finding(self, user_info):
        """
        If required, save a Info to the KB with the extra information we can
        get from user_info.

        :param user_info: A Info object as created by _check_user_dir
        :return: None, info is stored in KB
        """
        tag = user_info['user_tag']
        user = user_info['user']
        user_desc = user_info['user_desc']
        name = None
        desc = None

        if tag == OS:
            desc = ('The remote OS can be identified as "%s" based'
                    ' on the remote user "%s" information that is'
                    ' exposed by the web server.')
            desc %= (user_desc, user)

            name = 'Fingerprinted operating system'

        elif tag == APPLICATION:
            desc = ('The remote server has "%s" installed, w3af'
                    ' found this information based on the remote'
                    ' user "%s".')
            desc %= (user_desc, user)

            name = 'Identified installed application'

        if name is not None and desc is not None:
            i = Info(name, desc, user_info.get_id(), self.get_name())
            i.set_url(user_info.get_url())

            kb.kb.append(self, 'users', i)
            om.out.report_finding(i)

    def _create_tests(self, base_url, non_existent):
        """
        :param base_url: The base URL we want to mutate
        :param non_existent: HTTP response body for non-existent response
        :yield: Tests for all the user directories, tuples containing:
                    - URL with the user path
                    - User
                    - User description
                    - User tag, one of: OS, APPLICATION, EMAIL_TAG, COMMON_TAG
                    - HTTP response body for non-existent response
        """
        for user_desc, user, user_tag in self._get_users():
            for mutated_url in self._create_urls(base_url, user):
                yield mutated_url, user, user_desc, user_tag, non_existent

    def _create_urls(self, base_url, user):
        """
        Append the users to the URL.

        :param url: The original url
        :param user: The username for which we want to generate the URLs
        :return: A list of URL objects with the username appended.
        """
        for _format in {'/%s/', '/~%s/'}:
            yield base_url.url_join(_format % user)

    def _get_users(self):
        """
        :return: All usernames collected by other plugins and from DBs
        """
        for tag in {OS, APPLICATION}:
            for user_desc, user in get_users_from_csv(tag):
                yield user_desc, user, tag

        for user in self.COMMON_USERS:
            yield self.COMMON_USER_DESC, user, self.COMMON_TAG

        for email_kb in kb.kb.get('emails', 'emails'):
            yield self.EMAIL_USER_DESC, email_kb['user'], self.EMAIL_TAG

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins that should be run before
                 the current one.
        """
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
