'''
dependency_check.py

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
import sys
import platform

import core.controllers.outputManager as om

from core.controllers.dependency_check.lazy_load import lazy_load

def dependency_check():
    '''
    This function verifies that the dependencies that are needed by the
    framework core are met.
    '''
    #mem_test('at start')
    om.out.debug('Checking core dependencies')
    
    # Check python version
    major, minor, micro, releaselevel, serial = sys.version_info
    if major == 2:
        if minor <= 5:
            print 'Error: Python 2.' +str(minor)+' was found and Python 2.6 is required.'
            sys.exit( 1 )
        if minor >= 7:
            print 'w3af is officially supported under Python 2.6'
    elif major > 2:
        print 'It seems that you are running python 3k, please let us know if w3af works ok =)'
        sys.exit( 1 )
        
    reasonForExit = False
    packages = []
    packages_debian = []
    packages_mac_ports = []
    additional_information = []
    
    if platform.system() != 'Windows':
        try:
            from pybloomfilter import BloomFilter as mmap_filter
        except Exception, e:
            msg = '    pybloomfiltermmap is a required dependency in *nix systems, please download from '
            msg += 'http://pypi.python.org/pypi/pybloomfiltermmap/0.2.0 and build using the python2.6-dev '
            msg += 'package. Follow these steps:\n'
            msg += '    wget http://pypi.python.org/packages/source/p/pybloomfiltermmap/pybloomfiltermmap-0.2.0.tar.gz\n'
            msg += '    tar -zxpvf pybloomfiltermmap-0.2.0.tar.gz\n'
            msg += '    cd pybloomfiltermmap-0.2.0\n'
            msg += '    sudo apt-get install python2.6-dev\n'
            msg += '    sudo python setup.py install\n\n'
            
            additional_information.append(msg)
            reasonForExit = True
    #mem_test('after bloom filter import')
    try:
        import esmre
        import esm
    except ImportError:
        msg = '    esmre is an optional (for now) library for running w3af which'
        msg += ' will speed up pattern matching for most plugins. You'
        msg += ' can download it from http://code.google.com/p/esmre/ or run'
        msg += ' the following command to install it:\n'
        msg += '    sudo easy_install esmre\n'
        
        #packages.append('esmre')
        #packages.append('esm')
        #additional_information.append(msg)
    
    # nltk raises a warning... which I want to ignore...
    # This is the original warning:
    #
    # /usr/lib/python2.5/site-packages/nltk/__init__.py:117: UserWarning: draw module, ...
    # warnings.warn("draw module, app module, and gui downloader not loaded "
    #
    import warnings
    warnings.filterwarnings('ignore', '.*',)
    #mem_test('after esmre import')
    if not lazy_load('nltk'):
        packages.append('nltk')
        packages_debian.append('python-nltk')
        #TODO
        #packages_mac_port.append()
        msg  = '    If you can not install nltk, please try the following:\n'
        msg += '        wget http://pyyaml.org/download/pyyaml/PyYAML-3.09.tar.gz\n'
        msg += '        tar -xzvf PyYAML-3.09.tar.gz\n'
        msg += '        cd PyYAML-3.09\n'
        msg += '        python setup.py install\n'
        msg += '        cd ..\n'
        msg += '        wget http://nltk.googlecode.com/files/nltk-2.0b9.tar.gz\n'
        msg += '        tar -xzvf nltk-2.0b9.tar.gz\n'
        msg += '        cd nltk-2.0b9\n'
        msg += '        python setup.py install'
        additional_information.append(msg)
        reasonForExit = True
    #mem_test('after nltk import')
    
    if not lazy_load('extlib.SOAPpy.SOAPpy'):
        if not lazy_load('SOAPpy'):
            packages.append('SOAPpy')
            packages_debian.append('python-soappy')
            #TODO
            #packages_mac_port.append()
            reasonForExit = True
    #mem_test('after soappy import')
    try:
        import extlib.pyPdf.pyPdf as pyPdf
    except:
        try:
            import pyPdf
        except:
            packages.append('pyPdf')
            packages_debian.append('python-pypdf')
            #TODO
            #packages_mac_port.append()
            reasonForExit = True
    #mem_test('after pypdf import')   
    try:
        from OpenSSL import SSL
    except:
        packages.append('pyOpenSSL')
        packages_debian.append('python-pyopenssl')
        packages_mac_ports.extend(['py26-openssl'])
        reasonForExit = True
    #mem_test('after ssl import')
    try:
        from lxml import etree
    except:
        packages.append('lxml')
        packages_debian.append('python-lxml')
        #TODO
        #packages_mac_port.append()
        reasonForExit = True
    #mem_test('after lxml import')
    try:
        import pysvn
    except Exception, e:
        if e.message.startswith('pysvn was built'):
            msg  = '    It looks like your pysvn library installation is broken\n'
            msg += '    (are you using BT4 R2?). The error we get when importing\n'
            msg += '    the pysvn library is "%s". \n\n' % e.message
            
            msg += '    This is a BackTrack issue (works with Ubuntu 8.04 and 10.10)\n'
            msg += '    that was fixed by them in their devel repositories, in order to\n'
            msg += '    enable them you need to follow these steps:\n'
            msg += '        1. vim /etc/apt/sources.list\n'
            msg += '        2. Un-comment the BackTrack Devel Repository line (deb http://archive.offensive-security.com/repotest/ ./)'
            msg += '        3. apt-get update && apt-get dist-upgrade'

            additional_information.append(msg)

        packages.append('pysvn')
        packages_debian.append('python-svn')
        #TODO
        #packages_mac_port.append()
        reasonForExit = True       
    #mem_test('after pysvn import')
    import logging
    logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

    if not lazy_load('scapy'):
        packages.append('scapy')
        packages_debian.append('python-scapy')
        #TODO
        #packages_mac_port.append()
        reasonForExit = True
    else:
        try:
            import scapy.config
        except:
            msg  = '    Your version of scapy is *very old* and incompatible with w3af. Please install scapy version >= 2.0 .\n'
            msg += '    You may issue the following commands in order to install the latest version of scapy in your system:\n'
            msg += '        cd /tmp\n'
            msg += '        wget http://www.secdev.org/projects/scapy/files/scapy-latest.tar.gz\n'
            msg += '        tar -xzvf scapy-latest.tar.gz\n'
            msg += '        cd scapy-2*\n'
            msg += '        sudo python setup.py install\n'
            additional_information.append(msg)
            reasonForExit = True
        else:
            if not scapy.config.conf.version.startswith('2.'):
                msg = '    Your version of scapy (%s) is not compatible with w3af. Please install scapy version >= 2.0 .' % scapy.config.conf.version
                additional_information.append(msg)
                reasonForExit = True
    #mem_test('after scapy import')
    #Now output the results of the dependency check
    if packages:
        msg = 'Your python installation needs the following packages:\n'
        msg += '    '+' '.join(packages)
        print msg, '\n'
    if packages_debian:
        msg = 'On debian based systems:\n'
        msg += '    sudo apt-get install '+' '.join(packages_debian)
        print msg, '\n'
    if packages_mac_ports:
        msg = 'On a mac with mac ports installed:\n'
        msg += '    sudo port install '+' '.join(packages_mac_ports)
        print msg, '\n'
    if additional_information:
        msg = 'Additional information:\n'
        msg += '\n'.join(additional_information)
        print msg
    #Now exit if necessary
    if reasonForExit:
        exit(1)
        

def mem_test(when):
    from core.controllers.profiling.ps_mem import get_memory_usage, human
    sorted_cmds, shareds, _, _ = get_memory_usage(None, True, True, True )
    cmd = sorted_cmds[0]
    msg = "%8sB Private + %8sB Shared = %8sB" % ( human(cmd[1]-shareds[cmd[0]]),
                                                  human(shareds[cmd[0]]), human(cmd[1])
                                                )
    print 'Total memory usage %s: %s' % (when,msg)