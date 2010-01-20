#REQUIRE_LINUX

import re

result = []
paths = []

def parse_mysql_init( mysql_init ):
    directory = re.search('(?<=$0: WARNING: )(.*?)my.cnf cannot', mysql_init)
    if directory:
        return directory.group(1)
    else:
        return ''

def check_mysql_config_dir( mysql ):
    my = read( mysql+ 'my.cnf')
    if my != '':
        return True
    else:
        return False

paths.append( parse_mysql_init( read('/etc/init.d/mysql') ) )
paths.append('/etc/mysql/')
folders = run_payload('users_folders')
for folder in folders:
    paths.append(folder)

for path in paths:
    if check_mysql_config_dir(path):
        result.append(path)

result = list(set(result))
result = [p for p in result if p != '']


