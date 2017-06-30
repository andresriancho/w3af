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


CORE_PIP_PACKAGES = [PIPDependency('pyclamd', 'pyClamd', '0.3.15'),
                     PIPDependency('github', 'PyGithub', '1.21.0'),
                     PIPDependency('git.util', 'GitPython', '2.1.3'),
                     PIPDependency('pybloomfilter', 'pybloomfiltermmap', '0.3.14'),
                     PIPDependency('esmre', 'esmre', '0.3.1'),
                     PIPDependency('phply', 'phply', '0.9.1'),
                     PIPDependency('nltk', 'nltk', '3.0.1'),
                     PIPDependency('chardet', 'chardet', '3.0.4'),
                     PIPDependency('tblib', 'tblib', '0.2.0'),
                     PIPDependency('pdfminer', 'pdfminer', '20140328'),
                     PIPDependency('concurrent.futures', 'futures', '2.1.5'),
                     PIPDependency('OpenSSL', 'pyOpenSSL', '0.15.1'),
                     PIPDependency('ndg', 'ndg-httpsclient', '0.3.3'),

                     # We need 0.1.8 because of mitmproxy
                     PIPDependency('pyasn1', 'pyasn1', '0.2.3'),

                     PIPDependency('lxml', 'lxml', '3.4.4'),
                     PIPDependency('scapy.config', 'scapy-real', '2.2.0-dev'),
                     PIPDependency('guess_language', 'guess-language', '0.2'),
                     PIPDependency('cluster', 'cluster', '1.1.1b3'),
                     PIPDependency('msgpack', 'msgpack-python', '0.4.4'),
                     PIPDependency('ntlm', 'python-ntlm', '1.0.1'),
                     PIPDependency('Halberd', 'halberd', '0.2.4'),
                     PIPDependency('darts.lib.utils', 'darts.util.lru', '0.5'),
                     PIPDependency('jinja2', 'Jinja2', '2.7.3'),
                     PIPDependency('vulndb', 'vulndb', '0.0.19'),
                     PIPDependency('markdown', 'markdown', '2.6.1'),

                     # This was used for testing, but now it's required for
                     # regular users too, do not remove!
                     PIPDependency('psutil', 'psutil', '2.2.1'),

                     # Console colors
                     PIPDependency('termcolor', 'termcolor', '1.1.0'),

                     # We "outsource" the HTTP proxy feature to mitmproxy
                     PIPDependency('mitmproxy', 'mitmproxy', '0.13'),

                     # https://gist.github.com/andresriancho/cf2fa1ce239b30f37bd9
                     PIPDependency('ruamel.ordereddict',
                                   'ruamel.ordereddict',
                                   '0.4.8'),

                     # Only used by the REST API, but in the future the console
                     # and GUI will consume it so it's ok to put this here
                     PIPDependency('Flask', 'Flask', '0.10.1'),
                     PIPDependency('yaml', 'PyYAML', '3.12'),

                     # tldextract extracts the tld from any domain name
                     PIPDependency('tldextract', 'tldextract', '1.7.2'),

                     # pebble multiprocessing
                     PIPDependency('pebble', 'pebble', '4.3.2'),
                     ]

GUI_PIP_EXTRAS = [PIPDependency('xdot', 'xdot', '0.6')]

GUI_PIP_PACKAGES = CORE_PIP_PACKAGES[:]
GUI_PIP_PACKAGES.extend(GUI_PIP_EXTRAS)
