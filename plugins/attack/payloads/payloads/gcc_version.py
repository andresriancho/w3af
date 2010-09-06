import re
from plugins.attack.payloads.base_payload import base_payload

class gcc_version(base_payload):
    '''
    This payload shows the current GCC Version
    '''
    def api_read(self):
        result = {}

        def parse_gcc_version( proc_version ):
            gcc_version = re.search('(?<=gcc version ).*?\)', proc_version)
            if gcc_version:
                return gcc_version.group(0)
            else:
                return ''
        
        version = parse_gcc_version( self.shell.read('/proc/version'))
        if version:
            result['gcc_version'] = version

        return result
    
    def run_read(self):
        hashmap = self.api_read()
        result = []
        
        for k, v in hashmap.iteritems():
            k = k.replace('_', ' ')
            result.append(k.title()+': '+v)
        
        if result == [ ]:
            result.append('GCC Version not found.')
        return result
        
