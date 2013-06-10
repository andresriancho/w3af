'''
test_users.py

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
'''
from w3af.plugins.attack.payloads.payloads.tests.payload_test_helper import PayloadTestHelper
from w3af.plugins.attack.payloads.payload_handler import exec_payload


class test_users(PayloadTestHelper):

    EXPECTED_RESULT = {
        u'backup': {'desc': u'backup',
                    'home': u'/var/backups/',
                    'shell': u'/bin/sh'},
        u'bin': {'desc': u'bin', 'home': u'/bin/', 'shell': u'/bin/sh'},
        u'daemon': {'desc': u'daemon', 'home': u'/usr/sbin/', 'shell': u'/bin/sh'},
        u'games': {'desc': u'games', 'home': u'/usr/games/', 'shell': u'/bin/sh'},
        u'gnats': {'desc': u'Gnats Bug-Reporting System (admin)',
                   'home': u'/var/lib/gnats/',
                   'shell': u'/bin/sh'},
        u'irc': {'desc': u'ircd', 'home': u'/var/run/ircd/', 'shell': u'/bin/sh'},
        u'landscape': {'desc': u'',
                       'home': u'/var/lib/landscape/',
                       'shell': u'/bin/false'},
        u'libuuid': {'desc': u'', 'home': u'/var/lib/libuuid/', 'shell': u'/bin/sh'},
        u'list': {'desc': u'Mailing List Manager',
                  'home': u'/var/list/',
                  'shell': u'/bin/sh'},
        u'lp': {'desc': u'lp', 'home': u'/var/spool/lpd/', 'shell': u'/bin/sh'},
        u'mail': {'desc': u'mail', 'home': u'/var/mail/', 'shell': u'/bin/sh'},
        u'man': {'desc': u'man', 'home': u'/var/cache/man/', 'shell': u'/bin/sh'},
        u'messagebus': {'desc': u'',
                        'home': u'/var/run/dbus/',
                        'shell': u'/bin/false'},
        u'moth': {'desc': u'moth', 'home': u'/home/moth/', 'shell': u'/bin/bash'},
        u'mysql': {'desc': u'MySQL Server',
                   'home': u'/nonexistent/',
                   'shell': u'/bin/false'},
        u'news': {'desc': u'news', 'home': u'/var/spool/news/', 'shell': u'/bin/sh'},
        u'nobody': {'desc': u'nobody',
                    'home': u'/nonexistent/',
                    'shell': u'/bin/sh'},
        u'proxy': {'desc': u'proxy', 'home': u'/bin/', 'shell': u'/bin/sh'},
        u'root': {'desc': u'root', 'home': u'/root/', 'shell': u'/bin/bash'},
        u'sshd': {'desc': u'',
                  'home': u'/var/run/sshd/',
                  'shell': u'/usr/sbin/nologin'},
        u'sync': {'desc': u'sync', 'home': u'/bin/', 'shell': u'/bin/sync'},
        u'sys': {'desc': u'sys', 'home': u'/dev/', 'shell': u'/bin/sh'},
        u'syslog': {'desc': u'', 'home': u'/home/syslog/', 'shell': u'/bin/false'},
        u'tomcat6': {'desc': u'',
                     'home': u'/usr/share/tomcat6/',
                     'shell': u'/bin/false'},
        u'uucp': {'desc': u'uucp', 'home': u'/var/spool/uucp/', 'shell': u'/bin/sh'},
        u'whoopsie': {'desc': u'', 'home': u'/nonexistent/', 'shell': u'/bin/false'},
        u'www-data': {'desc': u'www-data',
                      'home': u'/var/www/',
                      'shell': u'/bin/sh'},
        u'postfix': {'desc': u'postfix',
                             'home': u'/var/spool/postfix',
                             'shell': u'/bin/false'}
    }

    def test_users(self):
        result = exec_payload(self.shell, 'users', use_api=True)
        self.assertEquals(set(self.EXPECTED_RESULT.keys()), set(result.keys()))
