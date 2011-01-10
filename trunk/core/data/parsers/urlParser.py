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

import urlparse as _uparse
import urllib
import cgi
import re
import string

'''
This module parses URLs.

@author: Andres Riancho ( andres.riancho@gmail.com )
'''

def hasQueryString( uri ):
    '''
    Analizes the uri to check for a query string.

    @parameter uri: The uri to analize.
    @return: True if the URI has a query string.
    '''
    scheme, domain, path, params, qs, fragment = _uparse.urlparse( uri )
    if qs != '':
        return True
    return False

def getQueryString( url, ignoreExceptions=True ):
    '''
    Parses the query string and returns a dict.

    @parameter url: The url with the query string to parse.
    @return: A QueryString Object, example :
        - input url : http://localhost/foo.asp?xx=yy&bb=dd
        - output dict : { xx:yy , bb:dd }
    '''
    parsedQs = None
    result = queryString()

    scheme, domain, path, params, qs, fragment = _uparse.urlparse( url )

    if qs:
        try:
            parsedQs = cgi.parse_qs( qs ,keep_blank_values=True,strict_parsing=False)
        except Exception, e:
            if not ignoreExceptions:
                raise w3afException('Strange things found when parsing query string: "' + qs + '"')
        else:
            #
            #   Before we had something like this:
            #
            #for i in parsedQs.keys():
            #    result[ i ] = parsedQs[ i ][0]
            #
            #   But with that, we fail to handle web applications that use "duplicated parameter
            #   names". For example: http://host.tld/abc?sp=1&sp=2&sp=3
            #
            #   (please note the lack of [0]) , and that if the value isn't a list... 
            #    I create an artificial list
            for i in parsedQs.keys():
                if isinstance( parsedQs[ i ], list ):
                    result[ i ] = parsedQs[ i ]
                else:
                    result[ i ] = [parsedQs[ i ], ]

    return result

def uri2url( url):
    '''
    @parameter url: The url with the query string.
    @return: Returns a string contaning the URL without the query string. Example :
        - input url : http://localhost/foo.asp?xx=yy&bb=dd#fragment
        - output url string : http://localhost/foo.asp
    '''
    scheme, domain, path, params, qs, fragment = _uparse.urlparse( url )
    res = scheme + '://' + domain + path
    if params != '':
        res += ";" + params
    return res

def removeFragment(  url ):
    '''
    @parameter url: The url with fragments
    @return: Returns a string contaning the URL without the fragment. Example :
        - input url : http://localhost/foo.asp?xx=yy&bb=dd#fragment
        - output url string : http://localhost/foo.asp?xx=yy&bb=dd
    '''
    scheme, domain, path, params, qs, fragment = _uparse.urlparse( url )
    res = scheme + '://' + domain + path
    if params != '':
        res += ';' + params
    if qs != '':
        res += '?' + qs
    return res

def baseUrl(  url ):
    '''
    @parameter url: The url with the query string.
    @return: Returns a string contaning the URL without the query string and without any path. 
    Example :
        - input url : http://localhost/dir1/foo.asp?xx=yy&bb=dd
        - output url string : http://localhost/
    '''
    scheme, domain, path, params, qs, fragment = _uparse.urlparse( url )
    return scheme+'://'+domain + '/'


