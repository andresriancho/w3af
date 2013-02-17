# -*- coding: utf-8 -*-
'''
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

'''
import unittest

from nose.plugins.skip import SkipTest

from core.data.parsers.url import URL, parse_qs
from core.data.dc.query_string import QueryString


class TestURLParser(unittest.TestCase):

    #
    #    Object instansiation test
    #
    def test_simplest_url(self):
        u = URL('http://w3af.com/foo/bar.txt')
        
        self.assertEqual(u.path, '/foo/bar.txt')
        self.assertEqual(u.scheme, 'http')
        self.assertEqual(u.get_file_name(), 'bar.txt')
        self.assertEqual(u.get_extension(), 'txt')

    def test_default_proto(self):
        '''
        http is the default protocol, we can provide URLs with no proto
        '''
        u = URL('w3af.com')
        self.assertEqual(u.get_domain(), 'w3af.com')
        self.assertEqual(u.get_protocol(), 'http')
    
    def test_no_domain(self):
        '''
        But we can't specify a URL without a domain!
        '''
        self.assertRaises(ValueError, URL, 'http://')
    
    def test_case_insensitive_proto(self):
        u = URL('HtTp://w3af.com/foo/bar.txt')
        self.assertEqual(u.scheme, 'http')
        
    def test_path_root(self):
        u = URL('http://w3af.com/')
        self.assertEqual(u.path, '/')

    def test_url_in_qs(self):
        u = URL('http://w3af.org/?foo=http://w3af.com')
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
        qs_value = self.decode_get_qs(
            u'https://w3af.com:443/xyz/file.asp?id=1')
        EXPECTED = '1'
        self.assertEqual(qs_value, EXPECTED)

    def test_decode_perc_20(self):
        qs_value = self.decode_get_qs(
            u'https://w3af.com:443/xyz/file.asp?id=1%202')
        EXPECTED = u'1 2'
        self.assertEqual(qs_value, EXPECTED)

    def test_decode_space(self):
        qs_value = self.decode_get_qs(
            u'https://w3af.com:443/xyz/file.asp?id=1 2')
        EXPECTED = u'1 2'
        self.assertEqual(qs_value, EXPECTED)

    def test_decode_plus(self):
        qs_value = self.decode_get_qs(
            u'https://w3af.com:443/xyz/file.asp?id=1+2')
        EXPECTED = u'1+2'
        self.assertEqual(qs_value, EXPECTED)

    def test_decode_url_encode_plus(self):
        qs_value = self.decode_get_qs(
            u'https://w3af.com:443/xyz/file.asp?id=1%2B2')
        EXPECTED = u'1+2'
        self.assertEqual(qs_value, EXPECTED)

    #
    #    Encode tests
    #
    def test_encode_simple(self):
        res_str = URL(u'http://w3af.com').url_encode()
        EXPECTED = 'http://w3af.com/'
        self.assertEqual(res_str, EXPECTED)

    def test_encode_perc_20(self):
        res_str = URL(u'https://w3af.com:443/file.asp?id=1%202').url_encode()
        EXPECTED = 'https://w3af.com/file.asp?id=1%202'
        self.assertEqual(res_str, EXPECTED)

    def test_encode_space(self):
        res_str = URL(u'https://w3af.com:443/file.asp?id=1 2').url_encode()
        EXPECTED = 'https://w3af.com/file.asp?id=1%202'
        self.assertEqual(res_str, EXPECTED)

    def test_encode_plus(self):
        msg = '''
        When parsing an HTML document that has a link like the one below, can
        the browser (or in this case w3af) know the original intent of the web
        developer?

        Was he trying to put a space or a real "+" ? At the moment of writing
        these lines, w3af thinks that the user is trying to put a "+", so it
        will encode it as a %2B for sending to the wire.
        '''
        raise SkipTest(msg)

        res_str = URL(u'https://w3af.com:443/file.asp?id=1+2').url_encode()
        EXPECTED = 'https://w3af.com:443/file.asp?id=1+2'
        self.assertEqual(res_str, EXPECTED)

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
        '''Encode and Decode should be able to run one on the result of the
        other and return the original'''
        original = URL(u'https://w3af.com:443/file.asp?id=1%202')
        decoded = original.url_decode()
        encoded = decoded.url_encode()
        self.assertEqual(original.url_encode(), encoded)

    def test_encode_decode(self):
        '''Encode and Decode should be able to run one on the result of the
        other and return the original'''
        original = URL(u'https://w3af.com:443/file.asp?id=1%202')
        encoded = original.url_encode()
        decoded = URL(encoded).url_decode()
        self.assertEqual(original, decoded)
    
    #
    #    Test get_directories
    #
    def test_get_directories_path_levels_1(self):
        result = [i.url_string for i in URL('http://w3af.com/xyz/def/123/').get_directories()]
        expected = [u'http://w3af.com/xyz/def/123/', u'http://w3af.com/xyz/def/',
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
        '''
        Opera and Chrome behave like this. For those browsers the URL
        leads to no good, so I'm going to do the same thing. If the user
        wants to specify a URL that contains a colon he should URL
        encode it.
        '''
        u = URL('http://w3af.com/')
        self.assertRaises(ValueError, u.url_join, "d:url.html?id=13&subid=3")

    def test_url_join_case07(self):
        u = URL('http://w3af.com/')
        self.assertEqual(u.url_join('http://w3af.org:8080/abc.html').url_string,
                         u'http://w3af.org:8080/abc.html')

    def test_parse_qs_case01(self):
        self.assertEqual(parse_qs('id=3'),
                         QueryString( [(u'id', [u'3']),] ))
    
    def test_parse_qs_case02(self):
        self.assertEqual(parse_qs('id=3+1'),
                         QueryString( [(u'id', [u'3+1']),] ))
    
    def test_parse_qs_case03(self):
        self.assertEqual(parse_qs('id=3&id=4'),
                         QueryString( [(u'id', [u'3', u'4']),] ))
    
    def test_parse_qs_case04(self):
        self.assertEqual(parse_qs('id=3&ff=4&id=5'),
                         QueryString( [(u'id', [u'3', u'5']),
                                       (u'ff', [u'4'])] ))
    
    def test_parse_qs_case05(self):
        self.assertEqual(parse_qs('pname'),
                         QueryString( [(u'pname', [u'']),] ))
    
    def test_parse_qs_case06(self):
        self.assertEqual(parse_qs(u'%B1%D0%B1%D1=%B1%D6%B1%D7', encoding='euc-jp'),
                         QueryString( [(u'\u9834\u82f1', [u'\u75ab\u76ca']),] ))
    
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
        self.assertEqual(u.url_string,
                         u'http://host.tld/foo/bar')

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

    def normalize_url_case08(self):
        u = URL('http://w3af.com/../f00.b4r')
        u.normalize_url()
        self.assertEqual(u.url_string,
                         u'http://w3af.com/f00.b4r')

    def normalize_url_case09(self):
        u = URL('http://w3af.com/abc/../f00.b4r')
        u.normalize_url()
        self.assertEqual(u.url_string,
                         u'http://w3af.com/f00.b4r')

    def normalize_url_case10(self):
        u = URL('http://w3af.com/a//b/f00.b4r')
        u.normalize_url()
        self.assertEqual(u.url_string,
                         u'http://w3af.com/a/b/f00.b4r')

    def normalize_url_case11(self):
        u = URL('http://w3af.com/../../f00.b4r')
        u.normalize_url()
        self.assertEqual(u.url_string,
                         u'http://w3af.com/f00.b4r')

    def normalize_url_case12(self):
        # IPv6 support
        u = URL('http://fe80:0:0:0:202:b3ff:fe1e:8329/')
        u.normalize_url()
        self.assertEqual(u.url_string,
                         u'http://fe80:0:0:0:202:b3ff:fe1e:8329/')

    #
    #    __str__
    #
    def test_str_case01(self):
        self.assertEqual(str(URL('http://w3af.com/xyz.txt;id=1?file=2')),
                         'http://w3af.com/xyz.txt;id=1?file=2')
    
    def test_str_normalize_on_init(self):
        self.assertEqual(str(URL('http://w3af.com:80/')),
                         'http://w3af.com/')
    
    def test_special_encoding(self):
        self.assertEqual(str(URL(u'http://w3af.com/indéx.html', 'latin1')),
                         u'http://w3af.com/indéx.html'.encode('latin1'))

    #
    #    __unicode__
    #
    def test_unicode(self):
        self.assertEqual(unicode(URL('http://w3af.com:80/')),
                         u'http://w3af.com/')
        
        self.assertEqual(unicode(URL(u'http://w3af.com/indéx.html', 'latin1')),
                         u'http://w3af.com/indéx.html')
        
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
        

