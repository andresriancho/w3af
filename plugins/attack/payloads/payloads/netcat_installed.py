import re
from plugins.attack.payloads.base_payload import base_payload

class netcat_installed(base_payload):
    '''
    This payload verifies if Netcat is installed and supports "-e"
    '''
    def api_read(self):
        result = []
        files = []

        files.append('/bin/netcat')
        files.append('/etc/alternative/netcat')
        files.append('/bin/nc')

        installed = 'Netcat is not installed'
        support = 'without "-e" support !'
        for file in files:
            file_content = self.shell.self.shell.read(file)
            if file_content:
                installed = 'Netcat is installed'
                if '-e filename' in file_content:
                    support = 'with -e Support !'

        result.append(installed+' '+support)
        return result
    
    def run_read(self):
        result = self.api_read()
        return result