def normalizeURL(url):
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
    >>> normalizeURL('http://host.tld:80/foo/bar')
    'http://host.tld/foo/bar'
    >>> normalizeURL('https://host.tld:443/foo/bar')
    'https://host.tld/foo/bar'
    >>> normalizeURL('http://user:passwd@host.tld:80')
    'http://user:passwd@host.tld/'
    >>> normalizeURL('http://abc/../f00.b4r')
    'http://abc/f00.b4r'
    >>> normalizeURL('http://abc/../../f00.b4r')
    'http://abc/f00.b4r'
    '''
    # net location normalization:
    net_location = getNetLocation(url)
    protocol = getProtocol(url)

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
    relativeURL = getPathQs(url)

    commonjoin = _uparse.urljoin(baseURL, relativeURL)

    path = getPathQs(commonjoin)

    while path.startswith('../') or path.startswith('/../'):
        if path.startswith('../'):
            path = path[2:]
        elif path.startswith('/../'):
            path = path[3:]

    fixedURL = _uparse.urljoin(baseURL, path)
    return fixedURL

def getPort( url ):
    '''
    @return: The TCP port that is going to be used to contact the remote end.
    '''
    net_location = getNetLocation( url )
    protocol = getProtocol( url )
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
            
def urlJoin( baseurl , relative ):
    '''
    Construct a full (''absolute'') URL by combining a ''base URL'' (base) with a ``relative URL'' (url). 
    Informally, this uses components of the base URL, in particular the addressing scheme,
    the network location and (part of) the path, to provide missing components in the relative URL.

    Example:
    >>> urlJoin('http://www.cwi.nl/%7Eguido/Python.html', 'FAQ.html')
    'http://www.cwi.nl/%7Eguido/FAQ.html'
    
    For more information read RFC 1808 espeally section 5.
    
    @param baseurl: The base url to join
    @param relative: The relative url to add to the base url
    @return: The joined URL.
    '''
    response = _uparse.urljoin( baseurl, relative )
    response = normalizeURL(response)
    return response

def getDomain(url):
    '''
    @parameter url: The url to parse.
    @return: Returns the domain name for the url.
    
    >>> getDomain("http://localhost:4444/f00_bar.html")
    'localhost'
    '''
    scheme, domain, path, params, qs, fragment = _uparse.urlparse(url)
    domain = domain.split(':')[0]
    return domain

def isValidURLDomain(url):
    '''
    >>> isValidURLDomain("http://1.2.3.4")
    True
    >>> isValidURLDomain("http://aaa.com")
    True
    >>> isValidURLDomain("http://aaa.")
    False
    >>> isValidURLDomain("http://aa*a")
    False
    >>> isValidURLDomain('http://localhost:8080')
    True
    
    @parameter url: The url to parse.
    @return: Returns a boolean that indicates if <url>'s domain is valid
    '''
    domain  = getDomain(url)
    return re.match('[a-z0-9-]+(\.[a-z0-9-]+)*$', domain or '') is not None

def getNetLocation( url ):
    '''
    >>> getNetLocation('http://localhost:4444/f00_bar.html')
    'localhost:4444'

    @parameter url: The url to parse.
    @return: Returns the net location for the url.
    '''
    scheme, domain, path, params, qs, fragment = _uparse.urlparse( url )
    return domain

def getProtocol( url ):
    '''
    @parameter url: The url to parse.
    @return: Returns the domain name for the url.
    '''
    scheme, domain, path, params, qs, fragment = _uparse.urlparse( url )
    return scheme

def getRootDomain( input ):
    '''
    Get the root domain name. Examples:
    
    input: www.ciudad.com.ar
    output: ciudad.com.ar
    
    input: i.love.myself.ru
    output: myself.ru
    
    Code taken from: http://getoutfoxed.com/node/41
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
    def decomposeURI(aURI):
        
        authority = getDomain(aURI)
        s = splitAuthority(authority)
        subdomain = s[0]
        baseAuthority = s[1]
        
        return baseAuthority
    
    # Normalize the URL
    if not input.count('://'):
        # sometimes i make mistakes...
        url = 'http://' + input
    else:
        url = input
        
    domain = getNetLocation( url )
    
    if is_ip_address(domain):
        # An IP address has no "root domain" 
        return domain
    else:
        return decomposeURI( url )
        
def getDomainPath( url ):
    '''
    @parameter url: The url to parse.
    @return: Returns the domain name and the path for the url.

    >>> getDomainPath('http://localhost/')
    'http://localhost/'
    >>> getDomainPath('http://localhost/abc/')
    'http://localhost/abc/'
    >>> getDomainPath('http://localhost/abc/def.html')
    'http://localhost/abc/'
    >>> 
    '''
    scheme, domain, path, params, qs, fragment = _uparse.urlparse( url )
    if path:
        res = scheme + '://' +domain+ path[:path.rfind('/')+1]
    else:
        res = scheme + '://' +domain+ '/'
    return res

def getFileName( url ):
    '''
    @parameter url: The url to parse.
    @return: Returns the filename name for the given url.

    >>> getFileName('http://localhost/')
    ''
    >>> getFileName('http://localhost/abc')
    'abc'
    >>> getFileName('http://localhost/abc.html')
    'abc.html'
    >>> getFileName('http://localhost/def/abc.html')
    'abc.html'
    '''
    scheme, domain, path, params, qs, fragment = _uparse.urlparse( url )
    return path[path.rfind('/')+1:]

def getExtension( url ):
    '''
    @parameter url: The url to parse.
    @return: Returns the extension of the filename, if possible, else, ''.
    '''
    fname = getFileName( url )
    extension = fname[ fname.rfind('.') +1 :]
    if extension == fname:
        return ''
    else:
        return extension

