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

CORE = 1
GUI = 2

CORE_PIP_PACKAGES = [PIPDependency('clamd', 'clamd', '1.0.1'),
                     PIPDependency('github', 'PyGithub', '1.21.0'),
                     PIPDependency('git.util', 'GitPython', '0.3.2.RC1'),
                     PIPDependency('pybloomfilter', 'pybloomfiltermmap', '0.3.14'),
                     PIPDependency('esmre', 'esmre', '0.3.1'),
                     PIPDependency('phply', 'phply', '0.9.1'),
                     PIPDependency('stopit', 'stopit', '1.1.0'),
                     PIPDependency('nltk', 'nltk', '3.0.1'),
                     PIPDependency('chardet', 'chardet', '2.1.1'),
                     PIPDependency('tblib', 'tblib', '0.2.0'),
                     PIPDependency('pdfminer', 'pdfminer', '20140328'),
                     PIPDependency('concurrent.futures', 'futures', '2.1.5'),
                     PIPDependency('OpenSSL', 'pyOpenSSL', '0.13.1'),
                     PIPDependency('ndg', 'ndg-httpsclient', '0.3.3'),

                     # There is a newer pyasn1 release, but we're requiring this
                     # one to make Kali packaging easier, see:
                     # https://github.com/andresriancho/w3af/issues/8339
                     PIPDependency('pyasn1', 'pyasn1', '0.1.3'),

                     PIPDependency('lxml', 'lxml', '3.4.4'),
                     PIPDependency('scapy.config', 'scapy-real', '2.2.0-dev'),
                     PIPDependency('guess_language', 'guess-language', '0.2'),
                     PIPDependency('cluster', 'cluster', '1.1.1b3'),
                     PIPDependency('msgpack', 'msgpack-python', '0.4.4'),
                     PIPDependency('ntlm', 'python-ntlm', '1.0.1'),
                     PIPDependency('Halberd', 'halberd', '0.2.4'),
                     PIPDependency('darts.lib.utils', 'darts.util.lru', '0.5'),
                     PIPDependency('jinja2', 'Jinja2', '2.7.3'),
                     PIPDependency('vulndb', 'vulndb', '0.0.17'),
                     PIPDependency('markdown', 'markdown', '2.6.1'),

                     # https://gist.github.com/andresriancho/cf2fa1ce239b30f37bd9
                     PIPDependency('ruamel.ordereddict',
                                   'ruamel.ordereddict',
                                   '0.4.8')]

GUI_PIP_EXTRAS = [PIPDependency('xdot', 'xdot', '0.6')]

GUI_PIP_PACKAGES = CORE_PIP_PACKAGES[:]
GUI_PIP_PACKAGES.extend(GUI_PIP_EXTRAS)