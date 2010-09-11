from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table

class users_name(base_payload):
    '''
    This payload shows users name
    '''
    def api_read(self):
        result = {}

        passwd = self.shell.read('/etc/passwd')
        if passwd:
            for line in passwd.split('\n'):
                if line.strip() != '':
                    splitted_line = line.split(':')
                    user = splitted_line[0]
                    directory = splitted_line[-1]
                    result[user] = directory
        return result
    
    def run_read(self):
        hashmap = self.api_read()
        result = []
        if hashmap:
            result.append('User --> Folder')
        for user, folder in hashmap.iteritems():
            result.append(user+' --> '+folder)
        if result == [ ]:
            result.append('Users name not found.')
        return result
