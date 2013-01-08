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
import warnings

from core.controllers.dependency_check.lazy_load import lazy_load


def dependency_check():
    '''
    This function verifies that the dependencies that are needed by the
    framework core are met.
    '''
    #mem_test('at start')

    # Check python version
    major, minor, micro, releaselevel, serial = sys.version_info
    if major == 2:
        if minor not in (6, 7):
            msg = 'Error: Python 2.%s found but Python 2.6 or 2.7 required.' % minor
            print msg
    elif major > 2:
        msg = 'It seems that you are running Python 3k, please let us know if' \
              ' w3af works as expected at w3af-develop@lists.sourceforge.net !'
        print msg
        sys.exit(1)

    reason_for_exit = False
    packages = []
    packages_debian = []
    packages_mac_ports = []
    packages_openbsd = []
    packages_pip = []
    additional_information = []

    if platform.system() != 'Windows':
        try:
            from pybloomfilter import BloomFilter as mmap_filter
        except Exception, e:
            msg = '    pybloomfiltermmap is a required dependency in *nix' \
                  ' systems, in order to install it please run the following' \
                  ' command after installing the Python development headers' \
                  ' and Python setup tools:' \
                  '        sudo easy_install pybloomfiltermmap'
            packages.append('pybloomfilter')
            packages_debian.extend(['python2.7-dev', 'python-setuptools'])
            # Openbsd's python package already includes dev stuff
            packages_openbsd.append('py-setuptools')
            additional_information.append(msg)
            reason_for_exit = True
    #mem_test('after bloom filter import')
    try:
        import esmre
        import esm
    except ImportError:
        msg = '    esmre is an optional (for now) library for running w3af' \
              ' which will speed up pattern matching for most plugins. You' \
              ' can download it from http://code.google.com/p/esmre/ or run' \
              ' the following command to install it:\n' \
              '        sudo easy_install esmre\n'

        #packages_debian.append('python-setuptools')
        #packages_openbsd.append('py-setuptools')
        #packages.append('esmre')
        #packages.append('esm')
        #additional_information.append(msg)

    # nltk raises a warning... which I want to ignore...
    # This is the original warning:
    #
    # /usr/lib/python2.5/site-packages/nltk/__init__.py:117: UserWarning: draw module, ...
    # warnings.warn("draw module, app module, and gui downloader not loaded "
    #

    warnings.filterwarnings('ignore', '.*',)
    #mem_test('after esmre import')
    if not lazy_load('nltk'):
        packages.append('nltk')
        packages_debian.append('python-nltk')
        packages_openbsd.append('py-nltk')
        packages_mac_ports.append('py27-nltk')
        
        msg = '    If you can not install nltk with the system package manager,' \
              ' try the following:\n' \
              '        wget http://pyyaml.org/download/pyyaml/PyYAML-3.09.tar.gz\n' \
              '        tar -xzvf PyYAML-3.09.tar.gz\n' \
              '        cd PyYAML-3.09\n' \
              '        python setup.py install\n' \
              '        cd ..\n' \
              '        wget http://nltk.googlecode.com/files/nltk-2.0b9.tar.gz\n' \
              '        tar -xzvf nltk-2.0b9.tar.gz\n' \
              '        cd nltk-2.0b9\n' \
              '        python setup.py install'
        additional_information.append(msg)
        reason_for_exit = True
    #mem_test('after nltk import')

    if not lazy_load('extlib.SOAPpy.SOAPpy'):
        if not lazy_load('SOAPpy'):
            packages.append('SOAPpy')
            packages_debian.append('python-soappy')
            packages_openbsd.append('py-SOAPpy')
            packages_mac_ports.append('py27-soappy')
            reason_for_exit = True
    #mem_test('after soappy import')
    
    try:
        from pdfminer.converter import TextConverter
    except ImportError:
        packages.append('pdfminer')
        packages_debian.append('python-pdfminer')
        #TODO
        #packages_mac_ports.append()
        reason_for_exit = True
    #mem_test('after pypdf import')

    try:
        from concurrent.futures import Future
    except ImportError:
        packages.append('futures')
        packages_pip.append('futures')
        packages_debian.append('python-concurrent.futures')
        #TODO
        #packages_mac_ports.append()
        reason_for_exit = True
    #mem_test('after pypdf import')
    
    try:
        from OpenSSL import SSL
    except ImportError:
        packages.append('pyOpenSSL')
        packages_debian.append('python-pyopenssl')
        packages_mac_ports.extend(['py27-openssl'])
        packages_openbsd.append('py-openssl')
        reason_for_exit = True
    #mem_test('after ssl import')
    try:
        from lxml import etree
    except ImportError:
        packages.append('lxml')
        packages_debian.append('python-lxml')
        packages_openbsd.append('py-lxml')
        packages_mac_ports.append('py27-lxml')
        reason_for_exit = True
    #mem_test('after lxml import')
    try:
        import pysvn
    except Exception, e:
        # pylint: disable=E1101
        if e.message.startswith('pysvn was built'):
            msg = '    It looks like your pysvn library installation is broken\n'\
                  '    (are you using BT4 R2?). The error we get when importing\n'\
                  '    the pysvn library is "%s". \n\n' \
                  '    This is a BackTrack issue (works with Ubuntu 8.04 and 10.10)\n' \
                  '    that was fixed by them in their devel repositories, in order to\n' \
                  '    enable them you need to follow these steps:\n' \
                  '        1. vim /etc/apt/sources.list\n' \
                  '        2. Un-comment the BackTrack Devel Repository line ' \
                  '(deb http://archive.offensive-security.com/repotest/ ./)' \
                  '        3. apt-get update && apt-get dist-upgrade'

            additional_information.append(msg % e.message)

        packages.append('pysvn')
        packages_debian.append('python-svn')
        packages_openbsd.append('py-pysvn')
        packages_mac_ports.append('py27-pysvn')
        reason_for_exit = True
    #mem_test('after pysvn import')

    if not lazy_load('scapy'):
        packages.append('scapy')
        packages_debian.append('python-scapy')
        packages_openbsd.append('scapy')
        packages_mac_ports.append('scapy')
        reason_for_exit = True
    else:
        try:
            import scapy.config
        except:
            msg = '    Your version of scapy is *very old* and incompatible' \
                  ' with w3af. Please install scapy version >= 2.0 .\n' \
                  '    You may issue the following commands in order to install' \
                  ' the latest version of scapy in your system:\n' \
                  '        cd /tmp\n' \
                  '        wget http://www.secdev.org/projects/scapy/files/scapy-latest.tar.gz\n' \
                  '        tar -xzvf scapy-latest.tar.gz\n' \
                  '        cd scapy-2*\n' \
                  '        sudo python setup.py install\n'
            additional_information.append(msg)
            reason_for_exit = True
        else:
            if not scapy.config.conf.version.startswith('2.'):
                msg = '    Your version of scapy (%s) is not compatible with' \
                      ' w3af. Please install scapy version >= 2.0 .'
                additional_information.append(msg % scapy.config.conf.version)
                reason_for_exit = True
    #mem_test('after scapy import')
    
    try:
        import guess_language
    except ImportError:
        packages.append('guess_language')
        packages_pip.append('guess-language')
        reason_for_exit = True
    
    # Now output the results of the dependency check
    curr_platform = platform.system().lower()
    
    if packages:
        msg = 'Your python installation needs the following packages:\n'
        msg += '    ' + ' '.join(packages)
        print msg, '\n'
    if packages_debian and 'linux' in curr_platform:
        msg = 'On Debian based systems:\n'
        msg += '    sudo apt-get install ' + ' '.join(packages_debian)
        print msg, '\n'
    if packages_pip:
        msg = 'After installing Python\'s pip:\n'
        msg += '    sudo pip install ' + ' '.join(packages_pip)
        print msg, '\n'
    if packages_mac_ports and is_mac(curr_platform):
        msg = 'On Mac OSX with mac ports installed:\n'
        msg += '    sudo port install ' + ' '.join(packages_mac_ports)
        print msg, '\n'
    if packages_openbsd and 'openbsd' in curr_platform:
        msg = 'On OpenBSD 5.1 install the requirements by running:\n'
        msg += '    export PKG_PATH="http://ftp.openbsd.org/pub/OpenBSD/5.1/packages/i386/"\n'
        msg += '    pkg_add -v  ' + ' '.join(packages_openbsd)
        print msg, '\n'
    if additional_information:
        msg = 'Additional information:\n'
        msg += '\n'.join(additional_information)
        print msg

    #Now exit if necessary
    if reason_for_exit:
        exit(1)


def mem_test(when):
    from core.controllers.profiling.ps_mem import get_memory_usage, human
    sorted_cmds, shareds, _, _ = get_memory_usage(None, True, True, True)
    cmd = sorted_cmds[0]
    msg = "%8sB Private + %8sB Shared = %8sB" % (human(cmd[1] - shareds[cmd[0]]),
                                                 human(shareds[cmd[
                                                               0]]), human(cmd[1])
                                                 )
    print 'Total memory usage %s: %s' % (when, msg)


def is_mac(curr_platform):
    return 'darwin' in curr_platform or 'mac' in curr_platform
