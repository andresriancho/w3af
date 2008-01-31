"""
Python wrapper for Google web APIs

This module allows you to access Google's web APIs through SOAP,
to do things like search Google and get the results programmatically.
Described U{here <http://www.google.com/apis/>}
  
You need a Google-provided license key to use these services.
Follow the link above to get one.  These functions will look in
several places (in this order) for the license key:

    - the "license_key" argument of each function
    - the module-level LICENSE_KEY variable (call setLicense once to set it)
    - an environment variable called GOOGLE_LICENSE_KEY
    - a file called ".googlekey" in the current directory
    - a file called "googlekey.txt" in the current directory
    - a file called ".googlekey" in your home directory
    - a file called "googlekey.txt" in your home directory
    - a file called ".googlekey" in the same directory as google.py
    - a file called "googlekey.txt" in the same directory as google.py

Sample usage::
    
    >>> import google
    >>> google.setLicense('...') # must get your own key!
    >>> data = google.doGoogleSearch('python')
    >>> data.meta.searchTime
    0.043221000000000002
    
    >>> data.results[0].URL
    'http://www.python.org/'
    
    >>> data.results[0].title
    '<b>Python</b> Language Website'

@newfield contrib: Contributors
@author:   Mark Pilgrim <f8dy@diveintomark.org>
@author:   Brian Landers <brian@bluecoat93.org>
@license:  Python
@version:  0.6
@contrib:  David Ascher, for the install script
@contrib:  Erik Max Francis, for the command line interface
@contrib:  Michael Twomey, for HTTP proxy support
@contrib:  Mark Recht, for patches to support SOAPpy
"""

__author__ = "Mark Pilgrim (f8dy@diveintomark.org)"
__version__ = "0.6"
__cvsversion__ = "$Revision: 1.5 $"[11:-2]
__date__ = "$Date: 2004/02/25 23:46:07 $"[7:-2]
__copyright__ = "Copyright (c) 2002 Mark Pilgrim"
__license__ = "Python"
__credits__ = """David Ascher, for the install script
Erik Max Francis, for the command line interface
Michael Twomey, for HTTP proxy support"""

import os, sys, getopt
import GoogleSOAPFacade

LICENSE_KEY = None
HTTP_PROXY  = None

#
# Constants
#
_url         = 'http://api.google.com/search/beta2'
_namespace   = 'urn:GoogleSearch'
_googlefile1 = ".googlekey"
_googlefile2 = "googlekey.txt"

_false = GoogleSOAPFacade.false
_true  = GoogleSOAPFacade.true

_licenseLocations = (
    ( lambda key: key,
      'passed to the function in license_key variable' ),
    ( lambda key: LICENSE_KEY, 
      'module-level LICENSE_KEY variable (call setLicense to set it)' ),
    ( lambda key: os.environ.get( 'GOOGLE_LICENSE_KEY', None ),
      'an environment variable called GOOGLE_LICENSE_KEY' ),
    ( lambda key: _contentsOf( os.getcwd(), _googlefile1 ), 
      '%s in the current directory' % _googlefile1),
    ( lambda key: _contentsOf( os.getcwd(), _googlefile2 ),
      '%s in the current directory' % _googlefile2),
    ( lambda key: _contentsOf( os.environ.get( 'HOME', '' ), _googlefile1 ),
      '%s in your home directory' % _googlefile1),
    ( lambda key: _contentsOf( os.environ.get( 'HOME', '' ), _googlefile2 ),
      '%s in your home directory' % _googlefile2 ),
    ( lambda key: _contentsOf( _getScriptDir(), _googlefile1 ),
      '%s in the google.py directory' % _googlefile1 ),
    ( lambda key: _contentsOf( _getScriptDir(), _googlefile2 ),
      '%s in the google.py directory' % _googlefile2 )
)

## ----------------------------------------------------------------------
## Exceptions
## ----------------------------------------------------------------------

class NoLicenseKey(Exception): 
    """
    Thrown when the API is unable to find a valid license key.
    """
    pass

## ----------------------------------------------------------------------
## administrative functions (non-API)
## ----------------------------------------------------------------------

def _version():
    """
    Display a formatted version string for the module
    """
    print """PyGoogle %(__version__)s
%(__copyright__)s
released %(__date__)s

Thanks to:
%(__credits__)s""" % globals()

    
def _usage():
    """
    Display usage information for the command-line interface
    """
    program = os.path.basename(sys.argv[0])
    print """Usage: %(program)s [options] [querytype] query

options:
  -k, --key= <license key> Google license key (see important note below)
  -1, -l, --lucky          show only first hit
  -m, --meta               show meta information
  -r, --reverse            show results in reverse order
  -x, --proxy= <url>       use HTTP proxy
  -h, --help               print this help
  -v, --version            print version and copyright information
  -t, --test               run test queries

querytype:
  -s, --search= <query>    search (default)
  -c, --cache= <url>       retrieve cached page
  -p, --spelling= <word>   check spelling

IMPORTANT NOTE: all Google functions require a valid license key;
visit http://www.google.com/apis/ to get one.  %(program)s will look in
these places (in order) and use the first license key it finds:
  * the key specified on the command line""" % vars()
    for get, location in _licenseLocations[2:]:
        print "  *", location

