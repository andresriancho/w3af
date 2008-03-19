PyGoogle - an easy-to-use wrapper for Google's web API
Copyright (c) 2002-3 Mark Pilgrim (f8dy@diveintomark.org)
Open source, Python license

SUMMARY
-------
This module allows you to access Google's web APIs through SOAP,
to do things like search Google and get the results programmatically.
This API is described here:
  http://www.google.com/apis/
  
IMPORTANT NOTE
--------------
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

SYSTEM REQUIREMENTS
-------------------
Requires Python 2.0 or later

Requires the SOAPpy library from the Python Web Services project
(http://pywebsvcs.sourceforge.net).  We include an older version, but
its use is now deprecated (and will go away completely in future 
releases).  Unfortunately, versions of SOAPpy prior to 0.11.3 will not
work correctly, and thus PyGoogle will fall back on the included
SOAP.py library if an earlier version is found.

INSTALLATION
------------
python setup.py install

Or manually copy google.py and SOAP.py to your site-packages directory, or
anywhere else in your Python library path.  You must use the included version
of SOAP.py; all previous versions (0.97 and earlier) are incompatible with
Python 2.2.  Make sure you don't have any previous versions lingering around.
The included version of SOAP.py is fully backward-compatible; it just fixes
some important bugs, that's all.

USAGE
-----
- doGoogleSearch
- doGetCachedPage
- doSpellingSuggestion

>>> import google
>>> google.LICENSE_KEY = '...' # must get your own!
>>> data = google.doGoogleSearch('python')
>>> data.meta.searchTime
0.043221000000000002
>>> dir(data.meta)
['directoryCategories', 'documentFiltering', 'endIndex', 'estimateIsExact',
'estimatedTotalResultsCount', 'searchComments', 'searchQuery', 'searchTime',
'searchTips', 'startIndex']
>>> data.results[0].URL
'http://www.python.org/'
>>> data.results[0].title
'<b>Python</b> Language Website'
>>> dir(data.results[0])
['URL', 'cachedSize', 'directoryCategory', 'directoryTitle', 'hostName',
'relatedInformationPresent', 'snippet', 'summary', 'title']
>>> print google.doGetCachedPage('http://www.python.org/')
[prints Google cache page]
>>> google.doSpellingSuggestion('pithon')
'python'

HISTORY
-------
0.6 of 02/24/2004
  - support the latest SOAPpy release, fallback to included version if it's
    not found, or is a version that's known to be buggy.
  - epydoc API documentation
  - quite a bit of refactoring
  - make some functions and classes that SHOULD be private, actually private
  - formatting cleanup
0.53 of 6/18/2003
  - fixed small typo in documentation
0.5.2 of 4/18/2002
  - updated SOAP.py to 0.9.7.3, fixed bug encoding dictionaries under Python 2.2
  - serach for license key in ".googlekey" file as well as "googlekey.txt"
  - continues searching for license key elsewhere even if HOME environment
    variable is not set (like on Windows NT)
  - print usage summary if no command line options are given (thanks Erik)
  - search is now the default query type (thanks Erik)
  - text output formatter no longer prints internal variables under Python 2.2

0.5 of 4/17/2002
  - added HTTP proxy support (thanks Michael)
  - added command line interface (thanks Erik)
  - added additional ways to set license key (thanks Erik and David)
  - added install script (thanks David)
  - added unit tests for command line options and license key scenarios
0.4 of 4/12/2002
  - added support for doGetCachedPage
  - added support for doSpellingSuggestion
  - fixed bug in SOAP.py unmarshalling value of "null" attributes (now
    handles both "true" and "1" as true values)
0.3 of 4/11/2002
  - included copy of SOAP.py updated for Python 2.2 compatibility (between
    2.1 and 2.2, type("").__name__ changed from "string" to "str", thus 
    causing the marshalling to fail in SOAPBuilder.dump)
0.2 of 4/11/2002
  - fixed typo (_assertLicense)
0.1 of 4/11/2002
  - initial release
