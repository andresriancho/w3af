"""
api_process.py

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
import subprocess
import requests
from hashlib import sha512
import time
import sys
import os

from w3af import ROOT_PATH
from w3af.core.controllers.misc.get_unused_port import get_unused_port


def start_api():
    """
    Start the REST API server in 127.0.0.1 on any random port
    :return:
        * Process (so that I can kill() it later)
        * Port
        * URL
    """
    port = get_unused_port()
    dev_null = open(os.devnull, 'w')

    w3af_api_path = os.path.abspath(os.path.join(ROOT_PATH, '..'))
    python_executable = sys.executable
    api_auth = ('admin', 'unittests')

    cmd = [python_executable,
           'w3af_api',
           '-p',
           sha512(api_auth[1]).hexdigest(),
           '127.0.0.1:%s' % port]

    process = subprocess.Popen(cmd,
                               stdout=dev_null,
                               stderr=subprocess.STDOUT,
                               preexec_fn=os.setsid,
                               cwd=w3af_api_path)

    api_url = 'https://127.0.0.1:%s' % port

    # Now we wait until the API is ready to answer requests
    for i in xrange(75):
        time.sleep(0.5)

        try:
            response = requests.get(api_url, auth=api_auth, verify=False)
        except:
            if process.pid is None and i > 25:
                raise RuntimeError('Failed to start the REST API service')
        else:
            if response.status_code in (200, 404, 401):
                break
    else:
        raise RuntimeError('Timed out waiting for REST API service at %s' % api_url)

    return process, port, api_url, api_auth
