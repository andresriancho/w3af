'''
test_extrusion_scanner.py

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
import unittest
import commands

from nose.plugins.skip import SkipTest
from nose.plugins.attrib import attr

import core.data.kb.config as cf

from core.controllers.extrusionScanning.extrusionScanner import extrusionScanner
from core.controllers.w3afException import w3afException


class TestExtrusionScanner(unittest.TestCase):
    '''
    Test the extrusion scanner's basic features.
    '''
    def test_basic(self):
        es = extrusionScanner(commands.getoutput)
        
        self.assertTrue( es.canScan() )
        
        self.assertTrue( es.estimateScanTime() >= 8 )
        
        self.assertTrue( es.isAvailable(54545, 'tcp') )
    
    @attr('root')
    def test_scan(self):
        # FIXME: This unittest will only work in Linux
        cf.cf.save( 'interface', 'lo' )
        cf.cf.save( 'localAddress', '127.0.0.1' )
        es = extrusionScanner(commands.getoutput)
        
        try:
            inbound_port = es.get_inbound_port()
        except w3afException:
            raise SkipTest('This test requires root privileges.')
        else: 
            self.assertEquals( inbound_port , 8080 )
    
    def test_zzz(self):
        '''
        Can't stop finding nosetests errors! It looks like SkipTest works except
        in the case where it is the last test discovered!
        '''
        pass