## ----------------------------------------------------------------------
## utility functions (API)
## ----------------------------------------------------------------------

def setLicense(license_key):
    """
    Set the U{Google APIs <http://www.google.com/api>} license key
    
    @param license_key: The new key to use
    @type  license_key: String
    @todo: validate the key?
    """
    global LICENSE_KEY
    LICENSE_KEY = license_key
    
    
def getLicense(license_key = None):
    """
    Get the U{Google APIs <http://www.google.com/api>} license key
    
    The key can be read from any number of locations.  See the module-leve
    documentation for the search order.
    
    @return: the license key
    @rtype:  String
    @raise NoLicenseKey: if no valid key could be found
    """
    for get, location in _licenseLocations:
        rc = get(license_key)
        if rc: return rc
    _usage()
    raise NoLicenseKey, 'get a license key at http://www.google.com/apis/'


def setProxy(http_proxy):
    """
    Set the HTTP proxy to be used when accessing Google
    
    @param http_proxy: the proxy to use
    @type  http_proxy: String
    @todo: validiate the input?
    """
    global HTTP_PROXY
    HTTP_PROXY = http_proxy


def getProxy(http_proxy = None):
    """
    Get the HTTP proxy we use for accessing Google
    
    @return: the proxy
    @rtype:  String
    """
    return http_proxy or HTTP_PROXY


def _contentsOf(dirname, filename):
    filename = os.path.join(dirname, filename)
    if not os.path.exists(filename): return None
    fsock = open(filename)
    contents = fsock.read()
    fsock.close()
    return contents


def _getScriptDir():
    if __name__ == '__main__':
        return os.path.abspath(os.path.dirname(sys.argv[0]))
    else:
        return os.path.abspath(os.path.dirname(sys.modules[__name__].__file__))


def _marshalBoolean(value):
    if value:
        return _true
    else:
        return _false


def _getRemoteServer( http_proxy ):
    return GoogleSOAPFacade.getProxy( _url, _namespace, http_proxy )
    

## ----------------------------------------------------------------------
## search results classes
## ----------------------------------------------------------------------

class _SearchBase:
    def __init__(self, params):
        for k, v in params.items():
            if isinstance(v, GoogleSOAPFacade.structType):
                v = GoogleSOAPFacade.toDict( v )
                
            try:
                if isinstance(v[0], GoogleSOAPFacade.structType):
                    v = [ SOAPProxy.toDict( node ) for node in v ]

            except:
                pass
            self.__dict__[str(k)] = v

## ----------------------------------------------------------------------

class SearchResultsMetaData(_SearchBase):
    """
    Container class for metadata about a given search query's results.

    @ivar documentFiltering: is duplicate page filtering active?

    @ivar searchComments: human-readable informational message

        example::

             "'the' is a very common word and was not included in your search"

    @ivar estimatedTotalResultsCount: estimated total number of results 
        for this query.

    @ivar estimateIsExact: is estimatedTotalResultsCount an exact value?

    @ivar searchQuery: search string that initiated this search

    @ivar startIndex: index of the first result returned (zero-based)

    @ivar endIndex: index of the last result returned (zero-based)

    @ivar searchTips: human-readable informational message on how to better
       use Google.

    @ivar directoryCategories: list of categories for the search results

       This field is a list of dictionaries, like so::

           { 'fullViewableName': 'the Open Directory category',
             'specialEncoding':  'encoding scheme of this directory category'
           }

    @ivar searchTime: total search time, in seconds
    """    
    pass

## ----------------------------------------------------------------------

class SearchResult(_SearchBase):
    """
    Encapsulates the results from a search.

    @ivar URL: URL

    @ivar title: title (HTML)

    @ivar snippet: snippet showing query context (HTML

    @ivar cachedSize: size of cached version of this result, (KB)

    @ivar relatedInformationPresent: is the "related:" keyword supported?

        Flag indicates that the "related:" keyword is supported for this URL

    @ivar hostName:  used when filtering occurs

        When filtering occurs, a maximum of two results from any given
        host is returned.  When this occurs, the second resultElement
        that comes from that host contains the host name in this parameter.

    @ivar directoryCategory: Open Directory category information

        This field is a dictionary with the following values::

            { 'fullViewableName': 'the Open Directory category',
              'specialEncoding' : 'encoding scheme of this directory category'
            }

    @ivar directoryTitle: Open Directory title of this result (or blank)

    @ivar summary: Open Directory summary for this result (or blank)
    """
    pass

