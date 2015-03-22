"""
test_vulns.py

Copyright 2006 Andres Riancho

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
import unittest

from nose.plugins.attrib import attr

from w3af import ROOT_PATH
from w3af.core.data.constants.vulns import VULNS
from w3af.core.controllers.ci.constants import ARTIFACTS_DIR

       
class TestVulnsConstants(unittest.TestCase):
    
    LOCATION = os.path.join(ROOT_PATH, 'core', 'data', 'constants', 'vulns.py')
    
    def test_no_duplicated_ids(self):
        # Just skip the entire license header
        vulns_file = file(self.LOCATION) 
        for _ in xrange(21):
            vulns_file.readline()
            
        vuln_id_list = re.findall('\d+', vulns_file.read())
        filtered = set()
        dups = set()
        
        for vuln_id in vuln_id_list:
            if vuln_id in filtered:
                dups.add(vuln_id)
            
            filtered.add(vuln_id)
            
        self.assertEquals(set([]), dups)
    
    def test_no_empty(self):
        items = VULNS.items()
        empty_values = set([(key, val) for (key, val) in items if not val])
        self.assertEqual(set([]), empty_values)

    @attr('ci_fails')
    def test_vuln_updated(self):
        """
        Each time we call Info.set_name during a test (and only during tests,
        not run when the user is running w3af) we check if the name of the
        vulnerability being set is actually in the vuln.py database or not,
        if it's not we append it to a file called /tmp/missing-vulndb.txt

        This test asserts that the file:
            * Doesn't exist
            * Is empty
            * Fail if not

        Since we want to run this test at the end, we tag it as ci_fails for the
        main running to ignore it, but then we run it manually from circle.yml
        """
        missing = os.path.join(ARTIFACTS_DIR, 'missing-vulndb.txt')

        if not os.path.exists(missing):
            # Perfect!
            return

        missing_list = []
        for line in file(missing):
            line = line.strip()

            if not line:
                continue

            missing_list.append(line)

        self.maxDiff = None
        self.assertEqual(missing_list, [])