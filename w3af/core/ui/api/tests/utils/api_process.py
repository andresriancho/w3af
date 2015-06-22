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
import time
import os

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
    process = subprocess.Popen('python w3af_api 127.0.0.1:%s' % port,
                               shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               preexec_fn=os.setsid)

    api_url = 'http://127.0.0.1:%s' % port

    # Now we wait until the API is ready to answer requests
    for _ in xrange(10):
        time.sleep(0.5)
        try:
            response = requests.get(api_url)
        except:
            continue
        else:
            if response.status_code == 404:
                break

    return process, port, api_url