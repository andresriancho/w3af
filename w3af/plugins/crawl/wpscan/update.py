#!/usr/bin/env python

"""
update.py

Copyright 2015 Andres Riancho

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
import sys
import subprocess


URL = 'http://plugins.svn.wordpress.org/'
PLUGIN_FILE = 'w3af/plugins/crawl/wpscan/plugins.txt'
DOWNLOAD_CMD = 'curl -sL %s'

def download():
    print('Downloading HTML file...')
    return subprocess.check_output(DOWNLOAD_CMD % (URL,), shell=True)

def extract_names(html):
    with open(PLUGIN_FILE, 'w') as f:
        for line in html.splitlines():
            if line.strip().startswith("<li><a href="):
                f.write(re.sub("<[^<]+>", "", line).strip().rstrip('/') + '\n')
    print('done')

if __name__ == '__main__':
    html = download()
    extract_names(html)
