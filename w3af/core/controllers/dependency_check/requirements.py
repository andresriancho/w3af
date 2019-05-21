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


CORE_PIP_PACKAGES = [PIPDependency('pyclamd', 'pyClamd', '0.4.0'),
                     PIPDependency('github', 'PyGithub', '1.21.0'),
                     PIPDependency('git.util', 'GitPython', '2.1.3'),
                     PIPDependency('pybloomfilter', 'pybloomfiltermmap', '0.3.14'),
                     PIPDependency('phply', 'phply', '0.9.1'),
                     PIPDependency('nltk', 'nltk', '3.0.1'),
                     PIPDependency('chardet', 'chardet', '3.0.4'),
                     PIPDependency('tblib', 'tblib', '0.2.0'),
                     PIPDependency('pdfminer', 'pdfminer', '20140328'),
                     PIPDependency('concurrent.futures', 'futures', '3.2.0'),
                     PIPDependency('OpenSSL', 'pyOpenSSL', '18.0.0'),
                     PIPDependency('ndg', 'ndg-httpsclient', '0.4.0'),

                     # We need 0.1.8 because of mitmproxy
                     PIPDependency('pyasn1', 'pyasn1', '0.4.2'),

                     PIPDependency('lxml', 'lxml', '3.4.4'),
                     PIPDependency('scapy.config', 'scapy', '2.4.0'),
                     PIPDependency('guess_language', 'guess-language', '0.2'),
                     PIPDependency('cluster', 'cluster', '1.1.1b3'),
                     PIPDependency('msgpack', 'msgpack', '0.5.6'),
                     PIPDependency('ntlm', 'python-ntlm', '1.0.1'),
                     PIPDependency('Halberd', 'halberd', '0.2.4'),
                     PIPDependency('darts.lib.utils', 'darts.util.lru', '0.5'),
                     PIPDependency('jinja2', 'Jinja2', '2.10'),
                     PIPDependency('vulndb', 'vulndb', '0.1.1'),
                     PIPDependency('markdown', 'markdown', '2.6.1'),

                     # This was used for testing, but now it's required for
                     # regular users too, do not remove!
                     PIPDependency('psutil', 'psutil', '5.4.8'),

                     # Added for the crawl.ds_store plugin
                     PIPDependency('ds_store', 'ds-store', '1.1.2'),

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
                     PIPDependency('pebble', 'pebble', '4.3.8'),

                     # acora speeds up string search, for regular expressions
                     # we use esmre to extract the string literals from the re
                     # and acora to match those against the target string
                     PIPDependency('acora', 'acora', '2.1'),
                     PIPDependency('esmre', 'esmre', '0.3.1'),

                     # String diff by Google
                     PIPDependency('diff_match_patch', 'diff-match-patch', '20121119'),

                     # OpenAPI documentation parser
                     PIPDependency('bravado_core', 'bravado-core', '5.12.1'),

                     # Fast compression library
                     PIPDependency('lz4', 'lz4', '1.1.0'),

                     # Vulners API plugin needs this lib
                     PIPDependency('vulners', 'vulners', '1.3.0'),

                     PIPDependency('ipaddresses', 'ipaddresses', '0.0.2'),

                     # subprocess32 "it is guaranteed to be reliable when used
                     # in threaded applications". Needed this to fix issues in
                     # retirejs that spawns processes from threads
                     PIPDependency('subprocess32', 'subprocess32', '3.5.4')

                     ]

GUI_PIP_EXTRAS = [PIPDependency('xdot', 'xdot', '0.6')]

GUI_PIP_PACKAGES = CORE_PIP_PACKAGES[:]
GUI_PIP_PACKAGES.extend(GUI_PIP_EXTRAS)
