"""
test_latest_vulndb.py

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
import unittest
import pkg_resources

from yolk.yolklib import get_highest_version, Distributions
from yolk.pypi import CheeseShop


class TestLatestVulnDB(unittest.TestCase):
    def test_latest_vulndb(self):
        dists = Distributions()
        pkg = 'vulndb'
        found = None
        pypi = CheeseShop(False)
        all_dists = dists.get_distributions('all', pkg,
                                            dists.get_highest_installed(pkg))

        for dist, active in all_dists:
            project_name, versions = pypi.query_versions_pypi(dist.project_name)

            if versions:
                # PyPI returns them in chronological order,
                # but who knows if its guaranteed in the API?
                # Make sure we grab the highest version:
                newest = get_highest_version(versions)
                if newest != dist.version:

                    #We may have newer than what PyPI knows about

                    if pkg_resources.parse_version(dist.version) < \
                    pkg_resources.parse_version(newest):
                        found = True

        if found:
            self.assertTrue(False, 'There is a new vulndb available at pypi!')