## ----------------------------------------------------------------------

class SearchReturnValue:
    """
    complete search results for a single query

    @ivar meta: L{SearchResultsMetaData} instance for this query

    @ivar results: list of L{SearchResult} objects for this query 
    """
    def __init__( self, metadata, results ):
        self.meta    = metadata
        self.results = results

## ----------------------------------------------------------------------
## main functions
## ----------------------------------------------------------------------

def doGoogleSearch( q, start = 0, maxResults = 10, filter = 1,
                    restrict='', safeSearch = 0, language = '',
                    inputencoding = '', outputencoding = '',\
                    license_key = None, http_proxy = None ):
    """
    Search Google using the SOAP API and return the results.

    You need a license key to call this function; see the
    U{Google APIs <http://www.google.com/apis/>} site to get one.
    Then you can either pass it to this function every time, or
    set it globally; see the L{google} module-level docs for details.
    
    See U{http://www.google.com/help/features.html}
    for examples of advanced features.  Anything that works at the 
    Google web site will work as a query string in this method.
    
    You can use the C{start} and C{maxResults} parameters to page
    through multiple pages of results.  Note that 'maxResults' is
    currently limited by Google to 10.
            
    See the API reference for more advanced examples and a full list of
    country codes and topics for use in the C{restrict} parameter, along
    with legal values for the C{language}, C{inputencoding}, and
    C{outputencoding} parameters.
    
    You can download the API documentation 
    U{http://www.google.com/apis/download.html <here>}.
    
    @param q: search string.  
    @type  q: String

    @param start: (optional) zero-based index of first desired result.
    @type  start: int

    @param maxResults: (optional) maximum number of results to return.
    @type  maxResults: int

    @param filter: (optional) flag to request filtering of similar results
    @type  filter: int

    @param restrict: (optional) restrict results by country or topic.
    @type  restrict: String    

    @param safeSearch: (optional)
    @type  safeSearch: int

    @param language: (optional)
    @type  language: String

    @param inputencoding: (optional)
    @type  inputencoding: String

    @param outputencoding: (optional)
    @type  outputencoding: String

    @param license_key: (optional) the Google API license key to use
    @type  license_key: String

    @param http_proxy: (optional) the HTTP proxy to use for talking to Google
    @type  http_proxy: String
    
    @return: the search results encapsulated in an object
    @rtype:  L{SearchReturnValue}
    """
    license_key  = getLicense( license_key )    
    http_proxy   = getProxy( http_proxy )
    remoteserver = _getRemoteServer( http_proxy )
                                   
    filter     = _marshalBoolean( filter )
    safeSearch = _marshalBoolean( safeSearch )
    
    data = remoteserver.doGoogleSearch( license_key, q, start, maxResults,
                                        filter, restrict, safeSearch,
                                        language, inputencoding, 
                                        outputencoding )

    metadata = GoogleSOAPFacade.toDict( data )
    del metadata["resultElements"]
    
    metadata = SearchResultsMetaData( metadata )
    
    results = [ SearchResult( GoogleSOAPFacade.toDict( node ) ) \
                    for node in data.resultElements ]
    
    return SearchReturnValue( metadata, results )

## ----------------------------------------------------------------------

def doGetCachedPage( url, license_key = None, http_proxy = None ):
    """
    Retrieve a page from the Google cache.

    You need a license key to call this function; see the
    U{Google APIs <http://www.google.com/apis/>} site to get one.
    Then you can either pass it to this function every time, or
    set it globally; see the L{google} module-level docs for details.
    
    @param url: full URL to the page to retrieve
    @type  url: String
    
    @param license_key: (optional) the Google API key to use
    @type  license_key: String
    
    @param http_proxy:  (optional) the HTTP proxy server to use
    @type  http_proxy:  String
    
    @return: full text of the cached page
    @rtype:  String
    """
    license_key  = getLicense( license_key )
    http_proxy   = getProxy( http_proxy )
    remoteserver = _getRemoteServer( http_proxy )
                                   
    return remoteserver.doGetCachedPage( license_key, url )

## ----------------------------------------------------------------------

def doSpellingSuggestion( phrase, license_key = None, http_proxy = None ):
    """
    Get spelling suggestions from Google

    You need a license key to call this function; see the
    U{Google APIs <http://www.google.com/apis/>} site to get one.
    Then you can either pass it to this function every time, or
    set it globally; see the L{google} module-level docs for details.

    @param phrase: word or phrase to spell-check
    @type  phrase: String

    @param license_key: (optional) the Google API key to use
    @type  license_key: String
    
    @param http_proxy: (optional) the HTTP proxy to use
    @type  http_proxy: String
    
    @return: text of any suggested replacement, or None
    """
    license_key  = getLicense( license_key )    
    http_proxy   = getProxy( http_proxy) 
    remoteserver = _getRemoteServer( http_proxy )
                                   
    return remoteserver.doSpellingSuggestion( license_key, phrase )

