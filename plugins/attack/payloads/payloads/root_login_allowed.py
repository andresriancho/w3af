#REQUIRE_LINUX
#This payload checks if root user is allowed to login on console.

import re

result = []

def parse_securetty( securetty ):
    console = re.search('^console', securetty)
    if console:
        return console.group(1)
    else:
        return ''

def parse_permit_root_login(config):
    condition = re.findall('(?<=PermitRootLogin )(.*)', config)
    if condition:
        return condition.group(1)
    else:
        return ''

ssh_string = ''
ssh_config_result = run_payload('ssh_config_files')
for config in ssh_config_result:
    if parse_permit_root_login(config) == 'yes':
        ssh_string = 'A SSH Bruteforce attack is posible'
    elif parse_permit_root_login(config) == 'no':
        ssh_string = 'A SSH Bruteforce attack is NOT posible'
    else:
        ssh_string = 'A SSH Bruteforce attack MIGHT be posible'

if parse_securetty(read('/etc/securetty')):
    result.append('Root user is allowed to login on CONSOLE. '+ssh_string)
else:
    result.append('Root user is not allowed to login on CONSOLE. '+ssh_string)
