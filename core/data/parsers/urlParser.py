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

from core.data.dc.queryString import queryString
import core.data.kb.config as cf

from core.controllers.w3afException import w3afException
import core.controllers.outputManager as om
from core.controllers.misc.is_ip_address import is_ip_address

import urlparse
import urllib
import cgi
import re
import string
import copy


def set_changed(meth):
    '''
    Function to decorate methods in order to set the "self._changed" attribute
    of the object to True.
    '''
    def wrapper(self, *args, **kwargs):
        self._changed = True
        return meth(self, *args, **kwargs)

    return wrapper


def parse_qs( url_encoded_string, ignoreExceptions=True ):
    '''
    Parse a url encoded string (a=b&c=d) into a queryString object.
    
    @param url_encoded_string: The string to parse
    @return: A queryString object (a dict wrapper). 

    >>> parse_qs('id=3')
    {'id': ['3']}
    >>> parse_qs('id=3&id=4')
    {'id': ['3', '4']}
    >>> parse_qs('id=3&ff=4&id=5')
    {'id': ['3', '5'], 'ff': ['4']}

    '''
    parsed_qs = None
    result = queryString()

    if url_encoded_string:
        try:
            parsed_qs = cgi.parse_qs( url_encoded_string ,keep_blank_values=True,strict_parsing=False)
        except Exception, e:
            if not ignoreExceptions:
                raise w3afException('Strange things found when parsing query string: "' + qs + '"')
        else:
            #
            #   Before we had something like this:
            #
            #for i in parsed_qs.keys():
            #    result[ i ] = parsed_qs[ i ][0]
            #
            #   But with that, we fail to handle web applications that use "duplicated parameter
            #   names". For example: http://host.tld/abc?sp=1&sp=2&sp=3
            #
            #   (please note the lack of [0]) , and that if the value isn't a list... 
            #    I create an artificial list
            for p, v in parsed_qs.iteritems():
                if type(v) is not list:
                    v = [v]
                result[p] = v
                
    return result


