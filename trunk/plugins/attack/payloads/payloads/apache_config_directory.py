import re
from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class apache_config_directory(base_payload):
    '''
    This payload finds the Apache Config Directory
    '''
    def api_read(self, parameters):
        result = {}
        result['apache_directory'] = []
        paths = []

        def parse_apache2_init( apache_file_read ):
            directory = re.search('(?<=APACHE_PID_FILE needs to be defined in )(.*?)envvars', apache_file_read)
            if directory:
                return directory.group(1)
            else:
                return ''

        def parse_apache_init( apache_file_read ):
            directory = re.search('(?<=APACHE_HOME=")(.*?)\"', apache_file_read)
            if directory:
                return directory.group(1)
            else:
                return ''
            
        def parse_httpd_file( httpd_file_read ):
            directory = re.search('(?<=# config: )(.*?)/httpd.conf', httpd_file_read)
            if directory:
                return directory.group(1)
            else:
                return ''

        def check_apache_config_dir( apache_config_directory ):
            httpd = self.shell.read( apache_config_directory + 'httpd.conf')
            apache = self.shell.read( apache_config_directory + 'apache2.conf')
            if httpd != '' or apache != '':
                return True
            else:
                return False

        paths.append( parse_apache2_init( self.shell.read('/etc/init.d/apache2') ) )
        paths.append( parse_apache_init( self.shell.read('/etc/init.d/apache') ) )
        paths.append('/etc/apache2/')
        paths.append('/etc/apache/')
        paths.append('/etc/httpd/')
        paths.append('/usr/local/apache2/conf/')
        paths.append('/usr/local/apache/conf/')
        paths.append('/usr/local/etc/apache/')
        paths.append('/usr/local/etc/apache2/')
        paths.append('/opt/apache/conf/')
        paths.append('/etc/httpd/conf/')
        paths.append('/usr/pkg/etc/httpd/')
        paths.append('/usr/local/etc/apache22/')

        for path in paths:
            if check_apache_config_dir(path):
                result['apache_directory'].append(path)
        
        # uniq
        result['apache_directory'] = list( set(result['apache_directory']))
        
        return result
    
    def run_read(self, parameters):
        api_result = self.api_read( parameters )
                
        if not api_result['apache_directory']:
            return 'Apache configuration directory not found.'
        else:
            rows = []
            rows.append( ['Apache directories',] )
            rows.append( [] )
            for key_name in api_result:
                for path in api_result[key_name]:
                    rows.append( [path,] )
                    
            result_table = table( rows )
            result_table.draw( 80 )
            return

