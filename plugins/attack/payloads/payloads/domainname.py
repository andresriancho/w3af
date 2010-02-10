import re
from plugins.attack.payloads.base_payload import base_payload

class domainname(base_payload):
    '''
    This payload shows server domain name.
    '''
    def run_read(self):
        result = []

        result.append(self.shell.read('/proc/sys/kernel/domainname')[:-1])
        result = [p for p in result if p != '']
        return result
