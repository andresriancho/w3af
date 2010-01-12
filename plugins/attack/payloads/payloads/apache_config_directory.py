#REQUIRE_LINUX
import re

result = []
paths = []

def parse_apache2_init( apache_file_read ):
    directory = re.search('(?<=APACHE_PID_FILE needs to be defined in )(.*?)envvars', apache_file_read)
    return directory.group(1)

def parse_apache_init( apache_file_read ):
    directory = re.search('(?<=APACHE_HOME=")(.*?)\"', apache_file_read)
    return directory.group(1)
    
def parse_httpd_file( httpd_file_read ):
    directory = re.search('(?<=# config: )(.*?)/httpd.conf', httpd_file_read)
    return directory.group(1)

def check_apache_config_dir( apache_config_directory ):
    if read( apache_config_directory + 'httpd.conf') == '':
        return False
    else:
        return True

paths.append( parse_apache2_init( read ('/etc/init.d/apache2') ) )
paths.append( parse_apache_init( read ('/etc/init.d/apache') ) )
paths.append( parse_apache_init( read ('/etc/rc.d/init.d/httpd') ) )
paths.append('/etc/apache2/')
paths.append('/etc/apache/')
paths.append('/etc/httpd/')
paths.append('/usr/local/apache2/conf/')
paths.append('/usr/local/apache/conf/')
paths.append('/opt/apache/conf/')
paths.append('/etc/httpd/conf/')



for path in paths:
    if check_apache_config_dir(path):
        result.append(path)
result = [p for p in result if p != '']
