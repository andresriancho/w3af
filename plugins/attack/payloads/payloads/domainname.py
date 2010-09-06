import re
from plugins.attack.payloads.base_payload import base_payload

class domainname(base_payload):
    '''
    This payload shows server domain name.
    '''
    def api_read(self):
        result = {}
        values = []
        values.append(self.shell.read('/proc/sys/kernel/domainname')[:-1])

        for v in values:
            result.update({'Domain name':v})

        return result

    def run_read(self):
        hashmap = self.api_read()
        result = []
        for k, v in hashmap.iteritems():
            result.append(k+': '+v)
        
        if result == [ ]:
            result.append('Domain name not found.')
        return result
