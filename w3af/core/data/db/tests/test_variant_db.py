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

from w3af.core.controllers.misc.temp_dir import create_temp_dir
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.utils.form_params import FormParameters
from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.factory import dc_from_form_params
from w3af.core.data.dc.generic.kv_container import KeyValueContainer
from w3af.core.data.parsers.url import URL
from w3af.core.data.db.variant_db import (VariantDB, PARAMS_MAX_VARIANTS,
                                          PATH_MAX_VARIANTS, FILENAME_TOKEN,
                                          PATH_TOKEN)


def fr(url):
    # shortcut
    return FuzzableRequest(url)


class TestVariantDB(unittest.TestCase):

    def setUp(self):
        create_temp_dir()
        self.vdb = VariantDB()

    def test_db_int(self):
        url_fmt = 'http://w3af.org/foo.htm?id=%s'

        for i in xrange(PARAMS_MAX_VARIANTS):
            url = URL(url_fmt % i)
            self.assertTrue(self.vdb.append(fr(url)))

        extra_url = URL(url_fmt % (PARAMS_MAX_VARIANTS + 1,))
        self.assertFalse(self.vdb.append(fr(extra_url)))

    def test_db_int_int(self):
        url_fmt = 'http://w3af.org/foo.htm?id=%s&bar=1'

        for i in xrange(PARAMS_MAX_VARIANTS):
            url = URL(url_fmt % i)
            self.assertTrue(self.vdb.append(fr(url)))

        extra_url = URL(url_fmt % (PARAMS_MAX_VARIANTS + 1,))
        self.assertFalse(self.vdb.append(fr(extra_url)))

    def test_db_int_int_var(self):
        url_fmt = 'http://w3af.org/foo.htm?id=%s&bar=%s'

        for i in xrange(PARAMS_MAX_VARIANTS):
            url = URL(url_fmt % (i, i))
            self.assertTrue(self.vdb.append(fr(url)))

        url = URL(url_fmt % (PARAMS_MAX_VARIANTS + 1, PARAMS_MAX_VARIANTS + 1))
        self.assertFalse(self.vdb.append(fr(url)))

    def test_db_int_str(self):
        url_fmt = 'http://w3af.org/foo.htm?id=%s&bar=%s'

        for i in xrange(PARAMS_MAX_VARIANTS):
            url = URL(url_fmt % (i, 'abc' * i))
            self.assertTrue(self.vdb.append(fr(url)))

        url = URL(url_fmt % (PARAMS_MAX_VARIANTS + 1,
                             'abc' * (PARAMS_MAX_VARIANTS + 1)))
        self.assertFalse(self.vdb.append(fr(url)))

    def test_db_int_str_then_int_int(self):
        url_fmt = 'http://w3af.org/foo.htm?id=%s&bar=%s'

        # Add (int, str)
        for i in xrange(PARAMS_MAX_VARIANTS):
            url = URL(url_fmt % (i, 'abc' * i))
            self.assertTrue(self.vdb.append(fr(url)))

        # Please note that in this case I'm asking for (int, int) and I added
        # (int, str) before
        url = URL(url_fmt % (PARAMS_MAX_VARIANTS + 1, PARAMS_MAX_VARIANTS + 1))
        self.assertTrue(self.vdb.append(fr(url)))

        # Add (int, int)
        for i in xrange(PARAMS_MAX_VARIANTS):
            url = URL(url_fmt % (i, i))
            self.assertTrue(self.vdb.append(fr(url)))

        url = URL(url_fmt % (PARAMS_MAX_VARIANTS + 1, PARAMS_MAX_VARIANTS + 1))
        self.assertFalse(self.vdb.append(fr(url)))

    def test_clean_fuzzable_request_simple(self):
        u = 'http://w3af.org/'
        s = self.vdb._clean_fuzzable_request(fr(URL(u)))
        e = u'(GET)-http://w3af.org/'
        self.assertEqual(s, e)

    def test_clean_fuzzable_request_file(self):
        u = 'http://w3af.org/index.php'
        s = self.vdb._clean_fuzzable_request(fr(URL(u)))
        e = u'(GET)-http://w3af.org/%s.php' % FILENAME_TOKEN
        self.assertEqual(s, e)

    def test_clean_fuzzable_request_directory_file(self):
        u = 'http://w3af.org/foo/index.php'
        s = self.vdb._clean_fuzzable_request(fr(URL(u)))
        e = u'(GET)-http://w3af.org/foo/%s.php' % FILENAME_TOKEN
        self.assertEqual(s, e)

    def test_clean_fuzzable_request_directory_file_int(self):
        u = 'http://w3af.org/foo/index.php?id=2'
        s = self.vdb._clean_fuzzable_request(fr(URL(u)))
        e = u'(GET)-http://w3af.org/foo/index.php?id=number'
        self.assertEqual(s, e)

    def test_clean_fuzzable_request_int(self):
        u = 'http://w3af.org/index.php?id=2'
        s = self.vdb._clean_fuzzable_request(fr(URL(u)))
        e = u'(GET)-http://w3af.org/index.php?id=number'
        self.assertEqual(s, e)

    def test_clean_fuzzable_request_int_str(self):
        u = 'http://w3af.org/index.php?id=2&foo=bar'
        s = self.vdb._clean_fuzzable_request(fr(URL(u)))
        e = u'(GET)-http://w3af.org/index.php?id=number&foo=string'
        self.assertEqual(s, e)

    def test_clean_fuzzable_request_int_str_empty(self):
        u = 'http://w3af.org/index.php?id=2&foo=bar&spam='
        s = self.vdb._clean_fuzzable_request(fr(URL(u)))
        e = u'(GET)-http://w3af.org/index.php?id=number&foo=string&spam=string'
        self.assertEqual(s, e)

    def test_clean_fuzzable_request_directory_file_no_params(self):
        u = 'http://w3af.org/foo/index.php'
        s = self.vdb._clean_fuzzable_request(fr(URL(u)))
        e = u'(GET)-http://w3af.org/foo/%s.php' % FILENAME_TOKEN
        self.assertEqual(s, e)

    def test_clean_fuzzable_request_directory(self):
        u = 'http://w3af.org/foo/'
        s = self.vdb._clean_fuzzable_request(fr(URL(u)))
        e = u'(GET)-http://w3af.org/%s/' % PATH_TOKEN
        self.assertEqual(s, e)

    def test_clean_fuzzable_request_directory_parent_path(self):
        u = 'http://w3af.org/spam/foo/'
        s = self.vdb._clean_fuzzable_request(fr(URL(u)))
        e = u'(GET)-http://w3af.org/spam/%s/' % PATH_TOKEN
        self.assertEqual(s, e)

    def test_clean_form_fuzzable_request(self):
        fr = FuzzableRequest(URL("http://www.w3af.com/"),
                             headers=Headers([('Host', 'www.w3af.com')]),
                             method='POST',
                             post_data=KeyValueContainer(init_val=[('data', ['23'])]))

        expected = u'(POST)-http://www.w3af.com/!data=number'
        self.assertEqual(self.vdb._clean_fuzzable_request(fr), expected)

    def test_clean_form_fuzzable_request_form(self):
        form_params = FormParameters()
        form_params.add_input([("name", "username"), ("value", "abc")])
        form_params.add_input([("name", "address"), ("value", "")])
        form_params.set_action(URL('http://example.com/?id=1'))
        form_params.set_method('post')

        form = dc_from_form_params(form_params)

        fr = FuzzableRequest.from_form(form)

        expected = u'(POST)-http://example.com/' \
                   u'?id=number!username=string&address=string'
        self.assertEqual(self.vdb._clean_fuzzable_request(fr), expected)

    def test_db_many_files_in_root(self):
        url_fmt = 'http://w3af.org/foo%s.htm'

        for i in xrange(PATH_MAX_VARIANTS):
            url = URL(url_fmt % i)
            self.assertTrue(self.vdb.append(fr(url)))

        extra_url = URL(url_fmt % (PATH_MAX_VARIANTS + 1,))
        self.assertFalse(self.vdb.append(fr(extra_url)))

    def test_db_many_files_in_root_without_extension(self):
        url_fmt = 'http://w3af.org/foo%s'

        for i in xrange(PATH_MAX_VARIANTS):
            url = URL(url_fmt % i)
            self.assertTrue(self.vdb.append(fr(url)))

        extra_url = URL(url_fmt % (PATH_MAX_VARIANTS + 1,))
        self.assertFalse(self.vdb.append(fr(extra_url)))

    def test_db_many_files_different_extensions_in_root(self):
        url_fmt = 'http://w3af.org/foo%s.htm'

        for i in xrange(PATH_MAX_VARIANTS):
            url = URL(url_fmt % i)
            self.assertTrue(self.vdb.append(fr(url)))

        extra_url = URL(url_fmt % (PATH_MAX_VARIANTS + 1,))
        self.assertFalse(self.vdb.append(fr(extra_url)))

        #
        #   Now a different extension
        #
        url_fmt = 'http://w3af.org/foo%s.jpeg'

        for i in xrange(PATH_MAX_VARIANTS):
            url = URL(url_fmt % i)
            self.assertTrue(self.vdb.append(fr(url)))

        extra_url = URL(url_fmt % (PATH_MAX_VARIANTS + 1,))
        self.assertFalse(self.vdb.append(fr(extra_url)))

    def test_db_many_paths_in_root(self):
        url_fmt = 'http://w3af.org/foo%s/'

        for i in xrange(PATH_MAX_VARIANTS):
            url = URL(url_fmt % i)
            self.assertTrue(self.vdb.append(fr(url)))

        extra_url = URL(url_fmt % (PATH_MAX_VARIANTS + 1,))
        self.assertFalse(self.vdb.append(fr(extra_url)))

    def test_db_many_paths_in_other_directories(self):
        url_fmt = 'http://w3af.org/foo/bar%s/'

        for i in xrange(PATH_MAX_VARIANTS):
            url = URL(url_fmt % i)
            self.assertTrue(self.vdb.append(fr(url)))

        extra_url = URL(url_fmt % (PATH_MAX_VARIANTS + 1,))
        self.assertFalse(self.vdb.append(fr(extra_url)))

        #
        #   Now a different parent directory
        #
        url_fmt = 'http://w3af.org/spam/bar%s/'

        for i in xrange(PATH_MAX_VARIANTS):
            url = URL(url_fmt % i)
            self.assertTrue(self.vdb.append(fr(url)))

        extra_url = URL(url_fmt % (PATH_MAX_VARIANTS + 1,))
        self.assertFalse(self.vdb.append(fr(extra_url)))

    def test_db_many_files_other_directories(self):
        url_fmt = 'http://w3af.org/spam/foo%s.htm'

        for i in xrange(PATH_MAX_VARIANTS):
            url = URL(url_fmt % i)
            self.assertTrue(self.vdb.append(fr(url)))

        extra_url = URL(url_fmt % (PATH_MAX_VARIANTS + 1,))
        self.assertFalse(self.vdb.append(fr(extra_url)))

        #
        #   Now a different parent path and the same extension
        #
        url_fmt = 'http://w3af.org/eggs/foo%s.htm'

        for i in xrange(PATH_MAX_VARIANTS):
            url = URL(url_fmt % i)
            self.assertTrue(self.vdb.append(fr(url)))

        extra_url = URL(url_fmt % (PATH_MAX_VARIANTS + 1,))
        self.assertFalse(self.vdb.append(fr(extra_url)))

    def test_db_many_files_different_path_length_directories(self):
        url_fmt = 'http://w3af.org/spam/foo%s.htm'

        for i in xrange(PATH_MAX_VARIANTS):
            url = URL(url_fmt % i)
            self.assertTrue(self.vdb.append(fr(url)))

        extra_url = URL(url_fmt % (PATH_MAX_VARIANTS + 1,))
        self.assertFalse(self.vdb.append(fr(extra_url)))

        #
        #   Now a different parent path and the same extension
        #
        #   Note the /bar/ here! This is what makes this test different
        url_fmt = 'http://w3af.org/eggs/bar/foo%s.htm'

        for i in xrange(PATH_MAX_VARIANTS):
            url = URL(url_fmt % i)
            self.assertTrue(self.vdb.append(fr(url)))

        extra_url = URL(url_fmt % (PATH_MAX_VARIANTS + 1,))
        self.assertFalse(self.vdb.append(fr(extra_url)))

    def test_db_same_without_qs(self):
        url = URL('http://w3af.org/spam/foo.htm')

        self.assertTrue(self.vdb.append(fr(url)))
        self.assertFalse(self.vdb.append(fr(url)))

    def test_db_same_with_qs(self):
        url = URL('http://w3af.org/spam/foo.htm?id=2&abc=333')

        self.assertTrue(self.vdb.append(fr(url)))
        self.assertFalse(self.vdb.append(fr(url)))
