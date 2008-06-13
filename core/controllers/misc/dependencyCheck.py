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

'''
This module defines a dependencyCheck function.

@author: Andres Riancho ( andres.riancho@gmail.com )
'''

import core.controllers.outputManager as om
import sys

def dependencyCheck():
    om.out.debug('Checking dependencies:')
    
    try:
        import extlib.pygoogle.google as pygoogle
    except:
        try:
            import google as pygoogle
        except Exception, e:
            print 'You have to install pygoogle lib.'
            print 'Error: ' + str(e)
            sys.exit( 1 )

    try:
        import extlib.BeautifulSoup as BeautifulSoup
    except:
        try:
            import BeautifulSoup
        except:
            print 'You have to install BeautifulSoup lib.'
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
        print 'You have to install pyOpenSSL library. On Debian based distributions: apt-get install python-pyopenssl'
        sys.exit( 1 )

