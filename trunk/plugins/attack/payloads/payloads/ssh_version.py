import re
from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class ssh_version(base_payload):
    '''
    This payload shows the current SSH Server Version
    '''
    def api_read(self, parameters):
        result = {}
        result['ssh_version'] = ''
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

    def run_read(self, parameters):
        api_result = self.api_read( parameters )
        
        if not api_result['ssh_version']:
            return 'SSH version could not be identified.'
        else:
            rows = []
            rows.append( ['SSH version'] ) 
            rows.append( [] )
            
            rows.append( [api_result['ssh_version'],] )
                
            result_table = table( rows )
            result_table.draw( 80 )                    
            return

