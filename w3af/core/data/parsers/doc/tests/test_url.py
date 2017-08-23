# -*- coding: utf-8 -*-
"""
test_url.py

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
import urllib2
import cPickle
from multiprocessing.queues import SimpleQueue

from nose.plugins.skip import SkipTest

from w3af.core.data.parsers.doc.url import URL, parse_qs
from w3af.core.data.dc.query_string import QueryString
from w3af.core.data.dc.urlencoded_form import URLEncodedForm


class TestURLParser(unittest.TestCase):

    #
    #    Object instantiation test
    #
    def test_simplest_url(self):
        u = URL('http://w3af.com/foo/bar.txt')
        
        self.assertEqual(u.path, '/foo/bar.txt')
        self.assertEqual(u.scheme, 'http')
        self.assertEqual(u.get_file_name(), 'bar.txt')
        self.assertEqual(u.get_extension(), 'txt')

    def test_default_proto(self):
        """
        http is the default protocol, we can provide URLs with no proto
        """
        u = URL('w3af.com')
        self.assertEqual(u.get_domain(), 'w3af.com')
        self.assertEqual(u.get_protocol(), 'http')

    def test_websocket_proto(self):
        """
        We can also parse and handle ws and wss protocols
        """
        u = URL('ws://w3af.com')
        self.assertEqual(u.get_domain(), 'w3af.com')
        self.assertEqual(u.get_protocol(), 'ws')

    def test_websocket_secure_proto(self):
        """
        We can also parse and handle ws and wss protocols
        """
        u = URL('wss://w3af.com')
        self.assertEqual(u.get_domain(), 'w3af.com')
        self.assertEqual(u.get_protocol(), 'wss')

    def test_just_path(self):
        """
        Can't specify the path without a domain and protocol
        """
        self.assertRaises(ValueError, URL, '/')
    
    def test_no_domain(self):
        """
        But we can't specify a URL without a domain!
        """
        self.assertRaises(ValueError, URL, 'http://')
    
    def test_case_insensitive_proto(self):
        u = URL('HtTp://w3af.com/foo/bar.txt')
        self.assertEqual(u.scheme, 'http')

    def test_file_proto(self):
        u = URL('file://foo/bar.txt')
        self.assertEqual(u.scheme, 'file')
        
    def test_path_root(self):
        u = URL('http://w3af.com/')
        self.assertEqual(u.path, '/')

    def test_url_in_qs(self):
        u = URL('http://w3af.org/?foo=http://w3af.com')
        self.assertEqual(u.netloc, 'w3af.org')

    def test_url_in_filename(self):
        """
        Test https://github.com/andresriancho/w3af/issues/475

        Before the fix parsing a URL like:
            http://site.com/foo-http://external-test.com/.zip

        Returned a buggy result:
            foo-http:/external-test.com/.zip

        This is because of the "extra" http which lives in the URL and is not
        encoded. The "error" here is that the special characters in a filename
        part of a URL should be URL-encoded and in this case they are not.

        The Internet is an awful place, and we'll find this, so we better handle
        them properly.

        The issue comes from a call to urlparse.urljoin:
            >>> import urlparse
            >>> urlparse.urljoin('http://foo.com/', 'spam-bar://eggs.com')
            'spam-bar://eggs.com'

        Which lives inside the normalize_url method in URL:
            fixed_url = urlparse.urljoin(base_url, self.get_path_qs())
        """
        u = URL('http://w3af.org/foo-http://external-test.com/.zip')
        self.assertEqual(u.netloc, 'w3af.org')

    def test_invalid_encoding(self):
        self.assertRaises(ValueError, URL, 'http://w3af.org/', encoding='x-euc-jp')

    def test_invalid_no_port(self):
        self.assertRaises(ValueError, URL, "http://w3af.com:")

    def test_invalid_invalid_port(self):
        self.assertRaises(ValueError, URL, "http://w3af.com:998899")
        
    #
    #    Decode tests
    #
    def decode_get_qs(self, url_str):
        return URL(url_str).url_decode().querystring['id'][0]

    def test_decode_simple(self):
        qs_value = self.decode_get_qs(u'http://w3af.com/?id=1')
        expected = '1'
        self.assertEqual(qs_value, expected)

    def test_decode_perc_20(self):
        qs_value = self.decode_get_qs(u'http://w3af.com/?id=1%202')
        expected = u'1 2'
        self.assertEqual(qs_value, expected)

    def test_decode_space(self):
        qs_value = self.decode_get_qs(u'http://w3af.com/?id=1 2')
        expected = u'1 2'
        self.assertEqual(qs_value, expected)

    def test_decode_plus(self):
        qs_value = self.decode_get_qs(u'http://w3af.com/?id=1+2')
        expected = u'1 2'
        self.assertEqual(qs_value, expected)

    def test_decode_url_encode_plus(self):
        msg = ('There is a bug which is triggered here between URL.url_decode'
               ' and the parsing being done when creating a new URL. If you'
               ' add a "print self.querystring" at the end of URL.__init__'
               ' it shows the problem: id=1%2B2 and then id=1%202')
        raise SkipTest(msg)

        qs_value = self.decode_get_qs(u'http://w3af.com/?id=1%2B2')
        expected = u'1+2'
        self.assertEqual(qs_value, expected)

    #
    #    Encode tests
    #
    def test_encode_simple(self):
        res_str = URL(u'http://w3af.com').url_encode()
        expected = 'http://w3af.com/'
        self.assertEqual(res_str, expected)

    def test_encode_perc_20(self):
        res_str = URL(u'https://w3af.com:443/file.asp?id=1%202').url_encode()
        expected = 'https://w3af.com/file.asp?id=1%202'
        self.assertEqual(res_str, expected)

    def test_encode_space(self):
        res_str = URL(u'https://w3af.com:443/file.asp?id=1 2').url_encode()
        expected = 'https://w3af.com/file.asp?id=1%202'
        self.assertEqual(res_str, expected)

    def test_encode_plus(self):
        res_str = URL(u'https://w3af.com:443/file.asp?id=1+2').url_encode()
        expected = 'https://w3af.com/file.asp?id=1%202'
        self.assertEqual(res_str, expected)

    def test_encode_url_encode_plus(self):
        res_str = URL(u'https://w3af.com/file.asp?id=1%2B2').url_encode()
        EXPECTED = 'https://w3af.com/file.asp?id=1%2B2'
        self.assertEqual(res_str, EXPECTED)

    def test_encode_math(self):
        res_str = URL(u'http://w3af.com/x.py?ec=x*y/2==3').url_encode()
        EXPECTED = 'http://w3af.com/x.py?ec=x%2Ay%2F2%3D%3D3'
        self.assertEqual(res_str, EXPECTED)

    def test_encode_param(self):
        res_str = URL(u'http://w3af.com/x.py;id=1?y=3').url_encode()
        EXPECTED = 'http://w3af.com/x.py;id=1?y=3'
        self.assertEqual(res_str, EXPECTED)

    def test_decode_encode(self):
        """Encode and Decode should be able to run one on the result of the
        other and return the original"""
        original = URL(u'https://w3af.com:443/file.asp?id=1%202')
        decoded = original.url_decode()
        encoded = decoded.url_encode()
        self.assertEqual(original.url_encode(), encoded)

    def test_encode_decode(self):
        """Encode and Decode should be able to run one on the result of the
        other and return the original"""
        original = URL(u'https://w3af.com:443/file.asp?id=1%202')
        encoded = original.url_encode()
        decoded = URL(encoded).url_decode()
        self.assertEqual(original, decoded)
    
    #
    #    Test get_directories
    #
    def test_get_directories_path_levels_1(self):
        result = [i.url_string for i in URL('http://w3af.com/xyz/def/123/').get_directories()]
        expected = [u'http://w3af.com/xyz/def/123/',
                    u'http://w3af.com/xyz/def/',
                    u'http://w3af.com/xyz/', u'http://w3af.com/']
        self.assertEqual(result, expected)
    
    def test_get_directories_path_levels_2(self):
        result = [i.url_string for i in URL('http://w3af.com/xyz/def/').get_directories()]
        expected = [u'http://w3af.com/xyz/def/', u'http://w3af.com/xyz/',
                    u'http://w3af.com/']
        self.assertEqual(result, expected)
    
    def test_get_directories_path_levels_3(self):
        result = [i.url_string for i in URL('http://w3af.com/xyz/').get_directories()]
        expected = [u'http://w3af.com/xyz/', u'http://w3af.com/']
        self.assertEqual(result, expected)
    
    def test_get_directories_path_levels_4(self):
        result = [i.url_string for i in URL('http://w3af.com/').get_directories()]
        expected = [u'http://w3af.com/']
        self.assertEqual(result, expected)

    def test_get_directories_filename(self):
        result = [i.url_string for i in URL('http://w3af.com/def.html').get_directories()]
        expected = [u'http://w3af.com/']
        self.assertEqual(result, expected)
    
    def test_get_directories_fname_qs(self):
        expected = [u'http://w3af.com/']
        
        result = [i.url_string for i in URL('http://w3af.com/def.html?id=5').get_directories()]
        self.assertEqual(result, expected)
        
        result = [i.url_string for i in URL('http://w3af.com/def.html?id=/').get_directories()]
        self.assertEqual(result, expected)

    #
    #    Test url_join
    #
    def test_url_join_case01(self):
        u = URL('http://w3af.com/foo.bar')
        self.assertEqual(u.url_join('abc.html').url_string,
                         u'http://w3af.com/abc.html')
        
        self.assertEqual(u.url_join('/abc.html').url_string,
                         u'http://w3af.com/abc.html')
    
    def test_url_join_case02(self):
        u = URL('http://w3af.com/')
        self.assertEqual(u.url_join('/abc.html').url_string,
                         u'http://w3af.com/abc.html')
        
        self.assertEqual(u.url_join('/def/abc.html').url_string,
                         u'http://w3af.com/def/abc.html')

    def test_url_join_case03(self):
        u = URL('http://w3af.com/def/jkl/')
        self.assertEqual(u.url_join('/def/abc.html').url_string,
                         u'http://w3af.com/def/abc.html')
        
        self.assertEqual(u.url_join('def/abc.html').url_string,
                         u'http://w3af.com/def/jkl/def/abc.html')

    def test_url_join_case04(self):
        u = URL('http://w3af.com:8080/')
        self.assertEqual(u.url_join('abc.html').url_string,
                         u'http://w3af.com:8080/abc.html')
    
    def test_url_join_case05(self):
        u = URL('http://w3af.com/def/')
        self.assertEqual(u.url_join(u'тест').url_string,
                         u'http://w3af.com/def/тест')

    def test_url_join_case06(self):
        """
        Opera and Chrome behave like this. For those browsers the URL
        leads to no good, so I'm going to do the same thing. If the user
        wants to specify a URL that contains a colon he should URL
        encode it.
        """
        u = URL('http://w3af.com/')
        self.assertRaises(ValueError, u.url_join, "d:url.html")

    def test_url_join_case07(self):
        u = URL('http://w3af.com/')
        self.assertEqual(u.url_join('http://w3af.org:8080/abc.html').url_string,
                         u'http://w3af.org:8080/abc.html')

    def test_parse_qs_case01(self):
        self.assertEqual(parse_qs('id=3'),
                         QueryString([(u'id', [u'3'])]))
    
    def test_parse_qs_case02(self):
        qs = QueryString([(u'id', [u'3 1'])])
        parsed_qs = parse_qs('id=3+1')

        self.assertEqual(str(parsed_qs), str(qs))

    def test_parse_qs_case03(self):
        qs = QueryString([(u'id', [u'3 1'])])
        parsed_qs = parse_qs('id=3%201')

        self.assertEqual(str(parsed_qs), str(qs))

    def test_parse_qs_repeated_parameter_names(self):
        self.assertEqual(parse_qs('id=3&id=4'),
                         QueryString([(u'id', [u'3', u'4'])]))

    def test_url_with_repeated_parameter_names(self):
        u = URL('http://w3af.com/?id=3&id=4')
        self.assertEqual(u.get_querystring(),
                         QueryString([(u'id', [u'3', u'4'])]))

    def test_parse_qs_case04(self):
        self.assertEqual(parse_qs('id=3&ff=4&id=5'),
                         QueryString([(u'id', [u'3', u'5']),
                                      (u'ff', [u'4'])]))
    
    def test_parse_qs_case05(self):
        self.assertEqual(parse_qs('pname'),
                         QueryString([(u'pname', [u''])]))
    
    def test_parse_qs_case06(self):
        expected_parsed_url = QueryString([(u'\u9834\u82f1',
                                            [u'\u75ab\u76ca'])],
                                          encoding='euc-jp')
        self.assertEqual(parse_qs(u'%B1%D0%B1%D1=%B1%D6%B1%D7', encoding='euc-jp'),
                         expected_parsed_url)
    
    def test_parse_qs_case07(self):
        self.assertRaises(TypeError, parse_qs, QueryString())

    #
    # base_url
    #
    def test_base_url_path_fragment(self):
        u = URL('http://www.w3af.com/foo/bar.txt?id=3#foobar')
        self.assertEqual(u.base_url().url_string,
                         u'http://www.w3af.com/')

    def test_base_url_path_missing(self):
        u = URL('http://www.w3af.com')
        self.assertEqual(u.base_url().url_string,
                         u'http://www.w3af.com/')

    def test_base_url_port(self):
        u = URL('http://www.w3af.com:80/')
        self.assertEqual(u.base_url().url_string,
                         u'http://www.w3af.com/')

    def test_base_url_port_ssl(self):
        u = URL('https://www.w3af.com:443/')
        self.assertEqual(u.base_url().url_string,
                         u'https://www.w3af.com/')

    def test_base_url_port_not_default(self):
        u = URL('http://www.w3af.com:8080/')
        self.assertEqual(u.base_url().url_string,
                         u'http://www.w3af.com:8080/')

    def test_base_url_port_ssl_not_default(self):
        u = URL('https://www.w3af.com:8443/')
        self.assertEqual(u.base_url().url_string,
                         u'https://www.w3af.com:8443/')

    #
    #    normalize_url
    #
    def normalize_url_case01(self):
        u = URL('http://host.tld:80/foo/bar')
        u.normalize_url()
        self.assertEqual(u.url_string, u'http://host.tld/foo/bar')

    def normalize_url_case02(self):
        u = URL('https://host.tld:443/foo/bar')
        u.normalize_url()
        self.assertEqual(u.url_string,
                         u'https://host.tld/foo/bar')

    def normalize_url_case03(self):
        u = URL('https://host.tld:443////////////////')
        u.normalize_url()
        self.assertEqual(u.url_string,
                         u'https://host.tld/')

    def normalize_url_case04(self):
        u = URL('https://host.tld:443////////////////?id=3&bar=4')
        u.normalize_url()
        self.assertEqual(u.url_string,
                         u'https://host.tld/?id=3&bar=4')

    def normalize_url_case05(self):
        u = URL('http://w3af.com/../f00.b4r?id=3&bar=4')
        u.normalize_url()
        self.assertEqual(u.url_string,
                         u'http://w3af.com/f00.b4r?id=3&bar=4')

    def normalize_url_case06(self):
        u = URL('http://w3af.com/f00.b4r?id=3&bar=//')
        u.normalize_url()
        self.assertEqual(u.url_string,
                         u'http://w3af.com/f00.b4r?id=3&bar=//')

    def normalize_url_case07(self):
        u = URL('http://user:passwd@host.tld:80')
        u.normalize_url()
        self.assertEqual(u.url_string,
                         u'http://user:passwd@host.tld/')

    def normalize_url_case08_collapse_root(self):
        u = URL('http://w3af.com/../f00.b4r')
        u.normalize_url()
        self.assertEqual(u.url_string,
                         u'http://w3af.com/f00.b4r')

    def normalize_url_case09_collapse_path(self):
        u = URL('http://w3af.com/abc/../f00.b4r')
        u.normalize_url()
        self.assertEqual(u.url_string,
                         u'http://w3af.com/f00.b4r')

    def normalize_url_case10_collapse_double_slash(self):
        u = URL('http://w3af.com/a//b/f00.b4r')
        u.normalize_url()
        self.assertEqual(u.url_string,
                         u'http://w3af.com/a/b/f00.b4r')

    def normalize_url_case11_double_dotdot_root(self):
        u = URL('http://w3af.com/../../f00.b4r')
        u.normalize_url()
        self.assertEqual(u.url_string,
                         u'http://w3af.com/f00.b4r')

    def normalize_url_dotdot_in_qs(self):
        u = URL('http://w3af.com/f00.b4r?id=/../spam.py')
        u.normalize_url()
        self.assertEqual(u.url_string,
                         u'http://w3af.com/f00.b4r?id=/../spam.py')

    def normalize_url_case12(self):
        # IPv6 support
        u = URL('http://fe80:0:0:0:202:b3ff:fe1e:8329/')
        u.normalize_url()
        self.assertEqual(u.url_string,
                         u'http://fe80:0:0:0:202:b3ff:fe1e:8329/')

    def normalize_url_case13(self):
        u = URL('http://host.tld:80/foo/bar')
        orig_id = id(u.querystring)
        u.normalize_url()

        self.assertEqual(orig_id, id(u.querystring))

    #
    #    __str__
    #
    def test_str_case01(self):
        self.assertEqual(str(URL('http://w3af.com/xyz.txt;id=1?file=2')),
                         'http://w3af.com/xyz.txt;id=1?file=2')
    
    def test_str_normalize_on_init(self):
        self.assertEqual(str(URL('http://w3af.com:80/')),
                         'http://w3af.com/')
    
    def test_str_special_encoding_filename(self):
        self.assertEqual(str(URL(u'http://w3af.com/indéx.html', 'latin1')),
                         u'http://w3af.com/indéx.html'.encode('latin1'))

    def test_str_special_encoding_query_string(self):
        url = URL('http://w3af.com/a/b/é.php?x=á')
        self.assertEqual(str(url), 'http://w3af.com/a/b/é.php?x=á')

    def test_str_special_encoding_query_string_urlencoded(self):
        msg = ('Please note that this test does NOT make any sense.'
               'Leaving this here just as a reminder to myself.'
               ''
               'When the document parser extracts a URL from the HTML page'
               ' it will call BaseParser._decode_url() to URL-decode and'
               ' utf-8 (or whatever encoding is specified in the headers)'
               ' decode the string and then send unicode to URL.__init__.'
               ''
               'Thus, sending URL-encoded data to URL.__init__ like we do'
               ' in this test does NOT make any sense and will yield unexpected'
               ' results.')

        raise SkipTest(msg)

        url = URL('http://w3af.com/a/b/%E1%BA%BC.php?x=%E1%BA%BC')
        self.assertEqual(str(url), '#fail')

    #
    #    __unicode__
    #
    def test_unicode(self):
        self.assertEqual(unicode(URL('http://w3af.com:80/')),
                         u'http://w3af.com/')
        
        self.assertEqual(unicode(URL(u'http://w3af.com/indéx.html', 'latin1')),
                         u'http://w3af.com/indéx.html')

    def test_unicode_special_encoding_query_string(self):
        url = URL('http://w3af.com/a/b/é.php?x=á')
        self.assertEqual(unicode(url), u'http://w3af.com/a/b/é.php?x=á')

    #
    #    all_but_scheme
    #
    def test_all_but_scheme(self):
        self.assertEqual(URL('https://w3af.com:443/xyz/').all_but_scheme(),
                         'w3af.com/xyz/')
        
        self.assertEqual(URL('https://w3af.com:443/xyz/file.asp').all_but_scheme(),
                         'w3af.com/xyz/')

    #
    #    from_parts
    #
    def test_from_parts(self):
        u = URL.from_parts('http', 'w3af.com', '/foo/bar.txt', None, 'a=b',
                           'frag')
        
        self.assertEqual(u.path, '/foo/bar.txt')
        self.assertEqual(u.scheme, 'http')
        self.assertEqual(u.get_file_name(), 'bar.txt')
        self.assertEqual(u.get_extension(), 'txt')

    #
    #    get_domain_path
    #
    def test_get_domain_path(self):
        self.assertEqual(URL('http://w3af.com/def/jkl/').get_domain_path().url_string,
                         u'http://w3af.com/def/jkl/')
        
        self.assertEqual(URL('http://w3af.com/def.html').get_domain_path().url_string,
                         u'http://w3af.com/')
        
        self.assertEqual(URL('http://w3af.com/xyz/def.html').get_domain_path().url_string,
                         u'http://w3af.com/xyz/')
        
        self.assertEqual(URL('http://w3af.com:80/xyz/def.html').get_domain_path().url_string,
                         u'http://w3af.com/xyz/')
        
        self.assertEqual(URL('http://w3af.com:443/xyz/def.html').get_domain_path().url_string,
                         u'http://w3af.com:443/xyz/')
        
        self.assertEqual(URL('https://w3af.com:443/xyz/def.html').get_domain_path().url_string,
                         u'https://w3af.com/xyz/')
        
        self.assertEqual(URL('http://w3af.com').get_domain_path().url_string,
                         u'http://w3af.com/')

    def test_is_valid_domain_valid(self):
        self.assertTrue(URL("http://1.2.3.4").is_valid_domain())        
        self.assertTrue(URL("http://aaa.com").is_valid_domain())
        self.assertTrue(URL("http://aa-bb").is_valid_domain())
        self.assertTrue(URL("http://w3af.com").is_valid_domain())
        self.assertTrue(URL("http://w3af.com:39").is_valid_domain())
        self.assertTrue(URL("http://w3af.com:3932").is_valid_domain())
        self.assertTrue(URL("http://f.o.o.b.a.r.s.p.a.m.e.g.g.s").is_valid_domain())
        self.assertTrue(URL("http://abc:3932").is_valid_domain())
        
    def test_is_valid_domain_invalid(self):
        self.assertFalse(URL("http://aaa.").is_valid_domain())
        self.assertFalse(URL("http://aaa*a").is_valid_domain())

    #
    #    get_path
    #
    def test_get_path(self):
        self.assertEqual(URL('https://w3af.com:443/xyz/file.asp').get_path(),
                         '/xyz/file.asp')
        
        self.assertEqual(URL('https://w3af.com:443/xyz/file.asp?id=-2').get_path(),
                         '/xyz/file.asp')
        
        self.assertEqual(URL('https://w3af.com:443/xyz/').get_path(),
                         '/xyz/')
        
        self.assertEqual(URL('https://w3af.com:443/xyz/123/456/789/').get_path(),
                         '/xyz/123/456/789/')
        
        self.assertEqual(URL('https://w3af.com:443/').get_path(), '/')

    #
    #    get_params_string
    #
    def test_get_params_string(self):
        self.assertEqual(URL(u'http://w3af.com/').get_params_string(),
                         u'')
        
        self.assertEqual(URL(u'http://w3af.com/;id=1').get_params_string(),
                         u'id=1')
        
        self.assertEqual(URL(u'http://w3af.com/?id=3;id=1').get_params_string(),
                         u'')
        
        self.assertEqual(URL(u'http://w3af.com/;id=1?id=3').get_params_string(),
                         u'id=1')
        
        self.assertEqual(URL(u'http://w3af.com/foobar.html;id=1?id=3').get_params_string(),
                         u'id=1')

    #
    #    get_params
    #
    def test_get_params(self):
        self.assertEqual(URL('http://w3af.com/xyz.txt;id=1?file=2').get_params(),
                         {'id': '1'})
        
        self.assertEqual(URL('http://w3af.com/xyz.txt;id=1&file=2?file=2').get_params(),
                         {'id': '1', 'file': '2'})
        
        self.assertEqual(URL('http://w3af.com/xyz.txt;id=1&file=2?spam=2').get_params(),
                         {'id': '1', 'file': '2'})
                         
        self.assertEqual(URL('http://w3af.com/xyz.txt;id=1&file=2?spam=3').get_params(),
                         {'id': '1', 'file': '2'})
    
    #
    #    get_net_location
    #
    def test_get_net_location(self):
        self.assertEqual(URL("http://1.2.3.4").get_net_location(),
                         '1.2.3.4')
        
        self.assertEqual(URL("http://aaa.com:80").get_net_location(),
                         'aaa.com')
        
        self.assertEqual(URL("http://aaa:443").get_net_location(),
                         'aaa:443')
        
    #
    #    from_url
    #
    def test_from_url(self):
        o = URL('http://w3af.com/foo/bar.txt')
        u = URL.from_URL(o)
        
        self.assertEqual(u.path, '/foo/bar.txt')
        self.assertEqual(u.scheme, 'http')
        self.assertEqual(u.get_file_name(), 'bar.txt')
        self.assertEqual(u.get_extension(), 'txt')
        
        o = URL('w3af.com')
        u = URL.from_URL(o)
        self.assertEqual(u.get_domain(), 'w3af.com')
        self.assertEqual(u.get_protocol(), 'http')

    def test_from_url_keep_form(self):
        o = URL('http://w3af.com/foo/bar.txt')
        o.querystring = URLEncodedForm()

        u = URL.from_URL(o)
        self.assertIsInstance(u.querystring, URLEncodedForm)
        self.assertIsNot(u.querystring, o.querystring)
        self.assertEqual(u.querystring, o.querystring)

    #
    #    url_string
    #
    def test_url_string(self):
        u = URL('http://w3af.com/foo/bar.txt?id=1')
        self.assertEqual(u.url_string,
                         u'http://w3af.com/foo/bar.txt?id=1')
        
        u = URL('http://w3af.com/foo%20bar/bar.txt?id=1')
        self.assertEqual(u.url_string,
                         u'http://w3af.com/foo%20bar/bar.txt?id=1')
    
    #
    #    has_querystring
    #
    def test_has_query_string(self):
        u = URL('http://w3af.com/foo/bar.txt')
        self.assertFalse(u.has_query_string())
        
        u = URL('http://w3af.com/foo/bar.txt?id=1')
        self.assertTrue(u.has_query_string())
        
        u = URL('http://w3af.com/foo/bar.txt;par=3')
        self.assertFalse(u.has_query_string())
    
    def test_get_query_string(self):
        self.assertEqual(URL(u'http://w3af.com/a/').querystring,
                         QueryString({}.items()))
        
        self.assertEqual(URL(u'http://w3af.com/foo/bar.txt?id=3').querystring,
                         QueryString({u'id': [u'3']}.items()))
        
        self.assertEqual(URL(u'http://w3af.com/foo/bar.txt?id=3&id=4').querystring,
                         QueryString({u'id': [u'3', u'4']}.items()))
        
        url = URL(u'http://w3af.com/foo/bar.txt?id=3&ff=4&id=5')
        self.assertEqual(url.querystring,
                         QueryString({u'id': [u'3', u'5'], u'ff': [u'4']}.items()))
        
        self.assertEqual(url.querystring, parse_qs(str(url.querystring)))

    def test_uri2url(self):
        u = URL('http://w3af.com/foo/bar.txt?id=3')
        self.assertEqual(u.uri2url().url_string,
                         u'http://w3af.com/foo/bar.txt')

    def test_remove_fragment(self):
        u = URL('http://w3af.com/foo/bar.txt?id=3#foobar')
        u.remove_fragment()
        self.assertEqual(u.url_string, u'http://w3af.com/foo/bar.txt?id=3')
        
        u = URL('http://w3af.com/foo/bar.txt#foobar')
        orig_qs_id = id(u.querystring)
        u.remove_fragment()
        self.assertEqual(u.url_string, u'http://w3af.com/foo/bar.txt')
        self.assertEqual(id(u.querystring), orig_qs_id)
    
    def test_get_port(self):
        self.assertEqual(URL('http://w3af.com/f00.b4r').get_port(), 80)
        self.assertEqual(URL('http://w3af.com:80/f00.b4r').get_port(), 80)
        
        self.assertEqual(URL('http://w3af.com:443/f00.b4r').get_port(), 443)
        self.assertEqual(URL('https://w3af.com/f00.b4r').get_port(), 443)
        self.assertEqual(URL('https://w3af.com:443/f00.b4r').get_port(), 443)
        self.assertEqual(URL('https://w3af.com:80/f00.b4r').get_port(), 80)

    def test_get_domain(self):
        self.assertEqual(URL('http://w3af.com/def/jkl/').get_domain(),
                         'w3af.com')
        self.assertEqual(URL('http://1.2.3.4/def/jkl/').get_domain(),
                         '1.2.3.4')
        self.assertEqual(URL('http://555555/def/jkl/').get_domain(),
                         '555555')
        self.assertEqual(URL('http://foo.bar.def/def/jkl/').get_domain(),
                         'foo.bar.def')
    
    def test_set_domain(self):
        u = URL('http://w3af.com/def/jkl/')
        self.assertEqual(u.get_domain(), 'w3af.com')

        u.set_domain('host.tld')
        self.assertEqual(u.get_domain(), 'host.tld')

        u.set_domain('foobar')
        self.assertEqual(u.get_domain(), 'foobar')

        u.set_domain('foobar.')
        self.assertEqual(u.get_domain(), 'foobar.')

    def test_set_domain_invalid(self):
        u = URL('http://w3af.com/')
        self.assertRaises(ValueError, u.set_domain, 'foobar:443')
        self.assertRaises(ValueError, u.set_domain, 'foo*bar')
        self.assertRaises(ValueError, u.set_domain, '')

    def test_set_domain_with_port(self):
        u = URL('http://w3af.com:443/def/jkl/')
        self.assertEqual(u.get_domain(), 'w3af.com')
        
        u.set_domain('host.tld')
        self.assertEqual(u.get_net_location(), 'host.tld:443')

    def test_get_protocol(self):
        self.assertEqual(URL("http://1.2.3.4").get_protocol(), 'http')
        self.assertEqual(URL("https://aaa.com:80").get_protocol(), 'https')
        self.assertEqual(URL("ftp://aaa:443").get_protocol(), 'ftp')
    
    def test_set_protocol(self):
        u = URL("http://1.2.3.4")
        self.assertEqual(u.get_protocol(), 'http')
        
        u.set_protocol('https')
        self.assertEqual(u.get_protocol(), 'https')
    
    def test_get_root_domain(self):
        self.assertEqual(URL("http://1.2.3.4").get_root_domain(), '1.2.3.4')
        self.assertEqual(URL("https://aaa.com:80").get_root_domain(), 'aaa.com')
        self.assertEqual(URL("http://aaa.com").get_root_domain(), 'aaa.com')
        self.assertEqual(URL("http://www.aaa.com").get_root_domain(), 'aaa.com')
        self.assertEqual(URL("http://mail.aaa.com").get_root_domain(), 'aaa.com')
        self.assertEqual(URL("http://spam.eggs.aaa.com").get_root_domain(),
                         'aaa.com')
        self.assertEqual(URL("http://spam.eggs.aaa.com.ar").get_root_domain(),
                         'aaa.com.ar')
        self.assertEqual(URL("http://foo.aaa.com.ar").get_root_domain(),
                         'aaa.com.ar')
        self.assertEqual(URL("http://foo.aaa.edu.sz").get_root_domain(),
                         'edu.sz')
    
    def test_get_filename(self):
        self.assertEqual(URL('https://w3af.com:443/xyz/def.html').get_file_name(),
                         'def.html')
        self.assertEqual(URL('https://w3af.com:443/xyz/').get_file_name(), '')
        self.assertEqual(URL('https://w3af.com:443/xyz/d').get_file_name(), 'd')
    
    def test_set_filename(self):
        u = URL('https://w3af.com:443/xyz/def.html')
        u.set_file_name( 'abc.pdf' )
        self.assertEqual(u.url_string,
                         'https://w3af.com/xyz/abc.pdf')
        self.assertEqual(u.get_file_name(), 'abc.pdf')

        u = URL('https://w3af.com/xyz/def.html?id=1')
        u.set_file_name( 'abc.pdf' )
        self.assertEqual(u.url_string,
                         'https://w3af.com/xyz/abc.pdf?id=1')

        u = URL('https://w3af.com/xyz/def.html?file=/etc/passwd')
        u.set_file_name( 'abc.pdf' )
        self.assertEqual(u.url_string,
                         'https://w3af.com/xyz/abc.pdf?file=/etc/passwd')

        u = URL('https://w3af.com/')
        u.set_file_name( 'abc.pdf' )
        self.assertEqual(u.url_string,
                         'https://w3af.com/abc.pdf')
    
    def test_get_extension(self):
        self.assertEqual(URL('https://w3af.com:443/xyz/d').get_extension(), '')
        self.assertEqual(URL('https://w3af.com:443/xyz/').get_extension(), '')
        self.assertEqual(URL('https://w3af.com:443/xyz/d.html').get_extension(),
                         'html')

    def test_set_extension(self):
        u = URL('https://www.w3af.com/xyz/foo')
        self.assertRaises(Exception, u.set_extension, 'xml')

        u = URL('https://w3af.com/xyz/d.html')
        u.set_extension('xml')
        self.assertEqual(u.get_extension(), 'xml')

        u = URL('https://w3af.com/xyz/d.html?id=3')
        u.set_extension('xml')
        self.assertEqual(u.get_extension(), 'xml')

        u = URL('https://w3af.com/xyz/d.html.foo?id=3')
        u.set_extension('xml')
        self.assertEqual(u.get_extension(), 'xml')
        self.assertEqual(u.url_string,
                         u'https://w3af.com/xyz/d.html.xml?id=3')
    
    def test_get_path_without_filename(self):
        u = URL('https://w3af.com:443/xyz/file.asp')
        self.assertEqual(u.get_path_without_file(), '/xyz/')
        
        u = URL('https://w3af.com:443/xyz/')
        self.assertEqual(u.get_path_without_file(), '/xyz/')
        
        u = URL('https://w3af.com:443/xyz/123/456/789/')
        self.assertEqual(u.get_path_without_file(), '/xyz/123/456/789/')
    
    def test_get_path_qs(self):
        u = URL(u'https://w3af.com:443/xyz/123/456/789/')
        self.assertEqual(u.get_path(), u'/xyz/123/456/789/')
        
        u = URL(u'https://w3af.com:443/xyz/123/456/789/')
        self.assertEqual(u.get_path_qs(), u'/xyz/123/456/789/')
        
        u = URL(u'https://w3af.com:443/xyz/file.asp')
        self.assertEqual(u.get_path_qs(), u'/xyz/file.asp')
        
        u = URL(u'https://w3af.com:443/xyz/file.asp?id=1')
        self.assertEqual(u.get_path_qs(), u'/xyz/file.asp?id=1')

    def test_has_params(self):
        self.assertFalse(URL('http://w3af.com/').has_params())
        self.assertFalse(URL('http://w3af.com/?id=3;id=1').has_params())
        
        self.assertTrue(URL('http://w3af.com/;id=1').has_params())
        self.assertTrue(URL('http://w3af.com/;id=1?id=3').has_params())
        self.assertTrue(URL('http://w3af.com/foobar.html;id=1?id=3').has_params())

    def test_remove_params(self):
        self.assertEqual(URL('http://w3af.com/').remove_params().url_string,
                         u'http://w3af.com/')
        self.assertEqual(URL('http://w3af.com/def.txt').remove_params().url_string,
                         u'http://w3af.com/def.txt')
        self.assertEqual(URL('http://w3af.com/;id=1').remove_params().url_string,
                         u'http://w3af.com/')
        self.assertEqual(URL('http://w3af.com/;id=1&file=2').remove_params().url_string,
                         u'http://w3af.com/')
        self.assertEqual(URL('http://w3af.com/;id=1?file=2').remove_params().url_string,
                         u'http://w3af.com/?file=2')
        self.assertEqual(URL('http://w3af.com/xyz.txt;id=1?file=2').remove_params().url_string,
                         u'http://w3af.com/xyz.txt?file=2')

    def test_set_params(self):
        u = URL('http://w3af.com/;id=1')
        u.set_param('file=2')
        
        self.assertEqual(u.get_params_string(), 'file=2')
        
        u = URL('http://w3af.com/xyz.txt;id=1?file=2')
        u.set_param('file=3')
        
        self.assertEqual(u.get_params_string(), 'file=3')
        self.assertEqual(u.get_path_qs(), '/xyz.txt;file=3?file=2')

    def test_iter(self):
        url = u'http://w3af.com/xyz.txt;id=1?file=2'
        url_obj = URL(url)
        self.assertEqual(''.join(chr for chr in url_obj), url)

    def test_hash_diff(self):
        u1 = URL('http://w3af.com/')
        u2 = URL('http://w3af.com/def.htm')
        test = [u1, u2]
        self.assertEqual( len(list(set(test))), 2)
    
    def test_hash_equal(self):
        u1 = URL('http://w3af.com/')
        u2 = URL('http://w3af.com/')
        test = [u1, u2]
        self.assertEqual( len(list(set(test))), 1)

    def test_contains_true(self):
        u = URL('http://w3af.com/xyz.txt;id=1?file=2')
        self.assertIn('1', u)

        u = URL('http://w3af.com/xyz.txt;id=1?file=2')
        self.assertIn('file=2', u)

    def test_contains_false(self):
        u = URL('http://w3af.com/xyz.txt;id=1?file=2')
        self.assertNotIn('hello!', u)

    def test_add(self):
        u = URL('http://www.w3af.com/')
        x = u + 'abc'
        self.assertEqual(x, u'http://www.w3af.com/abc')

        u = URL('http://www.w3af.com/')
        x = u + ' hello world!'
        self.assertEqual(x, u'http://www.w3af.com/ hello world!')

        u = URL('http://www.w3af.com/')
        self.assertRaises(TypeError, u.__add__, 1)
    
    def test_radd(self):
        u = URL('http://www.w3af.com/')
        x = 'abc' + u
        self.assertEqual(x, u'abchttp://www.w3af.com/')

        u = URL('http://www.w3af.com/')
        x = 'hello world! ' + u
        self.assertEqual(x, u'hello world! http://www.w3af.com/')

        u = URL('http://www.w3af.com/')
        self.assertRaises(TypeError, u.__radd__, 1)
    
    def test_nonzero(self):
        self.assertTrue( bool(URL('http://www.w3af.com')) )

    def test_file_url_full_path(self):
        u = URL('file:///etc/passwd')
        self.assertIn('root', urllib2.urlopen(u.url_string).read())

    #
    #   Test memoize
    #
    def test_memoized(self):
        u = URL('http://www.w3af.com/')
        self.assertEqual(u._cache, dict())

        url = u.uri2url()
        self.assertNotEqual(u._cache, dict())
        self.assertIn(url, u._cache.values())

        second_url = u.uri2url()
        self.assertIs(url, second_url)

        self.assertIsInstance(url, URL)
        self.assertIsInstance(second_url, URL)

    def test_can_be_pickled(self):
        # Pickle a URL object that contains a cache
        u = URL('http://www.w3af.com/')
        domain_path = u.get_domain_path()

        cPickle.dumps(u)
        cPickle.dumps(domain_path)

    def test_can_be_pickled_with_qs(self):
        # Pickle a URL object that contains a query string
        u = URL('http://www.w3af.com/?id=1')

        pickled_url = cPickle.dumps(u)
        unpickled_url = cPickle.loads(pickled_url)

        self.assertEqual(unpickled_url, u)
        self.assertEqual(str(unpickled_url.get_querystring()), 'id=1')

    def test_can_pickle_via_queue(self):
        """
        https://github.com/andresriancho/w3af/issues/8748
        """
        sq = SimpleQueue()
        u1 = URL('http://www.w3af.com/')
        sq.put(u1)
        u2 = sq.get()

        self.assertEqual(u1, u2)

    def test_copy(self):
        u = URL('http://www.w3af.com/?id=1&id=2')
        self.assertEqual(u, u.copy())

