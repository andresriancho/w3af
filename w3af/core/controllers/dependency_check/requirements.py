"""
requirements.py

Copyright 2013 Andres Riancho

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
from w3af.core.controllers.dependency_check.pip_dependency import PIPDependency

PHPLY_GIT = 'git+https://github.com/andresriancho/phply.git#egg=phply'
PHPLY_GIT_TGZ = 'https://github.com/andresriancho/phply/archive/0.9.tar.gz#egg=phply'

PIP_PACKAGES = [PIPDependency('clamd', 'clamd', '1.0.1'),
                PIPDependency('github', 'PyGithub', '1.21.0'),
                PIPDependency('git.util', 'GitPython', '0.3.2.RC1'),
                PIPDependency('pybloomfilter', 'pybloomfiltermmap', '0.3.11'),
                PIPDependency('esmre', 'esmre', '0.3.1'),
                PIPDependency('phply', 'phply', 'dev', git_src=PHPLY_GIT,
                              tgz_src=PHPLY_GIT_TGZ),
                PIPDependency('nltk', 'nltk', '2.0.4'),
                PIPDependency('chardet', 'chardet', '2.1.1'),
                PIPDependency('pdfminer', 'pdfminer', '20110515'),
                PIPDependency('concurrent.futures', 'futures', '2.1.5'),
                PIPDependency('OpenSSL', 'pyOpenSSL', '0.13.1'),
                PIPDependency('lxml', 'lxml', '2.3.2'),
                PIPDependency('scapy.config', 'scapy-real', '2.2.0-dev'),
                PIPDependency('guess_language', 'guess-language', '0.2'),
                PIPDependency('cluster', 'cluster', '1.1.1b3'),
                PIPDependency('msgpack', 'msgpack-python', '0.2.4'),
                PIPDependency('ntlm', 'python-ntlm', '1.0.1'),
                PIPDependency('Halberd', 'halberd', '0.2.4'),]
