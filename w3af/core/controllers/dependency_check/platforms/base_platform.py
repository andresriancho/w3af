"""
platform.py

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
from ..requirements import CORE_PIP_PACKAGES, GUI_PIP_PACKAGES, CORE, GUI
from ..external.retirejs import retirejs_is_installed
from ..external.chrome import chrome_is_installed


class Platform(object):
    """
    Simple base class for defining platforms/operating systems for dependency
    checks.
    """
    PIP_PACKAGES = {CORE: CORE_PIP_PACKAGES,
                    GUI: GUI_PIP_PACKAGES}

    SYSTEM_PACKAGES = {CORE: [],
                       GUI: []}

    EXTERNAL_COMMAND_HANDLERS = ['retirejs_handler',
                                 'chrome_handler']

    def is_current_platform(self):
        raise NotImplementedError

    def os_package_is_installed(self, package_name):
        raise NotImplementedError

    def after_hook(self):
        pass

    def get_missing_external_commands(self):
        instructions = []

        for handler_name in self.EXTERNAL_COMMAND_HANDLERS:
            handler = getattr(self, handler_name)
            instructions.extend(handler())

        return instructions

    def retirejs_handler(self):
        if retirejs_is_installed():
            return []

        return ['npm install -g retire@2.0.3',
                'npm update -g retire']

    def chrome_handler(self):
        if chrome_is_installed():
            return []

        return [
            '#',
            '# Chromium browser binary is missing. Please install Chromium or',
            '# Google Chrome.',
            '#',
            '# w3af works with both Chromium and Google Chrome. You can either',
            '# install Chromium using your operating system package manager or',
            '# browse to Google Chrome site and install it manually.',
            '#',
            '# This message is shown because w3af does not know the commands to',
            '# install Chromium via the command line in your platform. If you know',
            '# how to, please submit the steps here:',
            '# ',
            '#      https://github.com/andresriancho/w3af/issues/17099',
            '# ',
            '# And we will include the commands in the next w3af release.',
            '#',
        ]
