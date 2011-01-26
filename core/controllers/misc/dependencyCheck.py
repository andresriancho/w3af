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


def dependencyCheck():
    '''
    This function verifies that the dependencies that are needed by the
    framework core are met.
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
        import nltk
    except Exception, e:
        msg = 'You have to install nltk. \n'
        msg += '    - On Debian based distributions: apt-get install python-nltk\n'
        msg += '    - If that\'s not working for you, please try the following:\n'
        msg += '        wget http://pyyaml.org/download/pyyaml/PyYAML-3.09.tar.gz\n'
        msg += '        tar -xzvf PyYAML-3.09.tar.gz\n'
        msg += '        cd PyYAML-3.09\n'
        msg += '        python setup.py install\n'
        msg += '        cd ..\n'
        msg += '        wget http://nltk.googlecode.com/files/nltk-2.0b9.tar.gz\n'
        msg += '        tar -xzvf nltk-2.0b9.tar.gz\n'
        msg += '        cd nltk-2.0b9\n'
        msg += '        python setup.py install'
        print msg
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
        msg = 'You have to install python libxml2 wrapper. \n'
        msg += '    - On Debian based distributions: apt-get install python-lxml'
        print msg
        sys.exit( 1 )
    
    try:
        import pysvn
    except:
        msg = 'You have to install python pysvn lib. \n'
        msg += '    - On Debian based distributions:  apt-get install python-svn'
        print msg
        sys.exit( 1 )

    try:
        import scapy
    except:
        msg = 'You have to install scapy. \n'
        msg += '    - On Debian based distributions: apt-get install python-scapy'
        print msg
        sys.exit( 1 )
    else:
        try:
            import scapy.config
        except:
            msg = 'Your version of scapy is *very old* and incompatible with w3af. Please install scapy version >= 2.0 .\n'
            msg += 'You may issue the following commands in order to install the latest version of scapy in your system:\n'
            msg += '    cd /tmp\n'
            msg += '    wget http://www.secdev.org/projects/scapy/files/scapy-latest.tar.gz\n'
            msg += '    tar -xzvf scapy-latest.tar.gz\n'
            msg += '    cd scapy-2*\n'
            msg += '    sudo python setup.py install\n'
            print msg
            sys.exit( 1 )
        else:
            if not scapy.config.conf.version.startswith('2.'):
                msg = 'Your version of scapy (%s) is not compatible with w3af. Please install scapy version >= 2.0 .' % scapy.config.conf.version
                print msg
                sys.exit( 1 )
        

