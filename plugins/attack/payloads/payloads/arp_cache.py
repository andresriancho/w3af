import re
from plugins.attack.payloads.base_payload import base_payload

class arp_cache(base_payload):
    '''
    This payload shows the ARP CACHE
    '''
    def api_read(self):
        result = {}
        files = []

        files.append('/proc/net/arp')
        files.append('/etc/networks')
        files.append('/etc/ethers')

        for file in files:
            content = self.shell.read(file)
            if content != '':
                result .update({file:content})
        return result
    
    def run_read(self):
        hashmap = self.api_read()
        result = []
        if hashmap:
            result.append('ARP Cache')
            for file, content in hashmap.iteritems():
                result.append('-------------------------')
                result.append(file)
                result.append('-------------------------')
                result.append(content)
        
        if result == [ ]:
            result.append('ARP Cache configuration files not found.')
        return result
