"""
cleanup_bug_report.py

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
import re
import os

import w3af.core.data.kb.config as cf


EXPLICIT_CRASH_REPORT = os.environ.get('EXPLICIT_CRASH_REPORT', '0') == '1'


def cleanup_bug_report(_input):
    """
    :return: A string that contains a "clean" bug report. The function will
             remove all references to the target site, operating system user
             name, etc.
    """
    # In some scenarios users don't need to cleanup the bug reports. Use an
    # environment variable to configure this setting:
    #
    #    EXPLICIT_CRASH_REPORT=1 ./w3af_console -s script.w3af
    #
    # Not using a misc-setting or similar since this is a very rare scenario
    # and it would clutter the misc-settings
    if EXPLICIT_CRASH_REPORT:
        return _input

    user_re = '/home/(.*?)/'
    user_re_win = 'C:\\\\Documents and Settings\\\\(.*?)\\\\'

    _input = re.sub(user_re, '/home/user/', _input)
    _input = re.sub(user_re_win, 'C:/user/', _input)

    targets = cf.cf.get('targets')
    if targets is not None:
        domains = [url.get_domain() for url in targets]
        paths = [url.get_path() for url in targets if len(url.get_path()) >= 3]
        
        for domain in domains:
            _input = _input.replace(domain, 'domain')

        for path in paths:
            _input = _input.replace(path, '/path/foo/')

    return _input
