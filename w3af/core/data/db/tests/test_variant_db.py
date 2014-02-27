"""
test_variant_db.py

Copyright 2012 Andres Riancho

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

from w3af.core.data.parsers.url import URL
from w3af.core.data.db.variant_db import VariantDB
from w3af.core.controllers.misc.temp_dir import create_temp_dir


class TestVariantDB(unittest.TestCase):

    def setUp(self):
        create_temp_dir()
        self.vdb = VariantDB()

    def test_db_int(self):
        url_fmt = 'http://w3af.org/foo.htm?id=%s'
        _max = 5

        for i in xrange(_max):
            url = URL(url_fmt % i)
            self.assertTrue(self.vdb.need_more_variants(url))
            self.vdb.append(url)

        self.assertFalse(
            self.vdb.need_more_variants(URL(url_fmt % (_max + 1,))))

    def test_db_int_int(self):
        url_fmt = 'http://w3af.org/foo.htm?id=%s&bar=1'
        _max = 5

        for i in xrange(_max):
            url = URL(url_fmt % i)
            self.assertTrue(self.vdb.need_more_variants(url))
            self.vdb.append(url)

        self.assertFalse(
            self.vdb.need_more_variants(URL(url_fmt % (_max + 1,))))

    def test_db_int_int_var(self):
        url_fmt = 'http://w3af.org/foo.htm?id=%s&bar=%s'
        _max = 5

        for i in xrange(_max):
            url = URL(url_fmt % (i, i))
            self.assertTrue(self.vdb.need_more_variants(url))
            self.vdb.append(url)

        self.assertFalse(
            self.vdb.need_more_variants(URL(url_fmt % (_max + 1, _max + 1))))

    def test_db_int_str(self):
        url_fmt = 'http://w3af.org/foo.htm?id=%s&bar=%s'
        _max = 5

        for i in xrange(_max):
            url = URL(url_fmt % (i, 'abc' * i))
            self.assertTrue(self.vdb.need_more_variants(url))
            self.vdb.append(url)

        self.assertFalse(self.vdb.need_more_variants(
            URL(url_fmt % (_max + 1, 'abc' * (_max + 1)))))

    def test_db_int_str_then_int_int(self):
        url_fmt = 'http://w3af.org/foo.htm?id=%s&bar=%s'
        _max = 5

        # Add (int, str)
        for i in xrange(_max):
            url = URL(url_fmt % (i, 'abc' * i))
            self.assertTrue(self.vdb.need_more_variants(url))
            self.vdb.append(url)

        # Please note that in this case I'm asking for (int, int) and I added
        # (int, str) before
        self.assertTrue(
            self.vdb.need_more_variants(URL(url_fmt % (_max + 1, _max + 1))))

        # Add (int, int)
        for i in xrange(_max):
            url = URL(url_fmt % (i, i))
            self.assertTrue(self.vdb.need_more_variants(url))
            self.vdb.append(url)

        self.assertFalse(
            self.vdb.need_more_variants(URL(url_fmt % (_max + 1, _max + 1))))

    def test_clean_reference_simple(self):
        self.assertEqual(self.vdb._clean_reference(URL('http://w3af.org/')),
                         u'http://w3af.org/')

    def test_clean_reference_file(self):
        self.assertEqual(
            self.vdb._clean_reference(URL('http://w3af.org/index.php')),
            u'http://w3af.org/index.php')

    def test_clean_reference_directory_file(self):
        self.assertEqual(
            self.vdb._clean_reference(URL('http://w3af.org/foo/index.php')),
                                         u'http://w3af.org/foo/index.php')

    def test_clean_reference_directory_file_int(self):
        self.assertEqual(
            self.vdb._clean_reference(URL('http://w3af.org/foo/index.php?id=2')),
                                      u'http://w3af.org/foo/index.php?id=number')

    def test_clean_reference_int(self):
        self.assertEqual(
            self.vdb._clean_reference(URL('http://w3af.org/index.php?id=2')),
            u'http://w3af.org/index.php?id=number')

    def test_clean_reference_int_str(self):
        self.assertEqual(
            self.vdb._clean_reference(
                URL('http://w3af.org/index.php?id=2&foo=bar')),
            u'http://w3af.org/index.php?id=number&foo=string')

    def test_clean_reference_int_str_empty(self):
        self.assertEqual(
            self.vdb._clean_reference(
                URL('http://w3af.org/index.php?id=2&foo=bar&spam=')),
            u'http://w3af.org/index.php?id=number&foo=string&spam=string')
