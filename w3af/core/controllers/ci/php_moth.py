"""
php_moth.py

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

HTTP_PHP_MOTH = '/tmp/php-moth.txt'
DEFAULT_PHP_MOTH = 'php_moth-fallback:80'


def get_php_moth_http(path='/'):
    try:
        php_moth_netloc = file(HTTP_PHP_MOTH).read().strip()
    except IOError:
        php_moth_netloc = DEFAULT_PHP_MOTH

    return 'http://%s%s' % (php_moth_netloc, path)


