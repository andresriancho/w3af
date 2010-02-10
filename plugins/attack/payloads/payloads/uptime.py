import re
from plugins.attack.payloads.base_payload import base_payload

class uptime(base_payload):
    '''
    This payload shows Apache distributed configuration files (.htaccess & .htpasswd)
    '''
    def run_read(self):
        result = []

        result.append(self.shell.read('/proc/uptime'))
        return result
