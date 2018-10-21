"""
keys.py

Copyright 2006 Andres Riancho

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

import w3af.core.data.constants.severity as severity
from w3af.core.data.quick_match.multi_in import MultiIn
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.kb.info import Info


class keys(GrepPlugin):
    """
    Grep every page for public and private keys.

    :author: Yvonne Kim
    """
    def __init__(self):
        GrepPlugin.__init__(self)

        self.PUBLIC = 'public'
        self.PRIVATE = 'private'

        PUBLIC = 'public'
        PRIVATE = 'private'

        KEY_FORMATS = (
            # RSA (PKCS1)
            ('-----BEGIN RSA PRIVATE KEY-----', ('RSA-PRIVATE', PRIVATE)), 
            ('-----BEGIN RSA PUBLIC KEY-----', ('RSA-PUBLIC', PUBLIC)),
            ('ssh-rsa', ('RSA-PUBLIC', PUBLIC)),
            
            # DSA
            ('-----BEGIN DSA PRIVATE KEY-----', ('DSA-PRIVATE', PRIVATE)),
            ('-----BEGIN DSA PUBLIC KEY-----', ('DSA-PUBLIC', PUBLIC)),
            ('ssh-dss', ('DSA-PUBLIC', PUBLIC)),
            
            # Elliptic Curve
            ('-----BEGIN EC PRIVATE KEY-----', ('EC-PRIVATE', PRIVATE)),
            ('-----BEGIN EC PUBLIC KEY-----', ('EC-PUBLIC', PUBLIC)),
            ('ecdsa-sha2-nistp256', ('EC-PUBLIC', PUBLIC)),
            
            # SSH2
            ('---- BEGIN SSH2 PUBLIC KEY ----', ('SSH2-PRIVATE', PRIVATE)),
            ('---- BEGIN SSH2 PRIVATE KEY ----', ('SSH2-PUBLIC', PUBLIC)),

            # ed25519 (OpenSSH)
            ('-----BEGIN OPENSSH PRIVATE KEY-----', ('ED25519-SSH-PRIVATE', PRIVATE)),
            ('-----BEGIN OPENSSH PUBLIC KEY-----', ('ED25519-SSH-PUBLIC', PUBLIC)),
            ('ssh-ed25519', ('ED25519-SSH-PUBLIC', PUBLIC)),
            
            # PKCS8
            ('-----BEGIN PRIVATE KEY-----', ('PKCS8-PRIVATE', PRIVATE)),
            ('-----BEGIN PUBLIC KEY-----', ('PKCS8-PUBLIC', PUBLIC)),
            ('-----BEGIN ENCRYPTED PRIVATE KEY-----', ('PKCS8-ENCRYPTED-PRIVATE', PRIVATE)),
            ('-----BEGIN ENCRYPTED PUBLIC KEY-----', ('PKCS8-ENCRYPTED-PUBLIC', PUBLIC)),
            
            # XML
            ('<RSAKeyPair>', ('XML-RSA', PRIVATE)),
            ('<RSAKeyValue>', ('.NET-XML-RSA', PUBLIC))
        )        

        self._multi_in = MultiIn(KEY_FORMATS)


    def grep(self, request, response):
        """
        Plugin entry point, find the error pages and report them.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        if not response.is_text_or_html():
            return

        if not response.get_code() == 200:
            return

        for _, (key, keypair_type) in self._multi_in.query(response.body):
            desc = u'The URL: "%s" discloses a key of type: "%s"'
            desc %= (response.get_url(), key)

            if keypair_type == self.PUBLIC:
                item = Info(
                    'Public key disclosure', desc, response.id, self.get_name())

            elif keypair_type == self.PRIVATE:
                item = Vuln(
                    'Private key disclosure', desc, severity.HIGH, response.id, self.get_name())                

            item.set_url(response.get_url())
            item.add_to_highlight(key)

            self.kb_append(self, 'keys', item)
        

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """

        return """
        This plugin scans responses for keys in a few of the most common formats.
        Private keys are classified as vulnerabilities while public keys are stored
        as information. 

        """
