import re
from plugins.attack.payloads.base_payload import base_payload

class uptime(base_payload):
    '''
    This payload shows server Uptime.
    '''
    def run_read(self):
        result = []
        
        uptime = self.shell.read('/proc/uptime')
        uptime = uptime.split(' ')
        uptime[0] = int(float(uptime[0]))
        mins, secs = divmod(int(uptime[0]), 60)
        hours, mins = divmod(mins, 60)
        result.append('Uptime: %02d:%02d:%02d' % (hours, mins, secs))
        uptime[1] = int(float(uptime[1]))
        mins, secs = divmod(int(uptime[1]), 60)
        hours, mins = divmod(mins, 60)
        result.append('Idletime: %02d:%02d:%02d' % (hours, mins, secs))
        if result == [ ]:
            result.append('Uptime information not found.')
        return result
