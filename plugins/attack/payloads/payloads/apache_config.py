#REQUIRE_LINUX
#This payload displays content of Apache Configuration Files.

import re

result = []
files = []


#def parse_config (apache_config):
#    config = re.findall('^(?!.?#)(.*?)$', apache_config, re.MULTILINE)
#    if config:
#        return config
#    else:
#        return ''

apache_config_files = run_payload('apache_config_files')
if apache_config_files:
    for file in apache_config_files:
        result.append('------------------------- ')
        result.append('FILE => '+file)
        result.append(read(file))

result = [p for p in result if p != '']
