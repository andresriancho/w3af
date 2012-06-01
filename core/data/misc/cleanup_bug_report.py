'''
cleanup_bug_report.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

import re

import core.data.kb.config as cf


def cleanup_bug_report( input ):
    '''
    @return: A string that contains a "clean" bug report. The function will remove
             all references to the target site, operating system user name, etc.
    '''
    user_re = '/home/(.*?)/'
    # TODO: Need a regex for Windows
    # TODO: Apply regex.sub
    
    targets = cf.cf.getData('targets')
    domains = [url.getDomain() for url in targets]
    paths = [url.getPath() for url in targets]
    
    for domain in domains:
        input = input.replace(domain, 'domain')

    for path in paths:
        input = input.replace(path, '/path/foo')
        
    return input
    