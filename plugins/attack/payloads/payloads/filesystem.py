import re
from plugins.attack.payloads.base_payload import base_payload

class filesystem(base_payload):
    '''
    This payload shows filesystem info.
    '''
    def run_read(self):
        result = []
        files = []

        files.append('/etc/fstab')
        files.append('/etc/vfstab')
        files.append('/etc/mtab')
        files.append('/proc/mounts')

        for file in files:
            if self.shell.read(file) != '':
                result.append('-------------------------')
                result.append('FILE => '+file)
                result.append(self.shell.read(file))

        result = [p for p in result if p != '']
        if result == [ ]:
            result.append('Filesystem configuration files not found.')
        return result
