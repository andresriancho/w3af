import re
from plugins.attack.payloads.base_payload import base_payload

class domainname(base_payload):
    '''
    This payload shows server domain name.
    '''
    def api_read(self):
        result = []

        result.append(self.shell.read('/proc/sys/kernel/domainname')[:-1])
        result = [p for p in result if p != '']
        if result == [ ]:
            result.append('Domainname not found.')
        return result

    def run_read(self):
        result = self.api_read()
        if result == [ ]:
            result.append('Server domain name not found.')
        return result
