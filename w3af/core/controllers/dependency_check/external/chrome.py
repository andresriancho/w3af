"""
chrome.py

Copyright 2018 Andres Riancho

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
from w3af.core.controllers.misc.which import which
from w3af.core.controllers.process.timeout import SubProcessWithTimeout


def chrome_is_installed():
    """
    :return: True if Google Chrome is installed and we were able to parse the version.
    """
    chrome_path = get_chrome_path()
    if chrome_path is not None:
        return True

    return False


def get_chrome_path():
    paths_to_chrome = []

    chrome_binaries = [
        'chromium',
        'chromium-browser',
        'google-chrome',
        'google-chrome-stable'
    ]

    for chrome_binary in chrome_binaries:
        paths_to_chrome.extend(which(chrome_binary))

    if not paths_to_chrome:
        return None

    for path_to_chrome in paths_to_chrome:

        cmd = [path_to_chrome, '--version']
        timeout_process = SubProcessWithTimeout(cmd)

        timeout_process.run(timeout=2)
        if timeout_process.returncode != 0:
            continue

        output = timeout_process.stdout
        output = output.strip()

        # Chromium 66.0.3359.181 Built on Ubuntu , running on Ubuntu 18.04
        if 'Chromium ' in output:
            return path_to_chrome

        # Google Chrome 67.0.3396.99
        if 'Google Chrome' in output:
            return path_to_chrome

    return None


def get_chrome_version():
    path_to_chrome = get_chrome_path()
    cmd = [path_to_chrome, '--version']
    timeout_process = SubProcessWithTimeout(cmd)

    timeout_process.run(timeout=2)
    if timeout_process.returncode != 0:
        return None

    version = timeout_process.stdout
    version = version.strip()

    for line in version.split('\n'):
        if line.startswith('Chromium'):
            return line

        if line.startswith('Google'):
            return line

    return version
