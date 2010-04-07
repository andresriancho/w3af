import re
from plugins.attack.payloads.base_payload import base_payload

class ssh_version(base_payload):
    '''
    This payload shows the current SSH Server Version
    '''
    def api_read(self):
        result = {}
        files = []

        def parse_binary(bin_ssh):
            version = re.search('(?<=OpenSSH)(.*?)\x00', bin_ssh)
            if version:
                return version.group(1)
            else:
                return ''

#TODO: Add more binaries
        version = self.shell.read('/usr/sbin/sshd')
        if version:
            result['ssh_version'] = 'OpenSSH'+parse_binary(version)
        return result

    def run_read(self):
        hashmap = self.api_read()
        result = []
        
        for k, v in hashmap.iteritems():
            k = k.replace('_', ' ')
            result.append(k.title()+': '+v)
        if result == [ ]:
            result.append('SSH version not found.')
        return result

