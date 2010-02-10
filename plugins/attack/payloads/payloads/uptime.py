import re
from plugins.attack.payloads.base_payload import base_payload

class uptime(base_payload):
    '''
    This payload shows server Uptime.
    '''
    def run_read(self):
        result = []
        uptime = self.shell.read('/proc/uptime')
        uptime.split(' ')
        mins, secs = divmod(secs, 60)
        hours, mins = divmod(mins, 60)
        result.append('%02d:%02d:%02d' % (hours, mins, secs))
        return result
