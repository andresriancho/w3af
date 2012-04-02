# -*- encoding: utf-8 -*-

from test_data import HTTP_RESPONSE, SQL_ERRORS
from re_multire import re_multire
from esmre_multire import esmre_multire

import re
import unittest


class TestMultiRe(unittest.TestCase):

    def __init__(self, testname):
        super(TestMultiRe, self).__init__(testname)
        self.klass = esmre_multire
                
    def test_simplest(self):
        re_list = ['123','456','789']
        mre = self.klass( re_list )
        
        result = mre.query( '456' )
        self.assertEqual(1, len(result))
        self.assertEqual('456', result[0][1])
        
        result = mre.query( '789' )
        self.assertEqual(1, len(result))
        self.assertEqual('789', result[0][1])

    def test_re(self):
        re_list = ['123.*456','abc.*def']
        mre = self.klass( re_list )
        result = mre.query( '456' )
        self.assertEqual(0, len(result))
        self.assertEqual([], result)
        
        result = mre.query( '123a456' )
        self.assertEqual(1, len(result))
        self.assertEqual('123.*456', result[0][1])
        
        result = mre.query( 'abcAAAdef' )
        self.assertEqual(1, len(result))
        self.assertEqual('abc.*def', result[0][1])

    def test_re_with_obj(self):
        re_list = [ ('123.*456', None, None) , ('abc.*def', 1, 2) ]
        mre = self.klass( re_list )
        
        result = mre.query( '123A456' )
        self.assertEqual(1, len(result))
        self.assertEqual('123.*456', result[0][1])
        self.assertEqual(None, result[0][3])
        self.assertEqual(None, result[0][4])
        
        result = mre.query( 'abcAAAdef' )
        self.assertEqual(1, len(result))
        self.assertEqual('abc.*def', result[0][1])
        self.assertEqual(1, result[0][3])
        self.assertEqual(2, result[0][4])

    def test_re_flags(self):
        re_list = ['123.*456','abc.*def']
        mre = self.klass( re_list, re.IGNORECASE )
        
        result = mre.query( 'ABC3def' )
        self.assertEqual(1, len(result))
        self.assertEqual('abc.*def', result[0][1])

    def test_unicode_re(self):
        re_list = [u'ñ', u'ý']
        mre = self.klass( re_list )
        
        result = mre.query( 'abcn' )
        self.assertEqual(0, len(result))
        self.assertEqual([], result)
        
        result = mre.query( 'abcñ' )
        self.assertEqual(1, len(result))
        self.assertEqual('ñ', result[0][1])

    def test_unicode_query(self):
        re_list = [u'abc', u'def']
        mre = self.klass( re_list )
        
        result = mre.query( 'abcñ' )
        self.assertEqual(1, len(result))
        self.assertEqual('abc', result[0][1])
        
        result = mre.query( 'abc\\x00def' )
        self.assertEqual(2, len(result))
        self.assertEqual('abc', result[0][1])
        self.assertEqual('def', result[1][1])

    def test_special_char(self):
        re_list = [u'\x00']
        mre = self.klass( re_list )
        
        result = mre.query( 'abc\x00def' )
        self.assertEqual(1, len(result))
        self.assertEqual('\x00', result[0][1])

if __name__ == '__main__':
    unittest.main()