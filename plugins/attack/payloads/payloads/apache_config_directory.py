import re
from plugins.attack.payloads.base_payload import base_payload

class apache_config_directory(base_payload):
    '''
    This payload finds the Apache Config Directory
    '''
    def api_read(self):
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
                result['apache_directory'] .append(path)

        return result
    
    def run_read(self):
        hashmap = self.api_read()
        result = []
        
        for k, v in hashmap.iteritems():
            k = k.replace('_', ' ')
            result.append(k.title())
            for directory in v:
                result.append(directory)
        
        if result == [ ]:
            result.append('Apache configuration directory not found.')
        return result
