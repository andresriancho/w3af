import re
from plugins.attack.payloads.base_payload import base_payload

class os_fingerprint(base_payload):
    '''
    This payload detect OS.
    '''
    def api_read(self):
        result = {}

        if self.shell.read('/proc/sys/kernel/ostype')[:-1]  == 'Linux':
            result['os'] = 'Linux'
        else:
            result['os'] = 'Windows'

        return result
    
    def run_read(self):
        hashmap = self.api_read()
        result = []
        if hashmap:
            result.append('OS Detected: '+hashmap['os'])
        if result == [ ]:
            result.append('Can not detect OS')
        return result
