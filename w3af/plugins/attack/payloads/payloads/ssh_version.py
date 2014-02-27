import re
from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class ssh_version(Payload):
    """
    This payload shows the current SSH Server Version
    """
    def api_read(self):
        result = {}
        result['ssh_version'] = ''

        def parse_binary(bin_ssh):
            version = re.search('(?<=OpenSSH)(.*?)\x00', bin_ssh)
            if version:
                return version.group(1)
            else:
                return ''

        # TODO: Add more binaries
        # Please note that this only works IF the remote end allows us to use
        # php wrappers and read the binary file with base64
        version = self.shell.read('/usr/sbin/sshd')
        if version:
            result['ssh_version'] = 'OpenSSH' + parse_binary(version)

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result['ssh_version']:
            return 'SSH version could not be identified.'
        else:
            rows = []
            rows.append(['SSH version'])
            rows.append([])

            rows.append([api_result['ssh_version'], ])

            result_table = table(rows)
            result_table.draw(80)
            return rows
