import re
from plugins.attack.payloads.base_payload import base_payload

class ssh_version(base_payload):
    '''
    '''
    def api_read(self):
        result = []
        files = []

        def parse_binary(bin_ssh):
            version = re.search('(?<=OpenSSH)(.*?)\x00', bin_ssh)
            if version:
                return version.group(1)
            else:
                return ''

        ver = self.shell.read('/usr/sbin/sshd')
        if ver:
            result.append('Version => '+'OpenSSH'+parse_binary(ver))
        return result

    def run_read(self):
        result = self.api_read()
        if result == [ ]:
            result.append('SSH version not found.')
        return result

