import re
from plugins.attack.payloads.base_payload import base_payload

class hosts(base_payload):
    '''
    This payload shows the hosts allow and deny files.
    '''
    def api_read(self):
        result = {}
        hosts = []

        hosts.append('/etc/hosts')
        hosts.append('/etc/hosts.allow')
        hosts.append('/etc/hosts.deny')

        for file in hosts:
            content = self.shell.read(file)
            if content:
                result.update({file:content})
        return result
        
    def run_read(self):
        hashmap = self.api_read()
        result = []
        if hashmap:
            result.append('Hosts Config Files')
            for file, content in hashmap.iteritems():
                result.append('-------------------------')
                result.append(file)
                result.append('-------------------------')
                result.append(content)
        
        if result == [ ]:
            result.append('Hosts files not found.')
        return result


