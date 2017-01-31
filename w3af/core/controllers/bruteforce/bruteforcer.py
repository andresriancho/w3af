"""
bruteforcer.py

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

from itertools import chain

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.misc.make_leet import make_leet
from w3af.core.controllers.misc.itertools_toolset import unique_everseen


class PasswordBruteforcer(object):
    """
    This class is a helper for bruteforcing any login that provides passwords
    with an iterator API.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, url):
        self.passwd_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        'passwords.txt')
        self.l337_p4sswd = True
        self.use_profiling = True
        self.profiling_number = 50

        self._url = url

    def generator(self):
        """
        TODO: I need a way to calculate the __len__ of this generator in order
              to avoid the "iterable = list(iterable)" in pool.py
        """
        pwd_chain = chain(self._read_pwd_file(),
                          self._special_passwords(),)

        for pwd in unique_everseen(pwd_chain):
            yield pwd

            if self.l337_p4sswd:
                for pwd in unique_everseen(make_leet(pwd)):
                    yield pwd

    def _special_passwords(self):
        yield self._url.get_domain()
        yield self._url.get_root_domain()
        
        if self.use_profiling:
            for pwd in get_profiling_results(self.profiling_number):
                yield pwd

    def _read_pwd_file(self):
        for line in file(self.passwd_file):
            yield line.strip()


class UserPasswordBruteforcer(object):
    """
    This class is a helper for bruteforcing any login that provides user and
    password combinations with an iterator API.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self, url):
        # Config params for user generation
        self.users_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                       'users.txt')
        self.combo_file = ''
        self.combo_separator = ":"
        self.use_emails = True
        self.use_SVN_users = True
        self.pass_eq_user = True

        # Config params for password generation
        self.passwd_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        'passwords.txt')
        self.l337_p4sswd = True
        self.use_profiling = True
        self.profiling_number = 50

        # Internal variables
        self._url = url

    def _new_password_bruteforcer(self):
        pbf = PasswordBruteforcer(self._url)
        pbf.passwd_file = self.passwd_file
        pbf.l337_p4sswd = self.l337_p4sswd
        pbf.use_profiling = self.use_profiling
        pbf.profiling_number = self.profiling_number
        return pbf.generator()

    def generator(self):
        """
        :return: A tuple with user and password strings.

        TODO: I need a way to calculate the __len__ of this generator in order
              to avoid the "iterable = list(iterable)" in pool.py
        """
        for user, pwd in self._combo():
            yield user, pwd

        user_chain = chain(self._user_from_file(),
                           self._special_users(),)

        for user in unique_everseen(user_chain):

            if self.pass_eq_user:
                yield user, user

            yield user, ''

            for pwd in self._new_password_bruteforcer():
                yield user, pwd

    def _user_from_file(self):
        for line in file(self.users_file):
            user = line.strip()
            yield user

    def _special_users(self):
        """
        Generate special passwords from URL, password profiling, etc.
        """
        yield self._url.get_domain()

        if self.use_emails:
            emails = kb.kb.get('emails', 'emails')
            for user in [v['user'] for v in emails]:
                yield user

            emails = kb.kb.get('emails', 'emails')
            for user in [v['mail'] for v in emails]:
                yield user

        if self.use_SVN_users:
            users = kb.kb.get('svn_users', 'users')
            for user in [v['user'] for v in users]:
                yield user

        if self.use_profiling:
            for user in get_profiling_results(self.profiling_number):
                yield user

    def _combo(self):
        """
        Get the user, password combo from a file.
        """
        if not self.combo_file:
            return

        for line in file(self.combo_file):
            try:
                user, passwd = line.strip().split(self.combo_separator)
            except ValueError:
                om.out.debug('Invalid combo entry: "%s"' % line)
            else:
                yield user, passwd


def get_profiling_results(self, max_items=50):
    def sortfunc(x, y):
        return cmp(y[1], x[1])

    # pylint: disable=E1103
    kb_data = kb.kb.raw_read('password_profiling', 'password_profiling')

    if not kb_data:
        msg = ('No password profiling information collected for using during'
               ' the bruteforce process, please try to enable crawl.web_spider'
               ' and grep.password_profiling plugins and try again.')
        om.out.debug(msg)
        return []

    else:
        items = kb_data.items()
        items.sort(sortfunc)

        xlen = min(max_items, len(items))

        return [x[0] for x in items[:xlen]]
