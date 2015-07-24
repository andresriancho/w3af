"""
sqlmap_testenv.py

Copyright 2014 Andres Riancho

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

HTTP_SQLMAP_TESTENV = '/tmp/sqlmap-testenv.txt'
DEFAULT_SQLMAP_TESTENV = 'sqlmap-testenv-fallback:80'


def get_sqlmap_testenv_http(path='/'):
    try:
        sqlmap_testenv_netloc = file(HTTP_SQLMAP_TESTENV).read().strip()
    except IOError:
        sqlmap_testenv_netloc = DEFAULT_SQLMAP_TESTENV

    return 'http://%s%s' % (sqlmap_testenv_netloc, path)

