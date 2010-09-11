import re
from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class netcat_installed(base_payload):
    '''
    This payload verifies if Netcat is installed and supports "-e filename" (program to exec after connect)
    '''
    def api_read(self):
        
        files = []
        files.append('/bin/netcat')
        files.append('/etc/alternative/netcat')
        files.append('/bin/nc')

        for file in files:
            file_content = self.shell.read(file)
            installed = False
            support = False
            if file_content:
                installed = True
                if '-e filename' in file_content:
                    support = True

        result = {'netcat_installed': str(installed),  'supports_shell_bind': str(support) }
        return result
    
    def run_read(self):
        api_result = self.api_read()
        
        rows = []
        rows.append( ['Description', 'Value'] ) 
        rows.append( [] )
        for key in api_result:
            rows.append( [key, api_result[key] ] )
                          
        result_table = table( rows )
        result_table.draw( 80 )                    
        return