def allButScheme( url ):
    '''
    @parameter url: The url to parse.
    @return: Returns the domain name and the path for the url.
    '''
    scheme, domain, path, params, qs, fragment = _uparse.urlparse( url )
    return domain+ path[:path.rfind('/')+1]

def getPath( url ):
    '''
    @parameter url: The url to parse.
    @return: Returns the path for the url:
        Input:
            http://localhost/pepe/0a0a
        Output:
            /pepe/0a0a
    '''
    scheme, domain, path, params, qs, fragment = _uparse.urlparse( url )
    return path

def getPathQs(url):
    '''
    >>> getPathQs( 'http://localhost/a/b/c/hh.html' )
    '/a/b/c/hh.html'

    @parameter url: The url to parse.
    @return: Returns the domain name and the path for the url.
    '''
    scheme, domain, path, params, qs, fragment = _uparse.urlparse( url )
    res = path
    if qs != '':
        res += '?' + qs
    if params != '':
        res += ';' + params
    return res

def urlDecode( url ):
    '''
    UrlDecode the url.
    '''
    res = None
    if type(url) == type(""):
        res = urllib.unquote(string.replace(url, "+", " "))
    return res

def getDirectories( url ):
    '''
    Get a list of all directories and subdirectories.
    Example:
        - url = 'http://www.o.com/a/b/c/'
        - return: ['http://www.o.com/a/b/c/','http://www.o.com/a/b/','http://www.o.com/a/','http://www.o.com/']
    '''
    res = []
    
    dp = getDomainPath( url )
    bu = baseUrl( url )
    directories = dp.replace( bu, '' )
    splittedDirs = directories.split('/')
    for i in xrange( len(splittedDirs) ):
        url = bu + '/'.join( splittedDirs[:i] )
        if url[len( url )-1] != '/':
            url += '/'
        res.append( url )
    
    return res

def hasParams( url ):
    '''
    Analizes the url to check for a params

    @parameter url: The url to analize.
    @return: True if the URL has params.
    '''
    scheme, domain, path, params, qs, fragment = _uparse.urlparse( url )
    if params != '':
        return True
    return False

def getParamsString( url ):
    '''
    Input: http://localhost:4444/f00_bar.html;foo=bar?abc=def
    Output: foo=bar

    @parameter url: The url to parse.
    @return: Returns the params inside the url.
    '''
    scheme, domain, path, params, qs, fragment = _uparse.urlparse( url )
    return params

def removeParams( url ):
    '''
    @parameter url: The url with parameter
    @return: Returns a string contaning the URL without the parameter. Example :
        - input url : http://localhost/foo.asp;jsessionid=ABDR1234?xx=yy&bb=dd#fragment
        - output url string : http://localhost/foo.asp?xx=yy&bb=dd
    '''
    scheme, domain, path, params, qs, x3 = _uparse.urlparse( url )
    res = scheme + '://' + domain + path
    if qs != '':
        res += '?' + qs
    return res

def setParam( url, param_string ):
    '''
    @parameter url: The url to parse.
    @parameter param_string: The param to set (e.g. "foo=aaa").
    @return: Returns the url containing param.
    '''
    try:
        param, value = param_string.split("=")
    except ValueError, ve:
        param = param_string
        value = ''
        
    scheme, domain, path, params, qs, fragment = _uparse.urlparse( url )
    res = scheme + '://' + domain + path
    params = getParams(url)
    params[param] = value
    params_string = ";".join([k+"="+params[k] for k in params.keys() ])
    res = res + ';' + params_string
    if qs != '':
        res += '?' + qs
    return res

def getParams( url, ignoreExceptions=True ):
    '''
    Parses the params string and returns a dict.

    @parameter url: The url with the params string to parse.
    @return: A QueryString Object, example :
        - input url : http://localhost/foo.jsp;xx=yy;bb=dd
        - output dict : { xx:yy , bb:dd }
    '''
    parsedData = None
    result = {}
    if hasParams( url ):
        scheme, domain, path, params, qs, fragment = _uparse.urlparse( url )
        try:
            parsedData = cgi.parse_qs( params, keep_blank_values=True, strict_parsing=True)
        except Exception, e:
            if not ignoreExceptions:
                raise w3afException('Strange things found when parsing params string: ' + params)
        else:
            for i in parsedData.keys():
                result[ i ] = parsedData[ i ][0]
    return result

if __name__ == "__main__":
    import doctest
    doctest.testmod()

