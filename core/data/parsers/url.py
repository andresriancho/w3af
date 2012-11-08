# -*- coding: utf-8 -*-
'''
urlParser.py

Copyright 2006 Andres Riancho

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
import copy
import re
import urllib
import urlparse

from core.data.misc.encoding import smart_str, PERCENT_ENCODE
from core.controllers.misc.is_ip_address import is_ip_address
from core.data.misc.encoding import is_known_encoding
from core.controllers.misc.ordereddict import OrderedDict
from core.controllers.w3afException import w3afException
from core.data.constants.encodings import DEFAULT_ENCODING
from core.data.dc.data_container import DataContainer
from core.data.dc.queryString import QueryString
from core.data.db.disk_item import disk_item

# TODO: this list should be updated from time to time, automatically.
# last upd: 14 Jul 2011
# taken from http:#en.wikipedia.org/wiki/List_of_Internet_top-level_domains
GTOP_LEVEL_DOMAINS = set(('ac','ad','ae','aero','af','ag','ai','al','am',
    'an','ao','aq','ar','arpa','as','asia','at','au','aw','ax','az','ba',
    'bb','bd','be','bf','bg','bh','bi','biz','bj','bm','bn','bo','br','bs',
    'bt','bv','bw','by','bz','ca','cat','cc','cd','cf','cg','ch','ci','ck',
    'cl','cm','cn','co','com','coop','cr','cs','cu','cv','cx','cy','cz',
    'dd','de','dj','dk','dm','do','dz','ec','edu','ee','eg','er','es','et',
    'eu','fi','fj','fk','fm','fo','fr','ga','gb','gd','ge','gf','gg','gh',
    'gi','gl','gm','gn','gov','gp','gq','gr','gs','gt','gu','gw','gy','hk',
    'hm','hn','hr','ht','hu','id','ie','il','im','in','info','int','io',
    'iq','ir','is','it','je','jm','jo','jobs','jp','ke','kg','kh','ki',
    'km','kn','kp','kr','kw','ky','kz','la','lb','lc','li','lk','lr','ls',
    'lt','lu','lv','ly','ma','mc','md','me','mg','mh','mil','mk','ml',
    'mm','mn','mo','mobi','mp','mq','mr','ms','mt','mu','museum','mv','mw',
    'mx','my','mz','na','name','nc','ne','net','nf','ng','ni','nl','no',
    'np','nr','nu','nz','om','org','pa','pe','pf','pg','ph','pk','pl','pm',
    'pn','pr','pro','ps','pt','pw','py','qa','re','ro','rs','ru','rw','sa',
    'sb','sc','sd','se','sg','sh','si','sj','sk','sl','sm','sn','so','sr',
    'st','su','sv','sy','sz','tc','td','tel','tf','tg','th','tj','tk','tl',
    'tm','tn','to','tp','tr','travel','tt','tv','tw','tz','ua','ug','uk',
    'us','uy','uz','va','vc','ve','vg','vi','vn','vu','wf','ws','xxx','ye',
    'yt','za','zm','zw'))

def set_changed(meth):
    '''
    Function to decorate methods in order to set the "self._changed" attribute
    of the object to True.
    '''
    def wrapper(self, *args, **kwargs):
        self._changed = True
        return meth(self, *args, **kwargs)

    return wrapper

def parse_qsl(qs, keep_blank_values=0, strict_parsing=0):
    """This is a slightly modified version of the function with the same name
    that is defined in urlparse.py . I had to modify it in order to have
    '+' handled in the way w3af needed it. Note that the only change is:
    
    -        name = unquote(nv[0].replace('+', ' '))
    -        value = unquote(nv[1].replace('+', ' '))
    +        name = unquote(nv[0])
    +        value = unquote(nv[1])
    
    In other words, keep those + !
    
    Parse a query given as a string argument.

    Arguments:

    qs: percent-encoded query string to be parsed

    keep_blank_values: flag indicating whether blank values in
        percent-encoded queries should be treated as blank strings.  A
        true value indicates that blanks should be retained as blank
        strings.  The default false value indicates that blank values
        are to be ignored and treated as if they were  not included.

    strict_parsing: flag indicating what to do with parsing errors. If
        false (the default), errors are silently ignored. If true,
        errors raise a ValueError exception.

    Returns a list, as G-d intended.
    """
    pairs = [s2 for s1 in qs.split('&') for s2 in s1.split(';')]
    r = []
    for name_value in pairs:
        if not name_value and not strict_parsing:
            continue
        nv = name_value.split('=', 1)
        if len(nv) != 2:
            if strict_parsing:
                raise ValueError, "bad query field: %r" % (name_value,)
            # Handle case of a control-name with no equal sign
            if keep_blank_values:
                nv.append('')
            else:
                continue
        if len(nv[1]) or keep_blank_values:
            name = urlparse.unquote(nv[0])
            value = urlparse.unquote(nv[1])
            r.append((name, value))

    return r

def parse_qs(qstr, ignore_exc=True, encoding=DEFAULT_ENCODING):
    '''
    Parse a url encoded string (a=b&c=d) into a QueryString object.
    
    @param url_enc_str: The string to parse
    @return: A QueryString object (a dict wrapper). 

    >>> parse_qs('id=3')
    QueryString({u'id': [u'3']})
    >>> parse_qs('id=3+1')
    QueryString({u'id': [u'3+1']})
    >>> parse_qs('id=3&id=4')
    QueryString({u'id': [u'3', u'4']})
    >>> parse_qs('id=3&ff=4&id=5')
    QueryString({u'id': [u'3', u'5'], u'ff': [u'4']})
    >>> parse_qs('pname')
    QueryString({u'pname': [u'']})
    >>> parse_qs(u'%B1%D0%B1%D1=%B1%D6%B1%D7', encoding='euc-jp')
    QueryString({u'\u9834\u82f1': [u'\u75ab\u76ca']})
    >>> parse_qs('%B1%D0%B1%D1=%B1%D6%B1%D7', encoding='euc-jp')
    QueryString({u'\u9834\u82f1': [u'\u75ab\u76ca']})
    '''
    qs = QueryString(encoding=encoding)

    if qstr:
        # convert to string if unicode
        if isinstance(qstr, unicode):
            qstr = qstr.encode(encoding, 'ignore')
        try:
            odict = OrderedDict()
            for name, value in parse_qsl(qstr,
                                         keep_blank_values=True,
                                         strict_parsing=False):
                if name in odict:
                    odict[name].append(value)
                else:
                    odict[name] = [value]
        except Exception:
            if not ignore_exc:
                raise w3afException('Error while parsing "%r"' % (qstr,))
        else:
            def decode(item):
                return (
                    item[0].decode(encoding, 'ignore'),
                    [e.decode(encoding, 'ignore') for e in item[1]]
                )
            qs.update((decode(item) for item in odict.items()))
    return qs


class URL(disk_item):
    '''
    This class represents a URL and gives access to all its parts
    with several "getter" methods.
    
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    
    SAFE_CHARS = "%/:=&?~#+!$,;'@()*[]|"
    
    def __init__(self, data, encoding=DEFAULT_ENCODING):
        '''
        @param data: Either a string representing a URL or a 6-elems tuple
            representing the URL components:
            <scheme>://<netloc>/<path>;<params>?<query>#<fragment>

        Simple generic test, more detailed tests in each method!
        
        >>> u = URL('http://w3af.com/foo/bar.txt')
        >>> u.path
        '/foo/bar.txt'
        >>> u.scheme
        'http'
        >>> u.getFileName()
        'bar.txt'
        >>> u.getExtension()
        'txt'
        >>> 

        #
        # http is the default protocol, we can provide URLs with no proto
        #
        >>> u = URL('w3af.com')
        >>> u.getDomain()
        'w3af.com'
        >>> u.getProtocol()
        'http'

        #
        # But we can't specify a URL without a domain!
        #
        >>> u = URL('http://')
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        ValueError: Invalid URL "http://"

        #
        # And protocols are case insensitive
        #
        >>> u = URL('HtTp://w3af.com')
        >>> u.getDomain()
        'w3af.com'
        >>> u.getProtocol()
        'http'

        >>> u = URL(u'http://w3af.com/foo/bar.txt')
        >>> u.path
        u'/foo/bar.txt'

        >>> u = URL(u'http://w3af.com')
        >>> u.path
        u'/'

        >>> u = URL('http://w3af.org/?foo=http://w3af.com')
        >>> u.netloc
        'w3af.org'

        >>> u = URL('http://w3af.org/', encoding='x-euc-jp')
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        ValueError: Invalid encoding "x-euc-jp" when creating URL.
    
        '''
        self._already_calculated_url = None
        self._querystr = None
        self._changed = True
        self._encoding = encoding

        if data is None:
            raise ValueError('Can not build a URL from data=None.')

        # Verify that the encoding is a valid one. If we don't do it here,
        # things might get crazy afterwards.
        if not is_known_encoding( encoding ):
            raise ValueError('Invalid encoding "%s" when creating URL.' % encoding)

        if isinstance(data, tuple):
            scheme, netloc, path, params, qs, fragment = data
        else:
            scheme, netloc, path, params, qs, fragment = \
                                        urlparse.urlparse(data)
            #
            # This is the case when someone creates a URL like
            # this: URL('www.w3af.com')
            #
            if scheme == netloc == '' and path:
                # By default we set the protocol to "http"
                scheme = 'http'
                netloc = path
                path = ''
        
        self.scheme = scheme or u''
        self.netloc = netloc or u''
        self.path = path or u'/'
        self.params = params or u''
        self.querystring = qs or u''
        self.fragment = fragment or u''

        if not self.netloc:
            # The URL is invalid, we don't have a netloc!
            if isinstance(data, tuple):
                invalid_url = urlparse.urlunparse(data)
            else:
                invalid_url = data 
            raise ValueError, 'Invalid URL "%s"' % (invalid_url,)

    @classmethod
    def from_parts(cls, scheme, netloc, path, params,
                   qs, fragment, encoding=DEFAULT_ENCODING):
        '''
        @param scheme: http/https
        @param netloc: domain and port
        @param path: directory
        @param params: URL params
        @param qs: query string
        @param fragment: #fragments
        @return: An instance of URL.

        This is a "constructor" for the URL class.
        
        >>> u = URL.from_parts('http', 'w3af.com', '/foo/bar.txt', None, 'a=b', 'frag')
        >>> u.path
        '/foo/bar.txt'
        >>> u.scheme
        'http'
        >>> u.getFileName()
        'bar.txt'
        >>> u.getExtension()
        'txt'
        '''
        return cls((scheme, netloc, path, params, qs, fragment), encoding)

    @classmethod
    def from_URL(cls, src_url_obj):
        '''
        @param src_url: The url object to use as "template" for the new one
        @return: An instance of URL with the same data as original_url_object

        This is a "constructor" for the URL class.
        
        >>> o = URL('http://w3af.com/foo/bar.txt')
        >>> u = URL.from_URL(o)
        >>> u.path
        '/foo/bar.txt'
        >>> u.scheme
        'http'
        >>> u.getFileName()
        'bar.txt'
        >>> u.getExtension()
        'txt'
        >>> 
        >>> u = URL('w3af.com')
        >>> u.getDomain()
        'w3af.com'
        >>> u.getProtocol()
        'http'
        '''
        scheme = src_url_obj.getProtocol()
        netloc = src_url_obj.getDomain()
        path = src_url_obj.getPath()
        params = src_url_obj.getParams()
        qs = unicode(copy.deepcopy(src_url_obj.querystring))
        fragment = src_url_obj.getFragment()
        encoding = src_url_obj.encoding
        return cls((scheme, netloc, path, params, qs, fragment), encoding)

    @property
    def url_string(self):
        '''
        @return: A <unicode> representation of the URL
        
        >>> u = URL('http://w3af.com/foo/bar.txt?id=1')
        >>> u.url_string
        u'http://w3af.com/foo/bar.txt?id=1'
        >>> u.url_string
        u'http://w3af.com/foo/bar.txt?id=1'
        >>> u = URL('http://w3af.com/foo%20bar/bar.txt?id=1')
        >>> u.url_string
        u'http://w3af.com/foo%20bar/bar.txt?id=1'
        '''
        calc = self._already_calculated_url
        
        if self._changed or calc is None:
            data = (self.scheme, self.netloc, self.path,
                    self.params, unicode(self.querystring),
                    self.fragment)
            calc = urlparse.urlunparse(data)
            # ensuring this is actually unicode
            if not isinstance(calc, unicode):
                calc = unicode(calc, self.encoding, 'replace')
            self._already_calculated_url = calc
            self._changed = False
        
        return calc
    
    @property
    def encoding(self):
        return self._encoding
           
    def hasQueryString(self):
        '''
        Analyzes the uri to check for a query string.
        
        >>> u = URL('http://w3af.com/foo/bar.txt')
        >>> u.hasQueryString()
        False
        >>> u = URL('http://w3af.com/foo/bar.txt?id=1')
        >>> u.hasQueryString()
        True
        >>> u = URL('http://w3af.com/foo/bar.txt;par=3')
        >>> u.hasQueryString()
        False
    
        @return: True if self has a query string.
        '''
        return bool(self.querystring)
    
    @property
    def querystring(self):
        '''
        Parses the query string and returns a QueryString
        (a dict like) object.
    
        @return: A QueryString Object that represents the query string.
        
        >>> URL(u'http://w3af.com/a/').querystring
        QueryString({})
        >>> URL(u'http://w3af.com/foo/bar.txt?id=3').querystring
        QueryString({u'id': [u'3']})
        >>> URL(u'http://w3af.com/foo/bar.txt?id=3&id=4').querystring
        QueryString({u'id': [u'3', u'4']})
        >>> u = URL(u'http://w3af.com/foo/bar.txt?id=3&ff=4&id=5')
        >>> u.querystring
        QueryString({u'id': [u'3', u'5'], u'ff': [u'4']})
        >>> u.querystring == parse_qs(str(u.querystring))
        True
        '''
        return self._querystr
    
    @querystring.setter
    @set_changed
    def querystring(self, qs):
        '''
        Set the query string for this URL.
        '''
        if isinstance(qs, DataContainer):
            self._querystr = qs
        elif isinstance(qs, dict):
            self._querystr = QueryString(qs.items())
        elif isinstance(qs, basestring):
            self._querystr = parse_qs(qs, ignore_exc=True,
                                      encoding=self.encoding)
        else:
            raise TypeError, ("Invalid type '%r'; must be DataContainer, "
                "dict or string" % type(qs))
        
    def uri2url(self):
        '''
        @return: Returns a string contaning the URL without the query string.

        >>> u = URL('http://w3af.com/foo/bar.txt?id=3')
        >>> u.uri2url().url_string
        u'http://w3af.com/foo/bar.txt'
        '''
        return URL.from_parts(
                        self.scheme, self.netloc, self.path,
                        None, None, None, encoding=self._encoding
                        )
    
    def getFragment(self):
        '''
        @return: Returns the #fragment of the URL.
        '''
        return self.fragment
    
    def removeFragment(self):
        '''
        @return: A URL containing the URL without the fragment.
        
        >>> u = URL('http://w3af.com/foo/bar.txt?id=3#foobar')
        >>> u.removeFragment().url_string
        u'http://w3af.com/foo/bar.txt?id=3'
        >>> u = URL('http://w3af.com/foo/bar.txt#foobar')
        >>> u.removeFragment().url_string
        u'http://w3af.com/foo/bar.txt'
        '''
        params = (self.scheme, self.netloc, self.path,
                  self.params, unicode(self.querystring),
                  None)
        return URL.from_parts(*params, encoding=self._encoding)
    
    def baseUrl(self):
        '''
        @return: A string contaning the URL without the query string and
            without any path. 
        
        >>> u = URL('http://www.w3af.com/foo/bar.txt?id=3#foobar')
        >>> u.baseUrl().url_string
        u'http://www.w3af.com/'

        >>> u = URL('http://www.w3af.com')
        >>> u.baseUrl().url_string
        u'http://www.w3af.com/'
        '''
        params = (self.scheme, self.netloc, None, None, None, None)
        return URL.from_parts(*params, encoding=self._encoding)
    
    def normalizeURL(self):
        '''
        This method was added to be able to avoid some issues which are
        generated by the different way browsers and urlparser.urljoin
        join the URLs. A clear example of this is the following case:
            baseURL = 'http:/abc/'
            relativeURL = '/../f00.b4r'
    
        w3af would try to GET http:/abc/../f00.b4r; while mozilla would
        try to get http:/abc/f00.b4r. In some cases, the first is ok,
        on other cases the first one doesn't even work and return a 403
        error message.
    
        So, to sum up, this method takes an URL, and returns a normalized
        URL. For the example we were talking before, it will return:
            'http://abc/f00.b4r'
        instead of the normal response from urlparser.urljoin:
            'http://abc/../f00.b4r'
    
        Added later: Before performing anything, I also normalize the
        net location part of the URL.
        In some web apps we see things like:
            - http://host.tld:80/foo/bar
    
        As you may have noticed, the ":80" is redundant, and what's even
        worse, it can confuse w3af because in most cases
        http://host.tld:80/foo/bar != http://host.tld/foo/bar , and 
        http://host.tld/foo/bar could also be found by the web_spider
        plugin, so we are analyzing the same thing twice.
    
        So, before the path normalization, I perform a small net location
        normalization that transforms:
        
        >>> u = URL('http://host.tld:80/foo/bar')
        >>> u.normalizeURL()
        >>> u.url_string
        u'http://host.tld/foo/bar'
        
        >>> u = URL('https://host.tld:443/foo/bar')
        >>> u.normalizeURL()
        >>> u.url_string
        u'https://host.tld/foo/bar'
        
        >>> u = URL('https://host.tld:443////////////////')
        >>> u.normalizeURL()
        >>> u.url_string
        u'https://host.tld/'

        >>> u = URL('https://host.tld:443////////////////?id=3&bar=4')
        >>> u.normalizeURL()
        >>> u.url_string
        u'https://host.tld/?id=3&bar=4'

        >>> u = URL('http://w3af.com/../f00.b4r?id=3&bar=4')
        >>> u.normalizeURL()
        >>> u.url_string
        u'http://w3af.com/f00.b4r?id=3&bar=4'

        >>> u = URL('http://w3af.com/f00.b4r?id=3&bar=//')
        >>> u.normalizeURL()
        >>> u.url_string
        u'http://w3af.com/f00.b4r?id=3&bar=//'

        >>> u = URL('http://user:passwd@host.tld:80')
        >>> u.normalizeURL()
        >>> u.url_string
        u'http://user:passwd@host.tld/'
        
        >>> u = URL('http://w3af.com/../f00.b4r')
        >>> u.normalizeURL()
        >>> u.url_string
        u'http://w3af.com/f00.b4r'
        
        >>> u = URL('http://w3af.com/abc/../f00.b4r')
        >>> u.normalizeURL()
        >>> u.url_string
        u'http://w3af.com/f00.b4r'
        
        >>> u = URL('http://w3af.com/a//b/f00.b4r')
        >>> u.normalizeURL()
        >>> u.url_string
        u'http://w3af.com/a/b/f00.b4r'
        
        >>> u = URL('http://w3af.com/../../f00.b4r')
        >>> u.normalizeURL()
        >>> u.url_string
        u'http://w3af.com/f00.b4r'
        
        # IPv6 support
        >>> u = URL('http://fe80:0:0:0:202:b3ff:fe1e:8329/')
        >>> u.normalizeURL()
        >>> u.url_string
        u'http://fe80:0:0:0:202:b3ff:fe1e:8329/'
        
        '''
        # net location normalization:
        net_location = self.getNetLocation()
        protocol = self.getProtocol()
    
        # We may have auth URLs like <http://user:passwd@host.tld:80>.
        # Notice the ":" duplication. We'll be interested in transforming
        # 'net_location' beginning in the last appereance of ':'
        at_symb_index = net_location.rfind('@')
        colon_symb_max_index = net_location.rfind(':')
        # Found
        if colon_symb_max_index > at_symb_index:
    
            host = net_location[:colon_symb_max_index]
            port = net_location[(colon_symb_max_index + 1):]
    
            # Assign default port if nondigit.
            if not port.isdigit():
                if protocol == 'https':
                    port = '443'
                else:
                    port = '80'
    
            if (protocol == 'http' and port == '80') or \
                (protocol == 'https' and port == '443'):
                net_location = host
            else:
                # The net location has a specific port definition
                net_location = host + ':' + port
    
        # A normalized baseURL:
        base_url = protocol + '://' + net_location + '/'
    
        # Now normalize the path:
        path = self.path
        trailer_slash = path.endswith('/')

        tokens = []
        for p in path.split('/'):
            if not p:
                continue
            elif p != '..':
                tokens.append(p)
            else:
                if tokens:
                    tokens.pop()
        self.path = '/'.join(tokens) + ('/' if trailer_slash else '')
        
        # Put everything together
        fixed_url = urlparse.urljoin(base_url, self.getPathQs())

        # "re-init" the object 
        (self.scheme, self.netloc, self.path,
         self.params, self.querystring, self.fragment) = \
                                            urlparse.urlparse(fixed_url)
    
    def getPort(self):
        '''
        @return: The TCP port that is going to be used to contact the remote end.

        >>> u = URL('http://w3af.com/f00.b4r')
        >>> u.getPort()
        80
        >>> u = URL('http://w3af.com:80/f00.b4r')
        >>> u.getPort()
        80
        >>> u = URL('http://w3af.com:443/f00.b4r')
        >>> u.getPort()
        443
        >>> u = URL('https://w3af.com/f00.b4r')
        >>> u.getPort()
        443
        >>> u = URL('https://w3af.com:443/f00.b4r')
        >>> u.getPort()
        443
        >>> u = URL('https://w3af.com:80/f00.b4r')
        >>> u.getPort()
        80

        '''
        net_location = self.getNetLocation()
        protocol = self.getProtocol()
        if ':' in net_location:
            host,  port = net_location.split(':')
            return int(port)
        else:
            if protocol.lower() == 'http':
                return 80
            elif protocol.lower() == 'https':
                return 443
            else:
                # Just in case...
                return 80
                
    def urlJoin(self, relative, encoding=None):
        '''
        Construct a full (''absolute'') URL by combining a ''base URL'' (self)
        with a ``relative URL'' (relative). Informally, this uses components
        of the base URL, in particular the addressing scheme, the network
        location and (part of) the path, to provide missing components in the
        relative URL.
    
        For more information read RFC 1808 especially section 5.
        
        @param relative: The relative url to add to the base url
        @param encoding: The encoding to use for the final url_object being returned.
                         If no encoding is specified, the returned url_object will
                         have the same encoding that the current url_object.
        @return: The joined URL.

        Examples:
        
        >>> u = URL('http://w3af.com/foo.bar')
        >>> u.urlJoin('abc.html').url_string
        u'http://w3af.com/abc.html'
        >>> u.urlJoin('/abc.html').url_string
        u'http://w3af.com/abc.html'

        >>> u = URL('http://w3af.com/')
        >>> u.urlJoin('/abc.html').url_string
        u'http://w3af.com/abc.html'
        >>> u.urlJoin('/def/abc.html').url_string
        u'http://w3af.com/def/abc.html'

        >>> u = URL('http://w3af.com/def/jkl/')
        >>> u.urlJoin('/def/abc.html').url_string
        u'http://w3af.com/def/abc.html'
        >>> u.urlJoin('def/abc.html').url_string
        u'http://w3af.com/def/jkl/def/abc.html'

        >>> u = URL('http://w3af.com:8080/')
        >>> u.urlJoin('abc.html').url_string
        u'http://w3af.com:8080/abc.html'

        >>> u = URL('http://w3af.com/def/')
        >>> u.urlJoin(u'тест').url_string == u'http://w3af.com/def/тест'
        True

        
        Opera and Chrome behave like this. For those browsers the URL
        leads to no good, so I'm going to do the same thing. If the user
        wants to specify a URL that contains a colon he should URL
        encode it.
        
        >>> u = URL('http://w3af.com/')
        >>> u.urlJoin("d:url.html?id=13&subid=3")
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        ValueError: Invalid URL "d:url.html?id=13&subid=3"


        '''
        resp_encoding = encoding if encoding is not None else self._encoding
        joined_url = urlparse.urljoin(self.url_string, relative)
        jurl_obj = URL(joined_url, resp_encoding)
        jurl_obj.normalizeURL()
        return jurl_obj
    
    def getDomain(self):
        '''
        >>> URL('http://w3af.com/def/jkl/').getDomain()
        'w3af.com'
        >>> URL('http://1.2.3.4/def/jkl/').getDomain()
        '1.2.3.4'
        >>> URL('http://555555/def/jkl/').getDomain()
        '555555'
        >>> URL('http://foo.bar.def/def/jkl/').getDomain()
        'foo.bar.def'
    
        @return: Returns the domain name for the url.
        '''
        domain = self.netloc.split(':')[0]
        return domain

    @set_changed
    def setDomain(self, new_domain):
        '''
        >>> u = URL('http://w3af.com/def/jkl/')
        >>> u.getDomain()
        'w3af.com'

        >>> u.setDomain('host.tld')
        >>> u.getDomain()
        'host.tld'

        >>> u.setDomain('foobar')
        >>> u.getDomain()
        'foobar'

        >>> u.setDomain('foobar.')
        >>> u.getDomain()
        'foobar.'

        >>> u.setDomain('foobar:443')
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        ValueError: 'foobar:443' is an invalid domain

        >>> u.setDomain('foo*bar')
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        ValueError: 'foo*bar' is an invalid domain

        >>> u.setDomain('')
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        ValueError: '' is an invalid domain

        >>> u = URL('http://w3af.com:443/def/jkl/')
        >>> u.getDomain()
        'w3af.com'
        >>> u.setDomain('host.tld')
        >>> u.getNetLocation()
        'host.tld:443'
    
        @return: Returns the domain name for the url.
        '''
        if not re.match('[a-z0-9-\.]+([a-z0-9-]+)*$', new_domain):
            raise ValueError("'%s' is an invalid domain" % (new_domain))
        
        domain = self.netloc.split(':')[0]
        self.netloc = self.netloc.replace(domain, new_domain)
    
    def is_valid_domain(self):
        '''
        >>> URL("http://1.2.3.4").is_valid_domain()
        True
        >>> URL("http://aaa.com").is_valid_domain()
        True
        >>> URL("http://aaa.").is_valid_domain()
        False
        >>> URL("http://aaa*a").is_valid_domain()
        False
        >>> URL("http://aa-bb").is_valid_domain()
        True
        >>> URL("http://w3af.com").is_valid_domain()
        True
        >>> URL("http://w3af.com:39").is_valid_domain()
        True
        >>> URL("http://w3af.com:").is_valid_domain()
        False
        >>> URL("http://w3af.com:3932").is_valid_domain()
        True
        >>> URL("http://abc:3932322").is_valid_domain()
        False
        >>> URL("http://f.o.o.b.a.r.s.p.a.m.e.g.g.s").is_valid_domain()
        True
        
        @param url: The url to parse.
        @return: Returns a boolean that indicates if <url>'s domain is valid
        '''
        return re.match('[a-z0-9-]+(\.[a-z0-9-]+)*(:\d\d?\d?\d?\d?)?$', self.netloc) is not None
    
    def getNetLocation( self ):
        '''
        >>> URL("http://1.2.3.4").getNetLocation()
        '1.2.3.4'
        >>> URL("http://aaa.com:80").getNetLocation()
        'aaa.com:80'
        >>> URL("http://aaa:443").getNetLocation()
        'aaa:443'
    
        @return: Returns the net location for the url.
        '''
        return self.netloc
    
    def getProtocol( self ):
        '''
        >>> URL("http://1.2.3.4").getProtocol()
        'http'
        >>> URL("https://aaa.com:80").getProtocol()
        'https'
        >>> URL("ftp://aaa:443").getProtocol()
        'ftp'

        @return: Returns the domain name for the url.
        '''
        return self.scheme

    @set_changed    
    def setProtocol( self, protocol ):
        '''
        >>> u = URL("http://1.2.3.4")
        >>> u.getProtocol()
        'http'
        >>> u.setProtocol('https')
        >>> u.getProtocol()
        'https'

        @return: Returns the domain name for the url.
        '''
        self.scheme = protocol

    def getRootDomain( self ):
        '''
        Get the root domain name. Examples:
        
        input: www.ciudad.com.ar
        output: ciudad.com.ar
        
        input: i.love.myself.ru
        output: myself.ru
        
        Code taken from: http://getoutfoxed.com/node/41

        >>> URL("http://1.2.3.4").getRootDomain()
        '1.2.3.4'
        >>> URL("https://aaa.com:80").getRootDomain()
        'aaa.com'
        >>> URL("http://aaa.com").getRootDomain()
        'aaa.com'
        >>> URL("http://www.aaa.com").getRootDomain()
        'aaa.com'
        >>> URL("http://mail.aaa.com").getRootDomain()
        'aaa.com'
        >>> URL("http://foo.bar.spam.eggs.aaa.com").getRootDomain()
        'aaa.com'
        >>> URL("http://foo.bar.spam.eggs.aaa.com.ar").getRootDomain()
        'aaa.com.ar'
        >>> URL("http://foo.aaa.com.ar").getRootDomain()
        'aaa.com.ar'
        >>> URL("http://foo.aaa.edu.sz").getRootDomain()
        'aaa.edu.sz'

        '''
        # break authority into two parts: subdomain(s), and base authority
        # e.g. images.google.com --> [images, google.com]
        #      www.popo.com.au --> [www, popo.com.au]
        def splitAuthority(aAuthority):
        
            # walk down from right, stop at (but include) first non-toplevel domain
            chunks = re.split("\.",aAuthority)
            chunks.reverse()
            
            baseAuthority=""
            subdomain=""
            foundBreak = 0
            
            for chunk in chunks:
                if (not foundBreak):
                    baseAuthority = chunk + (".","")[baseAuthority==""] + baseAuthority
                else:
                    subdomain = chunk  + (".","")[subdomain==""] + subdomain
                if chunk not in GTOP_LEVEL_DOMAINS:
                    foundBreak=1
            return ([subdomain,baseAuthority])
        
        # def to split URI into its parts, returned as URI object
        def decomposeURI():
            return splitAuthority(self.getDomain())[1]
                
        if is_ip_address(self.netloc):
            # An IP address has no "root domain" 
            return self.netloc
        else:
            return decomposeURI()
            
    def getDomainPath( self ):
        '''
        @return: Returns the domain name and the path for the url.
    
        >>> URL('http://w3af.com/def/jkl/').getDomainPath().url_string
        u'http://w3af.com/def/jkl/'
        >>> URL('http://w3af.com/def.html').getDomainPath().url_string
        u'http://w3af.com/'
        >>> URL('http://w3af.com/xyz/def.html').getDomainPath().url_string
        u'http://w3af.com/xyz/'
        >>> URL('http://w3af.com:80/xyz/def.html').getDomainPath().url_string
        u'http://w3af.com:80/xyz/'
        >>> URL('http://w3af.com:443/xyz/def.html').getDomainPath().url_string
        u'http://w3af.com:443/xyz/'
        >>> URL('https://w3af.com:443/xyz/def.html').getDomainPath().url_string
        u'https://w3af.com:443/xyz/'
        >>> URL('http://w3af.com').getDomainPath().url_string
        u'http://w3af.com/'
        '''
        if self.path:
            res = self.scheme + '://' +self.netloc+ self.path[:self.path.rfind('/')+1]
        else:
            res = self.scheme + '://' +self.netloc+ '/'
        return URL(res, self._encoding)
    
    def getFileName( self ):
        '''
        @return: Returns the filename name for the given url.
    
        >>> URL('https://w3af.com:443/xyz/def.html').getFileName()
        'def.html'
        >>> URL('https://w3af.com:443/xyz/').getFileName()
        ''
        >>> URL('https://w3af.com:443/xyz/d').getFileName()
        'd'
        '''
        return self.path[self.path.rfind('/')+1:]

    @set_changed
    def setFileName( self, new ):
        '''
        @return: Sets the filename name for the given URL.
    
        >>> u = URL('https://w3af.com:443/xyz/def.html')
        >>> u.setFileName( 'abc.pdf' )
        >>> u.url_string
        'https://w3af.com:443/xyz/abc.pdf'
        >>> u.getFileName()
        'abc.pdf'
        
        >>> u = URL('https://w3af.com:443/xyz/def.html?id=1')
        >>> u.setFileName( 'abc.pdf' )
        >>> u.url_string
        'https://w3af.com:443/xyz/abc.pdf?id=1'

        >>> u = URL('https://w3af.com:443/xyz/def.html?file=/etc/passwd')
        >>> u.setFileName( 'abc.pdf' )
        >>> u.url_string
        'https://w3af.com:443/xyz/abc.pdf?file=/etc/passwd'

        >>> u = URL('https://w3af.com/')
        >>> u.setFileName( 'abc.pdf' )
        >>> u.url_string
        'https://w3af.com/abc.pdf'
        '''
        if self.path == '/':
            self.path = '/' + new
        
        else:
            last_slash = self.path.rfind('/')
            self.path = self.path[:last_slash+1] + new
    
    def getExtension( self ):
        '''
        @return: Returns the extension of the filename, if possible, else, ''.
        
        >>> URL('https://w3af.com:443/xyz/d').getExtension()
        ''
        >>> URL('https://w3af.com:443/xyz/d.html').getExtension()
        'html'
        >>> URL('https://w3af.com:443/xyz/').getExtension()
        ''
        '''
        fname = self.getFileName()
        extension = fname[ fname.rfind('.') +1 :]
        if extension == fname:
            return ''
        else:
            return extension

    @set_changed    
    def setExtension( self, extension ):
        '''
        @param extension: The new extension to set, without the '.'
        @return: None. The extension is set. An exception is raised if the
        original URL had no extension.
        
        >>> URL('https://www.w3af.com/xyz/foo').setExtension('xml')
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        Exception: You can only set a new extension to a URL that had one.

        >>> u = URL('https://w3af.com:443/xyz/d.html')
        >>> u.setExtension('xml')
        >>> u.getExtension()
        'xml'
        
        >>> u = URL('https://w3af.com:443/xyz/d.html?id=3')
        >>> u.setExtension('xml')
        >>> u.getExtension()
        'xml'

        >>> u = URL('https://w3af.com:443/xyz/d.html.foo?id=3')
        >>> u.setExtension('xml')
        >>> u.getExtension()
        'xml'
        >>> u.url_string
        'https://w3af.com:443/xyz/d.html.xml?id=3'

        '''
        if not self.getExtension():
            raise Exception('You can only set a new extension to a URL that had one.')
        
        filename = self.getFileName()
        
        split_filename = filename.split('.')
        split_filename[-1] = extension
        new_filename = '.'.join(split_filename)
        
        self.setFileName(new_filename)

    def allButScheme( self ):
        '''
        >>> URL('https://w3af.com:443/xyz/').allButScheme()
        'w3af.com:443/xyz/'
        >>> URL('https://w3af.com:443/xyz/file.asp').allButScheme()
        'w3af.com:443/xyz/'

        @return: Returns the domain name and the path for the url.
        '''
        return self.netloc+ self.path[:self.path.rfind('/')+1]
    
    def getPath( self ):
        '''
        >>> URL('https://w3af.com:443/xyz/file.asp').getPath()
        '/xyz/file.asp'
        >>> URL('https://w3af.com:443/xyz/file.asp?id=-2').getPath()
        '/xyz/file.asp'
        >>> URL('https://w3af.com:443/xyz/').getPath()
        '/xyz/'
        >>> URL('https://w3af.com:443/xyz/123/456/789/').getPath()
        '/xyz/123/456/789/'
        >>> URL('https://w3af.com:443/').getPath()
        '/'

        @return: Returns the path for the url:
        '''
        return self.path

    @set_changed    
    def setPath(self, path):
        self.path = path or u'/'

    def getPathWithoutFile( self ):
        '''
        >>> URL('https://w3af.com:443/xyz/file.asp').getPathWithoutFile()
        '/xyz/'
        >>> URL('https://w3af.com:443/xyz/').getPathWithoutFile()
        '/xyz/'
        >>> URL('https://w3af.com:443/xyz/123/456/789/').getPathWithoutFile()
        '/xyz/123/456/789/'

        @return: Returns the path for the url:
        '''
        path = self.getPath()
        filename = self.getFileName()
        return path.replace(filename, '', 1)
    
    def getPathQs(self):
        '''
        >>> URL(u'https://w3af.com:443/xyz/123/456/789/').getPath()
        u'/xyz/123/456/789/'
        >>> URL(u'https://w3af.com:443/xyz/123/456/789/').getPathQs()
        u'/xyz/123/456/789/'
        >>> URL(u'https://w3af.com:443/xyz/file.asp').getPathQs()
        u'/xyz/file.asp'
        >>> URL(u'https://w3af.com:443/xyz/file.asp?id=1').getPathQs()
        u'/xyz/file.asp?id=1'
    
        @return: Returns the domain name and the path for the url.
        '''
        res = self.path
        if self.params != '':
            res += ';' + self.params
        if self.hasQueryString():
            res += u'?' + unicode(self.querystring)
        return res
    
    def urlDecode(self):
        '''
        @see: Unittests at test_urlParser
        @return: A URL that represents the current URL without URL
                 encoded characters.
        '''
        unquotedurl = urllib.unquote(str(self))
        enc = self._encoding
        return URL(unquotedurl.decode(enc, 'ignore'), enc)
    
    def urlEncode(self):
        '''
        @see: Unittests at test_urlParser
        @return: String that represents the current URL
        '''
        self_str = str(self)
        qs = ''
        qs_start_index = self_str.find('?')
        
        if qs_start_index > -1:
            qs = '?' + str(self.querystring)
            self_str = self_str[:qs_start_index]
        
        return "%s%s" % (urllib.quote(self_str, safe=self.SAFE_CHARS), qs)
    
    def getDirectories( self ):
        '''
        Get a list of all directories and subdirectories.
        
        Test different path levels

        >>> [i.url_string for i in URL('http://w3af.com/xyz/def/123/').getDirectories()]
        [u'http://w3af.com/xyz/def/123/', u'http://w3af.com/xyz/def/', u'http://w3af.com/xyz/', u'http://w3af.com/']
        >>> [i.url_string for i in URL('http://w3af.com/xyz/def/').getDirectories()]
        [u'http://w3af.com/xyz/def/', u'http://w3af.com/xyz/', u'http://w3af.com/']
        >>> [i.url_string for i in URL('http://w3af.com/xyz/').getDirectories()]
        [u'http://w3af.com/xyz/', u'http://w3af.com/']
        >>> [i.url_string for i in URL('http://w3af.com/').getDirectories()]
        [u'http://w3af.com/']


        Test with a filename

        >>> [i.url_string for i in URL('http://w3af.com/def.html').getDirectories()]
        [u'http://w3af.com/']

        Test with a filename and a QS

        >>> [i.url_string for i in URL('http://w3af.com/def.html?id=5').getDirectories()]
        [u'http://w3af.com/']
        >>> [i.url_string for i in URL('http://w3af.com/def.html?id=/').getDirectories()]
        [u'http://w3af.com/']
        '''
        res = []
        
        current_url = self.copy()
        res.append(current_url.getDomainPath())

        while current_url.getPath().count('/') != 1:
            current_url = current_url.urlJoin('../')
            res.append(current_url)
        
        return res
    
    def hasParams( self ):
        '''
        Analizes the url to check for a params

        >>> URL('http://w3af.com/').hasParams()
        False
        >>> URL('http://w3af.com/;id=1').hasParams()
        True
        >>> URL('http://w3af.com/?id=3;id=1').hasParams()
        False
        >>> URL('http://w3af.com/;id=1?id=3').hasParams()
        True
        >>> URL('http://w3af.com/foobar.html;id=1?id=3').hasParams()
        True
    
        @return: True if the URL has params.
        '''
        if self.params != '':
            return True
        return False
    
    def getParamsString(self):
        '''
        >>> URL(u'http://w3af.com/').getParamsString()
        u''
        >>> URL(u'http://w3af.com/;id=1').getParamsString()
        u'id=1'
        >>> URL(u'http://w3af.com/?id=3;id=1').getParamsString()
        u''
        >>> URL(u'http://w3af.com/;id=1?id=3').getParamsString()
        u'id=1'
        >>> URL(u'http://w3af.com/foobar.html;id=1?id=3').getParamsString()
        u'id=1'
    
        @return: Returns the params inside the url.
        '''
        return self.params
    
    def removeParams(self):
        '''
        @return: Returns a new url object contaning the URL without the parameter. Example :

        >>> URL('http://w3af.com/').removeParams().url_string
        u'http://w3af.com/'
        >>> URL('http://w3af.com/def.txt').removeParams().url_string
        u'http://w3af.com/def.txt'
        >>> URL('http://w3af.com/;id=1').removeParams().url_string
        u'http://w3af.com/'
        >>> URL('http://w3af.com/;id=1&file=2').removeParams().url_string
        u'http://w3af.com/'
        >>> URL('http://w3af.com/;id=1?file=2').removeParams().url_string
        u'http://w3af.com/?file=2'
        >>> URL('http://w3af.com/xyz.txt;id=1?file=2').removeParams().url_string
        u'http://w3af.com/xyz.txt?file=2'

        '''
        parts = (self.scheme, self.netloc, self.path,
                 None, unicode(self.querystring), self.fragment)
        return URL.from_parts(*parts, encoding=self._encoding)
    
    @set_changed
    def setParam( self, param_string ):
        '''
        >>> u = URL('http://w3af.com/;id=1')
        >>> u.setParam('file=2')
        >>> u.getParamsString()
        'file=2'
        >>> u = URL('http://w3af.com/xyz.txt;id=1?file=2')
        >>> u.setParam('file=3')
        >>> u.getParamsString()
        'file=3'
        >>> u.getPathQs()
        '/xyz.txt;file=3?file=2'
        
        @param param_string: The param to set (e.g. "foo=aaa").
        @return: Returns the url containing param.
        '''
        self.params = param_string 
        
    def getParams(self, ignore_exc=True):
        '''
        Parses the params string and returns a dict.
    
        @return: A QueryString object.

        >>> u = URL('http://w3af.com/xyz.txt;id=1?file=2')
        >>> u.getParams()
        {'id': '1'}
        >>> u = URL('http://w3af.com/xyz.txt;id=1&file=2?file=2')
        >>> u.getParams()
        {'id': '1', 'file': '2'}
        >>> u = URL('http://w3af.com/xyz.txt;id=1&file=2?spam=2')
        >>> u.getParams()
        {'id': '1', 'file': '2'}
        >>> u = URL('http://w3af.com/xyz.txt;id=1&file=2?spam=3')
        >>> u.getParams()
        {'id': '1', 'file': '2'}

        '''
        parsedData = None
        result = {}
        if self.hasParams():
            try:
                parsedData = urlparse.parse_qs(self.params,
                                  keep_blank_values=True, strict_parsing=True)
            except Exception:
                if not ignore_exc:
                    raise w3afException('Strange things found when parsing '
                                        'params string: ' + self.params)
            else:
                for k, v in parsedData.iteritems():
                    result[k] = v[0]
        return result
    
    def __iter__(self):
        '''
        Return iterator for self.url_string
        
        >>> url = u'http://w3af.com/xyz.txt;id=1?file=2'
        >>> url_obj = URL(url)
        >>> ''.join(chr for chr in url_obj) == url
        True
        '''
        return iter(self.url_string)

    def __eq__(self, other):
        '''
        @return: True if the url_strings are equal
        '''
        return isinstance(other, URL) and \
                self.url_string == other.url_string
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        '''
        >>> u1 = URL('http://w3af.com/')
        >>> u2 = URL('http://w3af.com/def.htm')
        >>> test = [u1, u2]
        >>> len( list( set( test ) ) )
        2
        >>> u1 = URL('http://w3af.com/')
        >>> u2 = URL('http://w3af.com/')
        >>> test = [u1, u2]
        >>> len( list( set( test ) ) )
        1
        '''
        return hash(self.url_string)

    def __str__(self):
        '''
        @return: A string representation of myself

        >>> str(URL('http://w3af.com/xyz.txt;id=1?file=2'))
        'http://w3af.com/xyz.txt;id=1?file=2'
        >>> str(URL('http://w3af.com:80/'))
        'http://w3af.com:80/'
        >>> str(URL(u'http://w3af.com/indéx.html', 'latin1')) == \
        u'http://w3af.com/indéx.html'.encode('latin1')
        True
        '''
        urlstr = smart_str(
                       self.url_string,
                       self._encoding,
                       errors=PERCENT_ENCODE
                    )
        return urlstr.replace(' ', '%20')
        
    def __unicode__(self):
        '''
        @return: A unicode representation of myself
        
        >>> unicode(URL('http://w3af.com:80/'))
        u'http://w3af.com:80/'
        >>> unicode(URL(u'http://w3af.com/indéx.html', 'latin1')) == \
        u'http://w3af.com/indéx.html'
        True
        '''
        return self.url_string

    def __repr__(self):
        '''
        @return: A string representation of myself for debugging

        '''
        return '<URL for "%s">' % (self,)

    def __contains__(self, s):
        '''
        @return: True if "s" in url_string

        >>> u = URL('http://w3af.com/xyz.txt;id=1?file=2')
        >>> '1' in u
        True
        
        >>> u = URL('http://w3af.com/xyz.txt;id=1?file=2')
        >>> 'file=2' in u
        True

        >>> u = URL('http://w3af.com/xyz.txt;id=1?file=2')
        >>> 'hello!' in u
        False
        '''
        return s in self.url_string
    
    def __add__(self, other):
        '''
        @return: This URL concatenated with the "other" string.
        
        >>> u = URL('http://www.w3af.com/')
        >>> x = u + 'abc'
        >>> x
        u'http://www.w3af.com/abc'

        >>> u = URL('http://www.w3af.com/')
        >>> x = u + ' hello world!'
        >>> x
        u'http://www.w3af.com/ hello world!'

        >>> u = URL('http://www.w3af.com/')
        >>> x = u + 1
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        TypeError: cannot concatenate 'int' and 'URL' objects
        
        '''
        if not isinstance(other, basestring):
            msg = "cannot concatenate '%s' and '%s' objects"
            msg = msg % ( other.__class__.__name__, self.__class__.__name__)
            raise TypeError(msg)
        
        return self.url_string + other 

    def __nonzero__(self):
        '''
        Always evaluate as True
        
        >>> bool(URL('http://www.w3af.com'))
        True
        '''
        return True
        
    def __radd__(self, other):
        '''
        @return: The "other" string concatenated with this URL.
        
        >>> u = URL('http://www.w3af.com/')
        >>> x = 'abc' + u
        >>> x
        u'abchttp://www.w3af.com/'

        >>> u = URL('http://www.w3af.com/')
        >>> x = 'hello world! ' + u
        >>> x
        u'hello world! http://www.w3af.com/'

        >>> u = URL('http://www.w3af.com/')
        >>> x = 1 + u
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        TypeError: cannot concatenate 'int' and 'URL' objects
        
        '''
        if not isinstance(other, basestring):
            msg = "cannot concatenate '%s' and '%s' objects"
            msg = msg % ( other.__class__.__name__, self.__class__.__name__)
            raise TypeError(msg)
        
        return other + self.url_string

    def copy(self):
        return copy.deepcopy(self)

    def get_eq_attrs(self):
        return ['url_string']
