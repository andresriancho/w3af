"""
master.py

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
# TODO: This is just a mock which in the future will allow us to have multiple
#       running scans at the same time, results for each, etc. Now we'll only
#       store one scan
#
# Store integer IDs as keys and ScanInfo instances as values
SCANS = {}


class ScanInfo(object):
    def __init__(self):
        self.w3af_core = None
        self.output = None
        self.exception = None
        self.finished = False
        self.target_urls = None
        self.profile_path = None

    def cleanup(self):
        if self.w3af_core is not None:
            self.w3af_core.cleanup()

        if self.output is not None:
            self.output.cleanup()
