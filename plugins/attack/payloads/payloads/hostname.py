import re
from plugins.attack.payloads.base_payload import base_payload

class hostname(base_payload):
    '''
    This payload shows the server hostname
    '''
    def api_read(self):
        result = {}
        
        values = []
        values.append(self.shell.read('/etc/hostname')[:-1])
        values.append(self.shell.read('/proc/sys/kernel/hostname')[:-1])

        for v in values:
            result.update({'Hostname':v})

        return result
        
    def run_read(self):
        hashmap = self.api_read()
        result = []
        for k, v in hashmap.iteritems():
            result.append(k+': '+v)
        
        if result == [ ]:
            result.append('Hostname not found.')
        return result
        
