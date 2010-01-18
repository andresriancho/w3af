#REQUIRE_LINUX
import re

result = []
files = []

apache_dir = run_payload('apache_config_directory')
files.append('apache2.conf')
files.append('httpd.conf')
files.append('magic')
files.append('envvars')
files.append('ports.conf')
files.append('conf.d/security')
files.append('sites-available/default')
files.append('sites-available/default-ssl')

if apache_dir:
    for dir in apache_dir:
        for file in files:
            if read(dir+file) != '':
                result.append(dir+file)

result = [p for p in result if p != '']

