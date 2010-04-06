import re
from plugins.attack.payloads.base_payload import base_payload

class arp_cache(base_payload):
    '''
    This payload shows the ARP CACHE
    '''
    def api_read(self):
        result = []
        files = []

        files.append('/proc/net/arp')
        files.append('/etc/networks')
        files.append('/etc/ethers')

        for file in files:
            if self.shell.read(file) != '':
                result.append('-------------------------')
                result.append('FILE => '+file)
                result.append(self.shell.read(file))
        return result
    
    def run_read(self):
        result = self.api_read()
        if result == [ ]:
            result.append('ARP Cache configuration files not found.')
        return result