class url_object(object):
    '''
    This class represents a URL and gives access to all its parts
    with several "getter" methods.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self, data):
        '''
        @param data: Either a string representing a URL or a 6-elems tuple
            representing the URL components:
            <scheme>://<netloc>/<path>;<params>?<query>#<fragment>

        Simple generic test, more detailed tests in each method!
        
        >>> u = url_object('http://www.google.com/foo/bar.txt')
        >>> u.path
        '/foo/bar.txt'
        >>> u.scheme
        'http'
        >>> u.getFileName()
        'bar.txt'
        >>> u.getExtension()
        'txt'
        >>> 
        >>> u = url_object('www.google.com')
        >>> u.getDomain()
        'www.google.com'
        >>> u.getProtocol()
        'http'
        '''
        self._already_calculated_url = None
        self._changed = True

        if type(data) is tuple:
            scheme, netloc, path, params, qs, fragment = data
        else:
            scheme, netloc, path, params, qs, fragment = \
                                        urlparse.urlparse(data)
            #
            # This is the case when someone creates a url_object like
            # this: url_object('www.w3af.com')
            #
            if scheme == netloc == '' and path:
                # By default we set the protocol to "http"
                scheme = 'http'
                netloc = path
                path = ''
            
        self.scheme = scheme or ''
        self.netloc = netloc or ''
        self.path = path or ''
        self.params = params or ''
        self.qs = qs or ''
        self.fragment = fragment or ''

    @classmethod
    def from_parts(cls, scheme, netloc, path, params, qs, fragment):
        '''
        @param scheme: http/https
        @param netloc: domain and port
        @param path: directory
        @param params: URL params
        @param qs: query string
        @param fragment: #fragments
        @return: An instance of url_object.

        This is a "constructor" for the url_object class.
        
        >>> u = url_object.from_parts('http', 'www.google.com', '/foo/bar.txt', None, 'a=b', 'frag')
        >>> u.path
        '/foo/bar.txt'
        >>> u.scheme
        'http'
        >>> u.getFileName()
        'bar.txt'
        >>> u.getExtension()
        'txt'
        >>> 

        '''
        return cls((scheme, netloc, path, params, qs, fragment))

    @classmethod
    def from_url_object( cls, original_url_object ):
        '''
        @param original_url_object: The url object to use as "template" for the new one
        @return: An instance of url_object with the same data as original_url_object

        This is a "constructor" for the url_object class.
        
        >>> o = url_object('http://www.google.com/foo/bar.txt')
        >>> u = url_object.from_url_object( o )
        >>> u.path
        '/foo/bar.txt'
        >>> u.scheme
        'http'
        >>> u.getFileName()
        'bar.txt'
        >>> u.getExtension()
        'txt'
        >>> 
        >>> u = url_object('www.google.com')
        >>> u.getDomain()
        'www.google.com'
        >>> u.getProtocol()
        'http'

        '''
        scheme = original_url_object.getProtocol()
        netloc = original_url_object.getDomain()
        path = original_url_object.getPath()
        params = original_url_object.getParams()
        qs = copy.deepcopy( original_url_object.getQueryString() )
        fragment = original_url_object.getFragment()
        return cls((scheme, netloc, path, params, qs, fragment))

    @property
    def url_string(self):
        if self._changed or self._already_calculated_url is None:
            self._already_calculated_url = urlparse.urlunparse( (self.scheme, self.netloc, self.path, self.params, self.qs, self.fragment) )
            self._changed = False
            return self._already_calculated_url
        else:
            return self._already_calculated_url

       
    def hasQueryString( self ):
        '''
        Analyzes the uri to check for a query string.
        
        >>> u = url_object('http://www.google.com/foo/bar.txt')
        >>> u.hasQueryString()
        False
        >>> u = url_object('http://www.google.com/foo/bar.txt?id=1')
        >>> u.hasQueryString()
        True
        >>> u = url_object('http://www.google.com/foo/bar.txt;par=3')
        >>> u.hasQueryString()
        False
    
        @return: True if self has a query string.
        '''
        if self.qs != '':
            return True
        return False
    
    def getQueryString( self, ignoreExceptions=True ):
        '''
        Parses the query string and returns a dict.
    
        @return: A QueryString Object that represents the query string.

        >>> u = url_object('http://www.google.com/foo/bar.txt?id=3')
        >>> u.getQueryString()
        {'id': ['3']}
        >>> u = url_object('http://www.google.com/foo/bar.txt?id=3&id=4')
        >>> u.getQueryString()
        {'id': ['3', '4']}
        >>> u = url_object('http://www.google.com/foo/bar.txt?id=3&ff=4&id=5')
        >>> u.getQueryString()
        {'id': ['3', '5'], 'ff': ['4']}
        
        '''
        return parse_qs( self.qs, ignoreExceptions=True )
    
    @set_changed
    def setQueryString(self, qs):
        '''
        Sets the query string for this URL.
        
        @return: None, the infor is set and nothing is returned.
        '''
        from core.data.dc.form import form
        if isinstance(qs, form):
            self.qs = str(qs)
            return

        if isinstance(qs, dict) and not isinstance(qs, queryString):
            qs = urllib.urlencode( qs )
            self.qs = str(qs)
            return
        
        self.qs = str(qs)
        
    def uri2url( self ):
        '''
        @return: Returns a string contaning the URL without the query string. Example :

        >>> u = url_object('http://www.google.com/foo/bar.txt?id=3')
        >>> u.uri2url().url_string
        'http://www.google.com/foo/bar.txt'
        >>> 
        '''
        return url_object.from_parts(self.scheme, self.netloc,
                                     self.path, None, None, None)
    
    def getFragment(self):
        '''
        @return: Returns the #fragment of the URL.
        '''
        return self.fragment
    
    def removeFragment( self ):
        '''
        @return: Returns a url_object containing the URL without the fragment. Example:
        
        >>> u = url_object('http://www.google.com/foo/bar.txt?id=3#foobar')
        >>> u.removeFragment().url_string
        'http://www.google.com/foo/bar.txt?id=3'
        >>> u = url_object('http://www.google.com/foo/bar.txt#foobar')
        >>> u.removeFragment().url_string
        'http://www.google.com/foo/bar.txt'
        '''
        return url_object.from_parts( self.scheme, self.netloc, self.path, self.params, self.qs, None )
    
    def baseUrl( self ):
        '''
        @return: Returns a string contaning the URL without the query string and without any path. 
        Example :
        
        >>> u = url_object('http://www.google.com/foo/bar.txt?id=3#foobar')
        >>> u.baseUrl().url_string
        'http://www.google.com'
        '''
        return url_object.from_parts( self.scheme, self.netloc, None, None, None, None )
    
    
    def normalizeURL( self ):
        '''
        This method was added to be able to avoid some issues which are generated
        by the different way browsers and urlparser.urljoin join the URLs. A clear
        example of this is the following case:
            baseURL = 'http:/abc/'
            relativeURL = '/../f00.b4r'
    
        w3af would try to GET http:/abc/../f00.b4r; while mozilla would try to
        get http:/abc/f00.b4r . In some cases, the first is ok, on other cases
        the first one doesn't even work and return a 403 error message.
    
        So, to sum up, this method takes an URL, and returns a normalized URL.
        For the example we were talking before, it will return:
        'http://abc/f00.b4r'
        instead of the normal response from urlparser.urljoin: 'http://abc/../f00.b4r'
    
        Added later: Before performing anything, I also normalize the net location part of the URL.
        In some web apps we see things like:
            - http://host.tld:80/foo/bar
    
        As you may have noticed, the ":80" is redundant, and what's even worse, it can confuse w3af because
        in most cases http://host.tld:80/foo/bar != http://host.tld/foo/bar , and http://host.tld/foo/bar could also be
        found by the webSpider plugin, so we are analyzing the same thing twice.
    
        So, before the path normalization, I perform a small net location normalization that transforms:
        
        >>> u = url_object('http://host.tld:80/foo/bar')
        >>> u.normalizeURL()
        >>> u.url_string
        'http://host.tld/foo/bar'
        
        >>> u = url_object('https://host.tld:443/foo/bar')
        >>> u.normalizeURL()
        >>> u.url_string
        'https://host.tld/foo/bar'
        
        >>> u = url_object('http://user:passwd@host.tld:80')
        >>> u.normalizeURL()
        >>> u.url_string
        'http://user:passwd@host.tld/'
        
        >>> u = url_object('http://abc/../f00.b4r')
        >>> u.normalizeURL()
        >>> u.url_string
        'http://abc/f00.b4r'
        
        >>> u = url_object('http://abc/../../f00.b4r')
        >>> u.normalizeURL()
        >>> u.url_string
        'http://abc/f00.b4r'
        '''
        # net location normalization:
        net_location = self.getNetLocation()
        protocol = self.getProtocol()
    
        # We may have auth URLs like <http://user:passwd@host.tld:80>. Notice the
        # ":" duplication. We'll be interested in transforming 'net_location'
        # beginning in the last appereance of ':'
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
        baseURL = protocol + '://' + net_location + '/'
    
        # Now normalize the path:
        relativeURL = self.getPathQs()
    
        commonjoin = urlparse.urljoin(baseURL, relativeURL)
        
        common_join_url = url_object(commonjoin)
        path = common_join_url.getPathQs()
    
        while path.startswith('../') or path.startswith('/../'):
            if path.startswith('../'):
                path = path[2:]
            elif path.startswith('/../'):
                path = path[3:]
    
        fixed_url = urlparse.urljoin(baseURL, path)
        
        #    "re-init" the object 
        self.scheme, self.netloc, self.path, self.params, self.qs, self.fragment = urlparse.urlparse( fixed_url )
    
    def getPort( self ):
        '''
        @return: The TCP port that is going to be used to contact the remote end.

        >>> u = url_object('http://abc/f00.b4r')
        >>> u.getPort()
        80
        >>> u = url_object('http://abc:80/f00.b4r')
        >>> u.getPort()
        80
        >>> u = url_object('http://abc:443/f00.b4r')
        >>> u.getPort()
        443
        >>> u = url_object('https://abc/f00.b4r')
        >>> u.getPort()
        443
        >>> u = url_object('https://abc:443/f00.b4r')
        >>> u.getPort()
        443
        >>> u = url_object('https://abc:80/f00.b4r')
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
                
    def urlJoin( self , relative ):
        '''
        Construct a full (''absolute'') URL by combining a ''base URL'' (self) with a ``relative URL'' (relative). 
        Informally, this uses components of the base URL, in particular the addressing scheme,
        the network location and (part of) the path, to provide missing components in the relative URL.
    
        For more information read RFC 1808 espeally section 5.
        
        @param relative: The relative url to add to the base url
        @return: The joined URL.

        Examples:
        
        >>> u = url_object('http://abc/foo.bar')
        >>> u.urlJoin('abc.html').url_string
        'http://abc/abc.html'
        >>> u.urlJoin('/abc.html').url_string
        'http://abc/abc.html'
        >>> u = url_object('http://abc/')
        >>> u.urlJoin('/abc.html').url_string
        'http://abc/abc.html'
        >>> u.urlJoin('/def/abc.html').url_string
        'http://abc/def/abc.html'
        >>> u = url_object('http://abc/def/jkl/')
        >>> u.urlJoin('/def/abc.html').url_string
        'http://abc/def/abc.html'
        >>> u.urlJoin('def/abc.html').url_string
        'http://abc/def/jkl/def/abc.html'
        >>> u = url_object('http://abc:8080/')
        >>> u.urlJoin('abc.html').url_string
        'http://abc:8080/abc.html'

        '''
        joined_url = urlparse.urljoin( self.url_string, relative )
        jurl_obj = url_object(joined_url)
        jurl_obj.normalizeURL()
        return jurl_obj
    
    def getDomain( self ):
        '''
        >>> url_object('http://abc/def/jkl/').getDomain()
        'abc'
        >>> url_object('http://1.2.3.4/def/jkl/').getDomain()
        '1.2.3.4'
        >>> url_object('http://555555/def/jkl/').getDomain()
        '555555'
        >>> url_object('http://foo.bar.def/def/jkl/').getDomain()
        'foo.bar.def'
    
        @return: Returns the domain name for the url.
        '''
        domain = self.netloc.split(':')[0]
        return domain

    @set_changed
    def setDomain( self, new_domain ):
        '''
        >>> u = url_object('http://abc/def/jkl/')
        >>> u.getDomain()
        'abc'

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
        TypeError: 'foobar:443' is an invalid domain

        >>> u.setDomain('foo*bar')
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        TypeError: 'foo*bar' is an invalid domain

        >>> u = url_object('http://abc:443/def/jkl/')
        >>> u.getDomain()
        'abc'
        >>> u.setDomain('host.tld')
        >>> u.getNetLocation()
        'host.tld:443'
    
        @return: Returns the domain name for the url.
        '''
        if re.match('[a-z0-9-\.]+([a-z0-9-]+)*$', new_domain ) is None:
            raise TypeError( "'%s' is an invalid domain" % (new_domain) )
        else:
            domain = self.netloc.split(':')[0]
            self.netloc = self.netloc.replace(domain, new_domain)
    
    def is_valid_domain( self ):
        '''
        >>> url_object("http://1.2.3.4").is_valid_domain()
        True
        >>> url_object("http://aaa.com").is_valid_domain()
        True
        >>> url_object("http://aaa.").is_valid_domain()
        False
        >>> url_object("http://aaa*a").is_valid_domain()
        False
        >>> url_object("http://aa-bb").is_valid_domain()
        True
        >>> url_object("http://abc").is_valid_domain()
        True
        >>> url_object("http://abc:39").is_valid_domain()
        True
        >>> url_object("http://abc:").is_valid_domain()
        False
        >>> url_object("http://abc:3932").is_valid_domain()
        True
        >>> url_object("http://abc:3932322").is_valid_domain()
        False
        >>> url_object("http://f.o.o.b.a.r.s.p.a.m.e.g.g.s").is_valid_domain()
        True
        
        @parameter url: The url to parse.
        @return: Returns a boolean that indicates if <url>'s domain is valid
        '''
        return re.match('[a-z0-9-]+(\.[a-z0-9-]+)*(:\d\d?\d?\d?\d?)?$', self.netloc ) is not None
    
    def getNetLocation( self ):
        '''
        >>> url_object("http://1.2.3.4").getNetLocation()
        '1.2.3.4'
        >>> url_object("http://aaa.com:80").getNetLocation()
        'aaa.com:80'
        >>> url_object("http://aaa:443").getNetLocation()
        'aaa:443'
    
        @return: Returns the net location for the url.
        '''
        return self.netloc
    
    def getProtocol( self ):
        '''
        >>> url_object("http://1.2.3.4").getProtocol()
        'http'
        >>> url_object("https://aaa.com:80").getProtocol()
        'https'
        >>> url_object("ftp://aaa:443").getProtocol()
        'ftp'

        @return: Returns the domain name for the url.
        '''
        return self.scheme

    @set_changed    
    def setProtocol( self, protocol ):
        '''
        >>> u = url_object("http://1.2.3.4")
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

        >>> url_object("http://1.2.3.4").getRootDomain()
        '1.2.3.4'
        >>> url_object("https://aaa.com:80").getRootDomain()
        'aaa.com'
        >>> url_object("http://aaa.com").getRootDomain()
        'aaa.com'
        >>> url_object("http://www.aaa.com").getRootDomain()
        'aaa.com'
        >>> url_object("http://mail.aaa.com").getRootDomain()
        'aaa.com'
        >>> url_object("http://foo.bar.spam.eggs.aaa.com").getRootDomain()
        'aaa.com'
        >>> url_object("http://foo.bar.spam.eggs.aaa.com.ar").getRootDomain()
        'aaa.com.ar'
        >>> url_object("http://foo.aaa.com.ar").getRootDomain()
        'aaa.com.ar'
        >>> url_object("http://foo.aaa.edu.sz").getRootDomain()
        'aaa.edu.sz'

        '''
        # TODO: this list should be updated from time to time, automatically.
        # taken from http:#en.wikipedia.org/wiki/List_of_Internet_top-level_domains
        gTopLevelDomainDict =  {
            "ac":1,"ad":1,"ae":1,"aero":1,"af":1,"ag":1,"ai":1,"al":1,"am":1,
            "an":1,"ao":1,"aq":1,"ar":1,"arpa":1,"as":1,"at":1,"au":1,"aw":1,
            "az":1,"ba":1,"bb":1,"bd":1,"be":1,"bf":1,"bg":1,"bh":1,"bi":1,
            "biz":1,"bj":1,"bm":1,"bn":1,"bo":1,"br":1,"bs":1,"bt":1,"bv":1,
            "bw":1,"by":1,"bz":1,"ca":1,"cc":1,"cd":1,"cf":1,"cg":1,"ch":1,
            "ci":1,"ck":1,"cl":1,"cm":1,"cn":1,"co":1,"com":1,"coop":1,"cr":1,
            "cu":1,"cv":1,"cx":1,"cy":1,"cz":1,"de":1,"dj":1,"dk":1,"dm":1,
            "do":1,"dz":1,"ec":1,"edu":1,"ee":1,"eg":1,"er":1,"es":1,"et":1,
            "fi":1,"fj":1,"fk":1,"fm":1,"fo":1,"fr":1,"ga":1,"gb":1,"gd":1,
            "ge":1,"gf":1,"gg":1,"gh":1,"gi":1,"gl":1,"gm":1,"gn":1,"gov":1,
            "gp":1,"gq":1,"gr":1,"gs":1,"gt":1,"gu":1,"gw":1,"gy":1,"hk":1,
            "hm":1,"hn":1,"hr":1,"ht":1,"hu":1,"id":1,"ie":1,"il":1,"im":1,
            "in":1,"info":1,"int":1,"io":1,"iq":1,"ir":1,"is":1,"it":1,"je":1,
            "jm":1,"jo":1,"jp":1,"ke":1,"kg":1,"kh":1,"ki":1,"km":1,"kn":1,
            "kr":1,"kw":1,"ky":1,"kz":1,"la":1,"lb":1,"lc":1,"li":1,"lk":1,
            "lr":1,"ls":1,"lt":1,"lu":1,"lv":1,"ly":1,"ma":1,"mc":1,"md":1,
            "mg":1,"mh":1,"mil":1,"mk":1,"ml":1,"mm":1,"mn":1,"mo":1,"mp":1,
            "mq":1,"mr":1,"ms":1,"mt":1,"mu":1,"museum":1,"mv":1,"mw":1,"mx":1,
            "my":1,"mz":1,"na":1,"name":1,"nc":1,"ne":1,"net":1,"nf":1,"ng":1,
            "ni":1,"nl":1,"no":1,"np":1,"nr":1,"nu":1,"nz":1,"om":1,"org":1,
            "pa":1,"pe":1,"pf":1,"pg":1,"ph":1,"pk":1,"pl":1,"pm":1,"pn":1,
            "pr":1,"pro":1,"ps":1,"pt":1,"pw":1,"py":1,"qa":1,"re":1,"ro":1,
            "ru":1,"rw":1,"sa":1,"sb":1,"sc":1,"sd":1,"se":1,"sg":1,"sh":1,
            "si":1,"sj":1,"sk":1,"sl":1,"sm":1,"sn":1,"so":1,"sr":1,"st":1,
            "su":1,"sv":1,"sy":1,"sz":1,"tc":1,"td":1,"tf":1,"tg":1,"th":1,
            "tj":1,"tk":1,"tm":1,"tn":1,"to":1,"tp":1,"tr":1,"tt":1,"tv":1,
            "tw":1,"tz":1,"ua":1,"ug":1,"uk":1,"um":1,"us":1,"uy":1,"uz":1,
            "va":1,"vc":1,"ve":1,"vg":1,"vi":1,"vn":1,"vu":1,"wf":1,"ws":1,
            "ye":1,"yt":1,"yu":1,"za":1,"zm":1,"zw":1 
        }
        
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
            
            for i in chunks:
                if (not foundBreak):
                    baseAuthority = i + (".","")[baseAuthority==""] + baseAuthority
                else:
                    subdomain = i  + (".","")[subdomain==""] + subdomain
                if (not gTopLevelDomainDict.has_key(i)):
                    foundBreak=1
            return ([subdomain,baseAuthority])
        
        # def to split URI into its parts, returned as URI object
        def decomposeURI():
            
            authority = self.getDomain()
            s = splitAuthority(authority)
            subdomain = s[0]
            baseAuthority = s[1]
            
            return baseAuthority
                
        if is_ip_address(self.netloc):
            # An IP address has no "root domain" 
            return self.netloc
        else:
            return decomposeURI()
            
    def getDomainPath( self ):
        '''
        @return: Returns the domain name and the path for the url.
    
        >>> url_object('http://abc/def/jkl/').getDomainPath().url_string
        'http://abc/def/jkl/'
        >>> url_object('http://abc/def.html').getDomainPath().url_string
        'http://abc/'
        >>> url_object('http://abc/xyz/def.html').getDomainPath().url_string
        'http://abc/xyz/'
        >>> url_object('http://abc:80/xyz/def.html').getDomainPath().url_string
        'http://abc:80/xyz/'
        >>> url_object('http://abc:443/xyz/def.html').getDomainPath().url_string
        'http://abc:443/xyz/'
        >>> url_object('https://abc:443/xyz/def.html').getDomainPath().url_string
        'https://abc:443/xyz/'
        '''
        if self.path:
            res = self.scheme + '://' +self.netloc+ self.path[:self.path.rfind('/')+1]
        else:
            res = self.scheme + '://' +self.netloc+ '/'
        return url_object(res)
    
    def getFileName( self ):
        '''
        @return: Returns the filename name for the given url.
    
        >>> url_object('https://abc:443/xyz/def.html').getFileName()
        'def.html'
        >>> url_object('https://abc:443/xyz/').getFileName()
        ''
        >>> url_object('https://abc:443/xyz/d').getFileName()
        'd'
        '''
        return self.path[self.path.rfind('/')+1:]

    @set_changed
    def setFileName( self, new ):
        '''
        @return: Sets the filename name for the given URL.
    
        >>> u = url_object('https://abc:443/xyz/def.html')
        >>> u.setFileName( 'abc.pdf' )
        >>> u.url_string
        'https://abc:443/xyz/abc.pdf'
        >>> u.getFileName()
        'abc.pdf'
        
        >>> u = url_object('https://abc:443/xyz/def.html?id=1')
        >>> u.setFileName( 'abc.pdf' )
        >>> u.url_string
        'https://abc:443/xyz/abc.pdf?id=1'

        >>> u = url_object('https://abc:443/xyz/def.html?file=/etc/passwd')
        >>> u.setFileName( 'abc.pdf' )
        >>> u.url_string
        'https://abc:443/xyz/abc.pdf?file=/etc/passwd'

        >>> u = url_object('https://abc/')
        >>> u.setFileName( 'abc.pdf' )
        >>> u.url_string
        'https://abc/abc.pdf'
        '''
        if self.path == '/':
            self.path = '/' + new
        
        else:
            last_slash = self.path.rfind('/')
            self.path = self.path[:last_slash+1] + new
    
    def getExtension( self ):
        '''
        @return: Returns the extension of the filename, if possible, else, ''.
        
        >>> url_object('https://abc:443/xyz/d').getExtension()
        ''
        >>> url_object('https://abc:443/xyz/d.html').getExtension()
        'html'
        >>> url_object('https://abc:443/xyz/').getExtension()
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
        @parameter extension: The new extension to set, without the '.'
        @return: None. The extension is set. An exception is raised if the
        original URL had no extension.
        
        >>> url_object('https://www.w3af.com/xyz/foo').setExtension('xml')
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        Exception: You can only set a new extension to a URL that had one.

        >>> u = url_object('https://abc:443/xyz/d.html')
        >>> u.setExtension('xml')
        >>> u.getExtension()
        'xml'
        
        >>> u = url_object('https://abc:443/xyz/d.html?id=3')
        >>> u.setExtension('xml')
        >>> u.getExtension()
        'xml'

        >>> u = url_object('https://abc:443/xyz/d.html.foo?id=3')
        >>> u.setExtension('xml')
        >>> u.getExtension()
        'xml'
        >>> u.url_string
        'https://abc:443/xyz/d.html.xml?id=3'

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
        >>> url_object('https://abc:443/xyz/').allButScheme()
        'abc:443/xyz/'
        >>> url_object('https://abc:443/xyz/file.asp').allButScheme()
        'abc:443/xyz/'

        @return: Returns the domain name and the path for the url.
        '''
        return self.netloc+ self.path[:self.path.rfind('/')+1]
    
    def getPath( self ):
        '''
        >>> url_object('https://abc:443/xyz/file.asp').getPath()
        '/xyz/file.asp'
        >>> url_object('https://abc:443/xyz/').getPath()
        '/xyz/'
        >>> url_object('https://abc:443/xyz/123/456/789/').getPath()
        '/xyz/123/456/789/'

        @return: Returns the path for the url:
        '''
        return self.path

    @set_changed    
    def setPath(self, path):
        self.path = path

    def getPathWithoutFile( self ):
        '''
        >>> url_object('https://abc:443/xyz/file.asp').getPathWithoutFile()
        '/xyz/'
        >>> url_object('https://abc:443/xyz/').getPathWithoutFile()
        '/xyz/'
        >>> url_object('https://abc:443/xyz/123/456/789/').getPathWithoutFile()
        '/xyz/123/456/789/'

        @return: Returns the path for the url:
        '''
        path = self.getPath()
        filename = self.getFileName()
        return path.replace(filename, '', 1)
    
    def getPathQs( self ):
        '''
        >>> url_object('https://abc:443/xyz/123/456/789/').getPath()
        '/xyz/123/456/789/'
        >>> url_object('https://abc:443/xyz/123/456/789/').getPathQs()
        '/xyz/123/456/789/'
        >>> url_object('https://abc:443/xyz/file.asp').getPathQs()
        '/xyz/file.asp'
        >>> url_object('https://abc:443/xyz/file.asp?id=1').getPathQs()
        '/xyz/file.asp?id=1'
    
        @return: Returns the domain name and the path for the url.
        '''
        res = self.path
        if self.params != '':
            res += ';' + self.params
        if self.qs != '':
            res += '?' + self.qs
        return res
    
    def urlDecode( self ):
        '''
        >>> url_object('https://abc:443/xyz/file.asp?id=1').urlDecode().url_string
        'https://abc:443/xyz/file.asp?id=1'
        >>> url_object('https://abc:443/xyz/file.asp?id=1%202').urlDecode().url_string
        'https://abc:443/xyz/file.asp?id=1 2'
        >>> url_object('https://abc:443/xyz/file.asp?id=1+2').urlDecode().url_string
        'https://abc:443/xyz/file.asp?id=1 2'

        @return: An URL-Decoded version of the URL.
        '''
        res = None
        if type(self.url_string) == type(""):
            res = urllib.unquote(string.replace(self.url_string, "+", " "))
            res = url_object( res )
        return res
    
    def getDirectories( self ):
        '''
        Get a list of all directories and subdirectories.
        
        >>> [i.url_string for i in url_object('http://abc/xyz/def/123/').getDirectories()]
        ['http://abc/', 'http://abc/xyz/', 'http://abc/xyz/def/', 'http://abc/xyz/def/123/']
        >>> [i.url_string for i in url_object('http://abc/xyz/def/').getDirectories()]
        ['http://abc/', 'http://abc/xyz/', 'http://abc/xyz/def/']
        >>> [i.url_string for i in url_object('http://abc/xyz/').getDirectories()]
        ['http://abc/', 'http://abc/xyz/']
        >>> [i.url_string for i in url_object('http://abc/').getDirectories()]
        ['http://abc/']

        '''
        res = []
        
        dp = self.getDomainPath().url_string
        bu = self.baseUrl().url_string
        directories = dp.replace( bu, '' )
        splitted_dirs = directories.split('/')
        for i in xrange( len(splitted_dirs) ):
            url = bu + '/'.join( splitted_dirs[:i] )
            if url[len( url )-1] != '/':
                url += '/'
            res.append( url_object(url) )
        
        return res
    
    def hasParams( self ):
        '''
        Analizes the url to check for a params

        >>> url_object('http://abc/').hasParams()
        False
        >>> url_object('http://abc/;id=1').hasParams()
        True
        >>> url_object('http://abc/?id=3;id=1').hasParams()
        False
        >>> url_object('http://abc/;id=1?id=3').hasParams()
        True
        >>> url_object('http://abc/foobar.html;id=1?id=3').hasParams()
        True
    
        @return: True if the URL has params.
        '''
        if self.params != '':
            return True
        return False
    
    def getParamsString( self ):
        '''
        >>> url_object('http://abc/').getParamsString()
        ''
        >>> url_object('http://abc/;id=1').getParamsString()
        'id=1'
        >>> url_object('http://abc/?id=3;id=1').getParamsString()
        ''
        >>> url_object('http://abc/;id=1?id=3').getParamsString()
        'id=1'
        >>> url_object('http://abc/foobar.html;id=1?id=3').getParamsString()
        'id=1'
    
        @return: Returns the params inside the url.
        '''
        return self.params
    
    def removeParams( self ):
        '''
        @return: Returns a new url object contaning the URL without the parameter. Example :

        >>> url_object('http://abc/').removeParams().url_string
        'http://abc/'
        >>> url_object('http://abc/def.txt').removeParams().url_string
        'http://abc/def.txt'
        >>> url_object('http://abc/;id=1').removeParams().url_string
        'http://abc/'
        >>> url_object('http://abc/;id=1&file=2').removeParams().url_string
        'http://abc/'
        >>> url_object('http://abc/;id=1?file=2').removeParams().url_string
        'http://abc/?file=2'
        >>> url_object('http://abc/xyz.txt;id=1?file=2').removeParams().url_string
        'http://abc/xyz.txt?file=2'

        '''
        return url_object.from_parts( self.scheme, self.netloc, self.path, None, self.qs, self.fragment )
    
    @set_changed
    def setParam( self, param_string ):
        '''
        >>> u = url_object('http://abc/;id=1')
        >>> u.setParam('file=2')
        >>> u.getParamsString()
        'file=2'
        >>> u = url_object('http://abc/xyz.txt;id=1?file=2')
        >>> u.setParam('file=3')
        >>> u.getParamsString()
        'file=3'
        >>> u.getPathQs()
        '/xyz.txt;file=3?file=2'
        
        @parameter param_string: The param to set (e.g. "foo=aaa").
        @return: Returns the url containing param.
        '''
        self.params = param_string 
        
    def getParams( self, ignoreExceptions=True ):
        '''
        Parses the params string and returns a dict.
    
        @return: A QueryString object.

        >>> u = url_object('http://abc/xyz.txt;id=1?file=2')
        >>> u.getParams()
        {'id': '1'}
        >>> u = url_object('http://abc/xyz.txt;id=1&file=2?file=2')
        >>> u.getParams()
        {'id': '1', 'file': '2'}
        >>> u = url_object('http://abc/xyz.txt;id=1&file=2?spam=2')
        >>> u.getParams()
        {'id': '1', 'file': '2'}
        >>> u = url_object('http://abc/xyz.txt;id=1&file=2?spam=3')
        >>> u.getParams()
        {'id': '1', 'file': '2'}

        '''
        parsedData = None
        result = {}
        if self.hasParams():
            try:
                parsedData = cgi.parse_qs( self.params, keep_blank_values=True, strict_parsing=True)
            except Exception, e:
                if not ignoreExceptions:
                    raise w3afException('Strange things found when parsing params string: ' + params)
            else:
                for i in parsedData.keys():
                    result[ i ] = parsedData[ i ][0]
        return result

    def __eq__(self, other):
        '''
        @return: True if the url_strings are equal

        '''
        return isinstance(other, url_object) and \
                self.url_string == other.url_string
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        '''
        >>> u1 = url_object('http://abc/')
        >>> u2 = url_object('http://abc/def.htm')
        >>> test = [u1, u2]
        >>> len( list( set( test ) ) )
        2
        >>> u1 = url_object('http://abc/')
        >>> u2 = url_object('http://abc/')
        >>> test = [u1, u2]
        >>> len( list( set( test ) ) )
        1
        '''
        return hash(self.url_string)

    def __str__(self):
        '''
        @return: A string representation of myself

        >>> str( url_object('http://abc/xyz.txt;id=1?file=2') )
        'http://abc/xyz.txt;id=1?file=2'
        >>> str( url_object('http://abc:80/') )
        'http://abc:80/'
        '''
        return self.url_string

    def __repr__(self):
        '''
        @return: A string representation of myself for debugging

        '''
        return '<url_object for "%s">' % self.url_string

    def __contains__(self, s):
        '''
        @return: True if "s" in url_string

        >>> u = url_object('http://abc/xyz.txt;id=1?file=2')
        >>> '1' in u
        True
        
        >>> u = url_object('http://abc/xyz.txt;id=1?file=2')
        >>> 'file=2' in u
        True

        >>> u = url_object('http://abc/xyz.txt;id=1?file=2')
        >>> 'hello!' in u
        False
        '''
        return s in self.url_string
    
    def __add__(self, other):
        '''
        @return: This URL concatenated with the "other" string.
        
        >>> u = url_object('http://www.w3af.com/')
        >>> x = u + 'abc'
        >>> x
        'http://www.w3af.com/abc'

        >>> u = url_object('http://www.w3af.com/')
        >>> x = u + ' hello world!'
        >>> x
        'http://www.w3af.com/ hello world!'

        >>> u = url_object('http://www.w3af.com/')
        >>> x = u + 1
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        TypeError: cannot concatenate 'int' and 'url_object' objects
        
        '''
        if not isinstance(other, basestring):
            msg = "cannot concatenate '%s' and '%s' objects"
            msg = msg % ( other.__class__.__name__, self.__class__.__name__)
            raise TypeError(msg)
        
        return self.url_string + other 

    def __nonzero__(self):
        '''
        @return: True if the URL has a domain and a protocol.
        
        >>> u = url_object('http://www.w3af.com/')
        >>> if u:
        ...    True
        ...
        True
        >>>

        >>> u = url_object('http:///')
        >>> if not u:
        ...    True
        ...
        True
        >>>
        '''
        if self.scheme and self.netloc:
            return True
        
        return False
        
    def __radd__(self, other):
        '''
        @return: The "other" string concatenated with this URL.
        
        >>> u = url_object('http://www.w3af.com/')
        >>> x = 'abc' + u
        >>> x
        'abchttp://www.w3af.com/'

        >>> u = url_object('http://www.w3af.com/')
        >>> x = 'hello world! ' + u
        >>> x
        'hello world! http://www.w3af.com/'

        >>> u = url_object('http://www.w3af.com/')
        >>> x = 1 + u
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        TypeError: cannot concatenate 'int' and 'url_object' objects
        
        '''
        if not isinstance(other, basestring):
            msg = "cannot concatenate '%s' and '%s' objects"
            msg = msg % ( other.__class__.__name__, self.__class__.__name__)
            raise TypeError(msg)
        
        return other + self.url_string 

    def copy(self):
        return copy.deepcopy( self )

if __name__ == "__main__":
    import doctest
    doctest.testmod()

