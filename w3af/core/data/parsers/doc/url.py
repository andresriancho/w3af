# -*- coding: utf-8 -*-
"""
url.py

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
import copy
import re
import urllib
import urlparse

from functools import wraps
from ruamel.ordereddict import ordereddict as OrderedDict
from tldextract import TLDExtract

from w3af.core.controllers.misc.is_ip_address import is_ip_address
from w3af.core.controllers.exceptions import BaseFrameworkException

from w3af.core.data.constants.encodings import DEFAULT_ENCODING
from w3af.core.data.dc.generic.data_container import DataContainer
from w3af.core.data.dc.query_string import QueryString
from w3af.core.data.db.disk_item import DiskItem
from w3af.core.data.misc.encoding import (smart_str, PERCENT_ENCODE,
                                          is_known_encoding, smart_unicode)


def set_changed(meth):
    """
    Function to decorate methods in order to empty the memoized cache
    """
    @wraps(meth)
    def changed_wrapper(self, *args, **kwargs):
        self._cache.clear()
        return meth(self, *args, **kwargs)

    return changed_wrapper


def memoized(meth):
    """
    Function to decorate methods in order to query the memoized cache, very
    simplistic decorator since it can only be used for getters which take
    "self" as parameter.
    """
    @wraps(meth)
    def cache_wrapper(self, *args, **kwargs):
        result = self._cache.get(meth, None)

        if result is not None:
            return result
        else:
            value = meth(self, *args, **kwargs)
            self._cache[meth] = value
            return value

    return cache_wrapper


def parse_qsl(qs, keep_blank_values=0, strict_parsing=0):
    """This was a slightly modified version of the function with the same name
    that is defined in urlparse.py . I modified it, and then reverted the patch
    to have different handling of '+':

    -        name = unquote(nv[0].replace('+', ' '))
    -        value = unquote(nv[1].replace('+', ' '))
    +        name = unquote(nv[0])
    +        value = unquote(nv[1])

    Due to this [0] bug: "Proxy (and maybe others) affected by querystring +
    not being decoded by URL class #9139", I reverted my changes to the function
    but kept it here for better docs.

    [0] https://github.com/andresriancho/w3af/issues/9139

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
            name = urlparse.unquote(nv[0].replace('+', ' '))
            value = urlparse.unquote(nv[1].replace('+', ' '))
            r.append((name, value))

    return r


def parse_qs(qstr, ignore_exc=True, encoding=DEFAULT_ENCODING):
    """
    Parse a url encoded string (a=b&c=d) into a QueryString object.

    :param qstr: The string to parse
    :return: A QueryString object (a dict wrapper).
    """
    if not isinstance(qstr, basestring):
        raise TypeError('parse_qs requires a basestring as input.')
    
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
                raise BaseFrameworkException('Error while parsing "%r"' % qstr)
        else:
            def decode(item):
                return (item[0].decode(encoding, 'ignore'),
                        [e.decode(encoding, 'ignore') for e in item[1]])
            qs.update((decode(item) for item in odict.items()))

    return qs


