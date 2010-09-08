'''
dependencyCheck.py

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

import core.controllers.outputManager as om
import sys
import subprocess


def dependencyCheck():
    '''
    This function verifies that the dependencies that are needed by the framework core are met.
    '''

    om.out.debug('Checking core dependencies')
    
    # Check python version
    major, minor, micro, releaselevel, serial = sys.version_info
    if major == 2 and minor <= 4:
        print 'Error: Python 2.' +str(minor)+' was found and Python >= 2.5 is required.'
        sys.exit( 1 )
    elif major > 2:
        print 'It seems that you are running python 3k, please let us know if w3af works ok =)'
        sys.exit( 1 )
    
    # nltk raises a warning... which I want to ignore...
    # This is the original warning:
    #
    # /usr/lib/python2.5/site-packages/nltk/__init__.py:117: UserWarning: draw module, app module, and gui downloader not loaded (please install Tkinter library).
    # warnings.warn("draw module, app module, and gui downloader not loaded "
    #
    import warnings
    warnings.filterwarnings('ignore', '.*',)

    try:
        sys.path.append("./extlib")
        import nltk
    except Exception, e:
        print 'You have to install the nltk lib. Please read the users guide.'
        print 'Error: ' + str(e)
        sys.exit( 1 )
            
    try:
        import extlib.pygoogle.google as pygoogle
    except:
        try:
            import google as pygoogle
        except Exception, e:
            print 'You have to install pygoogle and fpconst libs. Please read the users guide.'
            print 'Error: ' + str(e)
            sys.exit( 1 )

    try:
        import extlib.BeautifulSoup as BeautifulSoup
    except:
        try:
            import BeautifulSoup
        except:
            print 'You have to install BeautifulSoup lib. Please read the users guide.'
            sys.exit( 1 )
        

    try:
        import extlib.SOAPpy.SOAPpy as SOAPpy
    except:
        try:
            import SOAPpy
        except:
            print 'You have to install SOAPpy lib. Debian based distributions: apt-get install python-soappy'
            sys.exit( 1 )
    
    try:
        import extlib.pyPdf.pyPdf as pyPdf
    except:
        try:
            import pyPdf
        except:
            print 'You have to install pyPdf lib. Debian based distributions: apt-get install python-pypdf'
            sys.exit( 1 )
    
    try:
        from extlib.jsonpy import json as json
    except:
        try:
            import json
        except:
            print 'You have to install python-json lib. Debian based distributions: apt-get install python-json'
            sys.exit( 1 )
            
    try:
        from OpenSSL import SSL
    except:
        msg = 'You have to install pyOpenSSL library. \n'
        msg += '    - On Debian based distributions: sudo apt-get install python-pyopenssl\n'
        msg += '    - On Mac: sudo port install py25-socket-ssl , or py25-openssl'
        print msg
        sys.exit( 1 )

    try:
        from lxml import etree
    except:
        msg = 'You have to install python libxml2 wrapper. Debian based distributions: apt-get install python-lxml'
        print msg
        sys.exit( 1 )     


