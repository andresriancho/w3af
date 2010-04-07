import re
from plugins.attack.payloads.base_payload import base_payload

class netcat_installed(base_payload):
    '''
    This payload verifies if Netcat is installed and supports "-e filename" (program to exec after connect)
    '''
    def api_read(self):
        result = {}
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

        result = {'installed':installed,  'supportE':support}
        return result
    
    def run_read(self):
        hashmap = self.api_read()
        result = []
        msg = ''
        if hashmap['installed']:
            msg += 'Netcat is installed'
            if hashmap['supportE']:
                msg += ' with "-e" support !'
            else:
                msg += ' without "-e" support'
        else:
            msg += 'Netcat is not installed.'
        
        result.append(msg)
        return result