## ----------------------------------------------------------------------
## functional test suite (see googletest.py for unit test suite)
## ----------------------------------------------------------------------

def _test():
    """
    Run functional test suite.
    """
    try:
        getLicense(None)
    except NoLicenseKey:
        return
        
    print "Searching for Python at google.com..."
    data = doGoogleSearch( "Python" )
    _output( data, { "func": "doGoogleSearch"} )

    print "\nSearching for 5 _French_ pages about Python, "
    print "encoded in ISO-8859-1..."

    data = doGoogleSearch( "Python", language = 'lang_fr',                 
                                     outputencoding = 'ISO-8859-1',
                                     maxResults = 5 )
                                     
    _output( data, { "func": "doGoogleSearch" } )

    phrase = "Pyhton programming languager"
    print "\nTesting spelling suggestions for '%s'..." % phrase
    
    data = doSpellingSuggestion( phrase )
    
    _output( data, { "func": "doSpellingSuggestion" } )

## ----------------------------------------------------------------------
## Command-line interface
## ----------------------------------------------------------------------

class _OutputFormatter:
    def boil(self, data):
        if type(data) == type(u""):
            return data.encode("ISO-8859-1", "replace")
        else:
            return data

class _TextOutputFormatter(_OutputFormatter):
    def common(self, data, params):
        if params.get("showMeta", 0):
            meta = data.meta
            for category in meta.directoryCategories:
                print "directoryCategory: %s" % \
                  self.boil(category["fullViewableName"])
            for attr in [node for node in dir(meta) if \
              node <> "directoryCategories" and node[:2] <> '__']:
                print "%s:" % attr, self.boil(getattr(meta, attr))
        
    def doGoogleSearch(self, data, params):
        results = data.results
        if params.get("feelingLucky", 0):
            results = results[:1]
        if params.get("reverseOrder", 0):
            results.reverse()
        for result in results:
            for attr in dir(result):
                if attr == "directoryCategory":
                    print "directoryCategory:", \
                      self.boil(result.directoryCategory["fullViewableName"])
                elif attr[:2] <> '__':
                    print "%s:" % attr, self.boil(getattr(result, attr))
            print
        self.common(data, params)
    
    def doGetCachedPage(self, data, params):
        print data
        self.common(data, params)

    doSpellingSuggestion = doGetCachedPage

def _makeFormatter(outputFormat):
    classname = "_%sOutputFormatter" % outputFormat.capitalize()
    return globals()[classname]()

def _output(results, params):
    formatter = _makeFormatter(params.get("outputFormat", "text"))
    outputmethod = getattr(formatter, params["func"])
    outputmethod(results, params)

def main(argv):
    """
    Command-line interface.
    """
    if not argv:
        _usage()
        return
    q = None
    func = None
    http_proxy = None
    license_key = None
    feelingLucky = 0
    showMeta = 0
    reverseOrder = 0
    runTest = 0
    outputFormat = "text"
    try:
        opts, args = getopt.getopt(argv, "s:c:p:k:lmrx:hvt1",
            ["search=", "cache=", "spelling=", "key=", "lucky", "meta",
             "reverse", "proxy=", "help", "version", "test"])
    except getopt.GetoptError:
        _usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-s", "--search"):
            q = arg
            func = "doGoogleSearch"
        elif opt in ("-c", "--cache"):
            q = arg
            func = "doGetCachedPage"
        elif opt in ("-p", "--spelling"):
            q = arg
            func = "doSpellingSuggestion"
        elif opt in ("-k", "--key"):
            license_key = arg
        elif opt in ("-l", "-1", "--lucky"):
            feelingLucky = 1
        elif opt in ("-m", "--meta"):
            showMeta = 1
        elif opt in ("-r", "--reverse"):
            reverseOrder = 1
        elif opt in ("-x", "--proxy"):
            http_proxy = arg
        elif opt in ("-h", "--help"):
            _usage()
        elif opt in ("-v", "--version"):
            _version()
        elif opt in ("-t", "--test"):
            runTest = 1
    if runTest:
        setLicense(license_key)
        setProxy(http_proxy)
        _test()
    if args and not q:
        q = args[0]
        func = "doGoogleSearch"
    if func:
        results = globals()[func]( q, http_proxy=http_proxy, 
                                   license_key=license_key )
        _output(results, locals())

if __name__ == '__main__':
    main(sys.argv[1:])