class URL(DiskItem):
    """
    This class represents a URL and gives access to all its parts
    with several "getter" methods.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    SAFE_CHARS = "%/:=&?~#+!$,;'@()*[]|"

    __slots__ = ('_querystr',
                 '_cache',
                 '_encoding',
                 'scheme',
                 'netloc',
                 'path',
                 'params',
                 'querystring',
                 'fragment')

    def __init__(self, data, encoding=DEFAULT_ENCODING):
        """
        :param data: Either a string representing a URL or a 6-elems tuple
            representing the URL components:
            <scheme>://<netloc>/<path>;<params>?<query>#<fragment>

        Simple generic test, more detailed tests in each method!

        """
        self._querystr = None
        self._cache = {}
        self._encoding = encoding

        if not isinstance(data, basestring):
            raise ValueError('Can not build a URL from %s.' % type(data))

        # Verify that the encoding is a valid one. If we don't do it here,
        # things might get crazy afterwards.
        if not is_known_encoding(encoding):
            msg = 'Invalid encoding "%s" when creating URL.'
            raise ValueError(msg % encoding)

        scheme, netloc, path, params, qs, fragment = urlparse.urlparse(data)
        #
        # This is the case when someone creates a URL like
        # this: URL('www.w3af.com')
        #
        if scheme == netloc == '' and not path.startswith('/'):
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

        if not self.netloc and self.scheme != 'file':
            # The URL is invalid, we don't have a netloc!
            raise ValueError('Invalid URL "%s"' % data)

        self.normalize_url()

    @classmethod
    def from_parts(cls, scheme, netloc, path, params,
                   qs, fragment, encoding=DEFAULT_ENCODING):
        """
        This is a "constructor" for the URL class.
        
        :param scheme: http/https
        :param netloc: domain and port
        :param path: directory
        :param params: URL params
        :param qs: query string
        :param fragment: #fragments
        :return: An instance of URL.
        """
        scheme = scheme or u'' 
        netloc = netloc or u''
        path = path or u''
        params = params or u''
        qs = qs or u''
        fragment = fragment or u'' 
        
        data = (scheme, netloc, path, params, qs, fragment)
        url_str = urlparse.urlunparse(data)
        return cls(url_str, encoding)

    @classmethod
    def from_URL(cls, src_url_obj):
        """
        :param src_url: The url object to use as "template" for the new one
        :return: An instance of URL with the same data as original_url_object

        This is a "constructor" for the URL class.
        """
        scheme = src_url_obj.get_protocol() or u''
        netloc = src_url_obj.get_domain() or u''
        path = src_url_obj.get_path() or u''
        params = src_url_obj.get_params() or u''
        fragment = src_url_obj.get_fragment() or u''
        
        encoding = src_url_obj.encoding
        qs = copy.deepcopy(src_url_obj.querystring)

        data = (scheme, netloc, path, params, '', fragment)
        url_str = urlparse.urlunparse(data)

        new_url = cls(url_str, encoding)
        new_url.querystring = qs

        return new_url

    @property
    @memoized
    def url_string(self):
        """
        :return: A <unicode> representation of the URL
        """
        data = (self.scheme,
                self.netloc,
                self.path,
                self.params,
                self.querystring,
                self.fragment)
        data = [smart_unicode(s) for s in data]

        calc = urlparse.urlunparse(data)

        # ensuring this is actually unicode
        if not isinstance(calc, unicode):
            calc = unicode(calc, self.encoding, 'replace')

        return calc

    @property
    def encoding(self):
        return self._encoding

    def has_query_string(self):
        """
        Analyzes the uri to check for a query string.

        :return: True if self has a query string.
        """
        return bool(self.querystring)

    def get_querystring(self):
        """
        Parses the query string and returns a QueryString
        (a dict like) object.

        :return: A QueryString Object that represents the query string.
        """
        return self._querystr

    @set_changed
    def set_querystring(self, qs):
        """
        Set the query string for this URL.
        """
        if isinstance(qs, DataContainer):
            self._querystr = qs
        elif isinstance(qs, basestring):
            self._querystr = parse_qs(qs, ignore_exc=True,
                                      encoding=self.encoding)
        else:
            # This might fail because of the type-check performed in QueryString
            # __init__, but that's ok.
            self._querystr = QueryString(qs)

    querystring = property(get_querystring, set_querystring)

    @memoized
    def uri2url(self):
        """
        :return: Returns a string containing the URL without the query string.
        """
        return URL.from_parts(self.scheme, self.netloc, self.path,
                              None, None, None, encoding=self._encoding)

    def get_fragment(self):
        """
        :return: Returns the #fragment of the URL.
        """
        return self.fragment

    def remove_fragment(self):
        """
        :return: Removes the URL #fragment (if any)
        """
        self.fragment = u''

    def base_url(self):
        """
        :return: A string containing the URL without the query string and
                 without any path.
        """
        params = (self.scheme, self.netloc, None, None, None, None)
        return URL.from_parts(*params, encoding=self._encoding)

    @set_changed
    def normalize_url(self):
        """
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
            http://abc/f00.b4r
        instead of the normal response from urlparser.urljoin:
            http://abc/../f00.b4r

        Added later: Before performing anything, I also normalize the
        net location part of the URL. In some web apps we see things like:
            http://host.tld:80/foo/bar

        As you may have noticed, the ":80" is redundant, and what's even
        worse, it can confuse w3af when performing string comparisons:
        http://host.tld:80/foo/bar != http://host.tld/foo/bar , and
        http://host.tld/foo/bar could also be found by the web_spider
        plugin, so we are analyzing the same thing twice.
        """
        # net location normalization:
        net_location = self.get_net_location()
        protocol = self.get_protocol()

        # We may have auth URLs like <http://user:passwd@host.tld:80>.
        # Notice the ":" duplication. We'll be interested in transforming
        # 'net_location' beginning in the last appearance of ':'
        at_symb_index = net_location.rfind('@')
        colon_symb_max_index = net_location.rfind(':')
        
        # Found
        if colon_symb_max_index > at_symb_index:

            host = net_location[:colon_symb_max_index]
            port = net_location[(colon_symb_max_index + 1):]

            if not port:
                msg = 'Expected protocol number, got an empty string instead.'
                raise ValueError(msg)

            # Assign default port if nondigit.
            if not port.isdigit():
                msg = 'Expected protocol number, got "%s" instead.'
                raise ValueError(msg % port)

            if int(port) > 65535 or int(port) < 1:
                msg = ('Invalid TCP port "%s", expected a number in range'
                       ' 1-65535.')
                raise ValueError(msg % port)
            
            # Collapse port
            if (protocol == 'http' and port == '80') or \
            (protocol == 'https' and port == '443'):
                net_location = host
            else:
                # The net location has a specific port definition
                net_location = host + ':' + port

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

        #
        # Put everything together, do NOT use urlparse.urljoin here or you'll
        # introduce a bug! For more information read:
        #       test_url.py -> test_url_in_filename
        #       https://github.com/andresriancho/w3af/issues/475
        #
        fixed_url = urlparse.urlunparse((protocol, net_location, self.path,
                                         self.params, '', self.fragment))

        # "re-init" the object
        (self.scheme, self.netloc, self.path,
         self.params, _, self.fragment) = urlparse.urlparse(fixed_url)

    def get_port(self):
        """
        :return: The TCP port that is going to be used to contact the remote
                 end.
        """
        net_location = self.get_net_location()
        protocol = self.get_protocol()
        if ':' in net_location:
            host, port = net_location.split(':')
            return int(port)
        else:
            if protocol.lower() == 'http':
                return 80
            elif protocol.lower() == 'https':
                return 443
            else:
                # Just in case...
                return 80

    def url_join(self, relative, encoding=None):
        """
        Construct a full (''absolute'') URL by combining a ''base URL'' (self)
        with a ``relative URL'' (relative). Informally, this uses components
        of the base URL, in particular the addressing scheme, the network
        location and (part of) the path, to provide missing components in the
        relative URL.

        For more information read RFC 1808 especially section 5.

        :param relative: The relative url to add to the base url
        :param encoding: The encoding to use for the final url_object being
                         returned. If no encoding is specified, the returned
                         url_object will have the same encoding that the current
                         url_object.
        :return: The joined URL.

        Example usage available in test_url.py
        """
        resp_encoding = encoding if encoding is not None else self._encoding
        joined_url = urlparse.urljoin(self.url_string, relative)
        jurl_obj = URL(joined_url, resp_encoding)

        # There is no need to call normalize_url here, since it is called in the
        # URL object __init__
        #
        #jurl_obj.normalize_url()

        return jurl_obj

    def get_domain(self):
        """
        :return: Returns the domain name for the url.
        """
        domain = self.netloc.split(':')[0]
        return domain

    @set_changed
    def set_domain(self, new_domain):
        """
        :return: Returns the domain name for the url.
        """
        if not re.match('[a-z0-9-\.]+([a-z0-9-]+)*$', new_domain):
            raise ValueError("'%s' is an invalid domain" % new_domain)

        domain = self.netloc.split(':')[0]
        self.netloc = self.netloc.replace(domain, new_domain)

    def is_valid_domain(self):
        """
        :param url: The url to parse.
        :return: Returns a boolean that indicates if <url>'s domain is valid
        """
        domain_re = '[a-z0-9-]+(\.[a-z0-9-]+)*(:\d\d?\d?\d?\d?)?$'
        return re.match(domain_re, self.netloc) is not None

    def get_net_location(self):
        """
        :return: Returns the net location for the url.
        """
        return self.netloc

    def get_protocol(self):
        """
        :return: Returns the domain name for the url.
        """
        return self.scheme

    @set_changed
    def set_protocol(self, protocol):
        """
        :return: Returns the domain name for the url.
        """
        self.scheme = protocol

    def switch_protocol(self):
        """
        http -> https
        https -> http

        :return: A copy of the current object, with the protocol switched
        """
        proto = self.get_protocol()
        changed_proto_url = self.copy()
        if proto == 'https':
            changed_proto_url.set_protocol('http')
        else:
            changed_proto_url.set_protocol('https')

        return changed_proto_url

    def get_root_domain(self):
        """
        Get the root domain name. Examples:

            input: www.ciudad.com.ar
            output: ciudad.com.ar

            input: i.love.myself.ru
            output: myself.ru
        """
        # An IP address has no 'root domain'
        if is_ip_address(self.netloc):
            return self.netloc

        extract = TLDExtract(suffix_list_url=False, fallback_to_snapshot=True)
        extract_result = extract(self.get_domain())
        return '%s.%s' % (extract_result.domain, extract_result.suffix)

    def get_domain_path(self):
        """
        :return: Returns the domain name and the path for the url.
        """
        if self.path:
            res = self.scheme + '://' + self.netloc + \
                self.path[:self.path.rfind('/') + 1]
        else:
            res = self.scheme + '://' + self.netloc + '/'
        return URL(res, self._encoding)

    def get_file_name(self):
        """
        :return: Returns the filename name for the given url.
        """
        return self.path[self.path.rfind('/') + 1:]

    @set_changed
    def set_file_name(self, new):
        """
        :return: Sets the filename name for the given URL.
        """
        if self.path == '/':
            self.path = '/' + new

        else:
            last_slash = self.path.rfind('/')
            self.path = self.path[:last_slash + 1] + new

    def get_extension(self):
        """
        :return: Returns the extension of the filename, if possible, else, ''.
        """
        fname = self.get_file_name()
        extension = fname[fname.rfind('.') + 1:]
        if extension == fname:
            return ''
        else:
            return extension

    @set_changed
    def set_extension(self, extension):
        """
        :param extension: The new extension to set, without the '.'
        :return: None. The extension is set. An exception is raised if the
        original URL had no extension.
        """
        if not self.get_extension():
            raise Exception(
                'You can only set a new extension to a URL that had one.')

        filename = self.get_file_name()

        split_filename = filename.split('.')
        split_filename[-1] = extension
        new_filename = '.'.join(split_filename)

        self.set_file_name(new_filename)

    def all_but_scheme(self):
        """
        :return: Returns the domain name and the path for the url.
        """
        return self.netloc + self.path[:self.path.rfind('/') + 1]

    def get_path(self):
        """
        :return: Returns the path for the url:
        """
        return self.path

    @set_changed
    def set_path(self, path):
        self.path = path or u'/'

    def get_path_without_file(self):
        """
        :return: Returns the path for the url without the filename part
        """
        return self.path[:self.path.rfind('/') + 1]

    def get_path_qs(self):
        """
        :return: Returns the path for the url containing the QS
        """
        res = self.path
        if self.params != '':
            res += ';' + self.params
        if self.has_query_string():
            res += u'?' + unicode(self.querystring)
        return res

    def url_decode(self):
        """
        Decode the URL, this will transform things like
            http://host.tld/?id=%2Fhome
        into,
            http://host.tld/?id=/home

        :see: Unittests at test_url.py
        :return: A URL that represents the current URL without URL
                 encoded characters.
        """
        unquoted_url = urllib.unquote(str(self))
        enc = self._encoding
        return URL(unquoted_url.decode(enc, 'ignore'), enc)

    def url_encode(self):
        """
        @see: Unittests at test_url.py
        :return: String that represents the current URL
        """
        self_str = str(self)
        qs = ''
        qs_start_index = self_str.find('?')

        if qs_start_index > -1:
            qs = '?' + str(self.querystring)
            self_str = self_str[:qs_start_index]

        return "%s%s" % (urllib.quote(self_str, safe=self.SAFE_CHARS), qs)

    def get_directories(self):
        """
        Get a list of all directories and subdirectories.
        """
        res = []

        current_url = self.copy()
        res.append(current_url.get_domain_path())

        while current_url.get_path().count('/') != 1:
            current_url = current_url.url_join('../')
            res.append(current_url)

        return res

    def has_params(self):
        """
        Analyzes the url to check for a params

        :return: True if the URL has params.
        """
        if self.params != '':
            return True
        return False

    def get_params_string(self):
        """
        :return: Returns the params inside the url.
        """
        return self.params

    def remove_params(self):
        """
        :return: Returns a new url object contaning the URL without the
                 parameter.
        """
        parts = (self.scheme, self.netloc, self.path,
                 None, unicode(self.querystring), self.fragment)
        return URL.from_parts(*parts, encoding=self._encoding)

    @set_changed
    def set_param(self, param_string):
        """
        :param param_string: The param to set (e.g. "foo=aaa").
        :return: Returns the url containing param.
        """
        self.params = param_string

    def get_params(self, ignore_exc=True):
        """
        Parses the params string and returns a dict.

        :return: A QueryString object.
        """
        result = {}

        if self.has_params():
            try:
                parsed_data = urlparse.parse_qs(self.params,
                                                keep_blank_values=True,
                                                strict_parsing=True)
            except Exception:
                if not ignore_exc:
                    raise BaseFrameworkException('Strange things found when'
                                                 ' parsing params string: %s' %
                                                 self.params)
            else:
                for k, v in parsed_data.iteritems():
                    result[k] = v[0]

        return result

    def __iter__(self):
        """
        Return iterator for self.url_string
        """
        return iter(self.url_string)

    def __eq__(self, other):
        """
        :return: True if the url_strings are equal
        """
        return isinstance(other, URL) and \
            self.url_string == other.url_string

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.url_string)

    @memoized
    def __str__(self):
        """
        :return: A string representation of self
        """
        urlstr = smart_str(
            self.url_string,
            self._encoding,
            errors=PERCENT_ENCODE
        )
        return urlstr.replace(' ', '%20')

    def __unicode__(self):
        """
        :return: A unicode representation of myself
        """
        return self.url_string

    def __repr__(self):
        """
        :return: A string representation of myself for debugging

        """
        return '<URL for "%s">' % (self,)

    def __contains__(self, s):
        """
        :return: True if "s" in url_string
        """
        s = smart_unicode(s)
        return s in self.url_string

    def __add__(self, other):
        """
        :return: This URL concatenated with the "other" string.
        """
        if not isinstance(other, basestring):
            msg = "cannot concatenate '%s' and '%s' objects"
            msg = msg % (other.__class__.__name__, self.__class__.__name__)
            raise TypeError(msg)

        return self.url_string + other

    def __nonzero__(self):
        """
        Always evaluate as True
        """
        return True

    def __radd__(self, other):
        """
        :return: The "other" string concatenated with this URL.
        """
        if not isinstance(other, basestring):
            msg = "cannot concatenate '%s' and '%s' objects"
            msg = msg % (other.__class__.__name__, self.__class__.__name__)
            raise TypeError(msg)

        return other + self.url_string

    def get_eq_attrs(self):
        return ['url_string']

    def __getstate__(self):
        state = {k: getattr(self, k) for k in self.__slots__}
        state.pop('_cache')
        return state

    def __setstate__(self, state):
        self._cache = {}
        for k, v in state.iteritems():
            setattr(self, k, v)

    def copy(self):
        self._cache = {}
        return copy.deepcopy(self)
