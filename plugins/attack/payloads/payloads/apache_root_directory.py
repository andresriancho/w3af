import re
from plugins.attack.payloads.base_payload import base_payload
import core.data.kb.knowledgeBase as kb
#TODO: TEST
class apache_root_directory(base_payload):
    '''
    This payload finds Apache Root Directories where websites are hosted.
    '''
    def api_read(self):
        result = {}

        def parse_etc_passwd(etc_passwd, user):
            root = re.search('(?<='+user+':/)(.*?)\:', etc_passwd)
            if root:
                return root.group(1)
            else:
                return ''

        def parse_config_file(config_file):
            root = re.search('(?<=DocumentRoot )(.*)', config_file)
            if root:
                return root.group(1)
            else:
                return ''

        users = self.exec_payload('apache_run_user')['apache_run_user'].values()
        if users:
            passwd = self.shell.read('/etc/passwd')
            for user in users:
                result.append('/'+parse_etc_passwd(passwd,  user)+'/')
        
        directory = []
        apache_config_files = self.exec_payload('apache_config_files')['apache_config_files'].values()
        if apache_config_files:
            for file in apache_config_files:
                file_content = self.shell.read(file)
                if parse_config_file(file_content) != '':
                    directory.append(parse_config_file(file_content)+'/')

        if kb.kb.getData('pathdisclosure', 'webroot'):
            directory.append(kb.kb.getData('pathdisclosure', 'webroot'))
        
        directory = list(set(directory))
        directory= [p for p in directory if p != '']
        
        result['apache_root_directory'] = directory

        return result
    
    def run_read(self):
        hashmap = self.api_read()
        result = []
        for k, v in hashmap.iteritems():
            k = k.replace('_', ' ')
            result.append(k.title())
            for elem in v:
                result.append(elem)
        
        if result == [ ]:
            result.append('Apache root directory not found.')
        return result
