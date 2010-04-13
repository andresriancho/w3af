import re
from plugins.attack.payloads.base_payload import base_payload

class uptime(base_payload):
    '''
    This payload shows server Uptime.
    '''
    def api_read(self):
        result = {}

        uptime = self.shell.read('/proc/uptime')
        uptime = uptime.split(' ')
        uptime[0] = int(float(uptime[0]))
        mins, secs = divmod(int(uptime[0]), 60)
        hours, mins = divmod(mins, 60)
        result['uptime'] = [hours, mins, secs]
        uptime[1] = int(float(uptime[1]))
        mins, secs = divmod(int(uptime[1]), 60)
        hours, mins = divmod(mins, 60)
        result['idletime'] = [hours, mins, secs]
        return result
        
    def run_read(self):
        hashmap = self.api_read()
        result = []
        if hashmap['uptime']:
            hours = hashmap['uptime'][0]
            mins = hashmap['uptime'][1]
            secs = hashmap['uptime'][2]
            result.append('Uptime: %02d:%02d:%02d' % (hours, mins, secs))
        if hashmap['idletime']:
            hours = hashmap['idletime'][0]
            mins = hashmap['idletime'][1]
            secs = hashmap['idletime'][2]
            result.append('Idletime: %02d:%02d:%02d' % (hours, mins, secs))
        if result == [ ]:
            result.append('Uptime information not found.')
        return result
