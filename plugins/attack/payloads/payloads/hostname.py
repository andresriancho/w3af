import re
from plugins.attack.payloads.base_payload import base_payload

class hostname(base_payload):
    '''
    This payload shows the server hostname
    '''
    def run_read(self):
        result = []
        values = []
        values.append(self.shell.read('/etc/hostname')[:-1])
        values.append(self.shell.read('/proc/sys/kernel/hostname')[:-1])

        for v in values:
            if not v in result:
               result.append(v)

        result = [p for p in result if p != '']
        return result
        
