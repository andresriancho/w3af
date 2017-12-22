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
import sys
import subprocess
import zipfile

URL = 'https://github.com/wpscanteam/wpscan/raw/master/data.zip'
ZIP_FILE = 'w3af/plugins/crawl/wpscan/data.zip'
DATA_DIR = 'w3af/plugins/crawl/wpscan/data'
JSON_FILE = 'w3af/plugins/crawl/wpscan/plugins.json'
DOWNLOAD_CMD = 'curl -sL %s > %s'

def download():
    print('Downloading ZIP file...')
    subprocess.check_call(DOWNLOAD_CMD % (URL, ZIP_FILE), shell=True)

def unpack_json():
    print('Extracting JSON file...')
    try:
        os.stat(DATA_DIR)
    except OSError:
        os.mkdir(DATA_DIR)
    _wpscan_data_zip = zipfile.ZipFile(ZIP_FILE)
    _wpscan_data_zip.extract('data/plugins.json', os.path.join(DATA_DIR, '..'))
    os.rename(os.path.join(DATA_DIR, 'plugins.json'), JSON_FILE)
    print('done')

if __name__ == '__main__':
    download()
    unpack_json()
    os.unlink(ZIP_FILE)
    os.rmdir(DATA_DIR)
