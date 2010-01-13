#REQUIRE_LINUX
import re

result = []
user = []
group = []

def parse_user_envvars (envvars_file):
    user = re.search('(?<=APACHE_RUN_USER=)(.*)', envvars_file)
    if user:
        return user.group(1)
    else:
        return ''

def parse_group_envvars (envvars_file):
    user = re.search('(?<=APACHE_RUN_GROUP=)(.*)', envvars_file)
    if user:
        return user.group(1)
    else:
        return ''

#TODO: PAYLOAD CALLING PAYLOAD
user.append(parse_user_envvars(open('/etc/apache2/envvars').read()))
#user.append(parse_user_envvars(open('/proc/PIDAPACHE/environ').read()))
group.append(parse_group_envvars(open('/etc/apache2/envvars').read()))
#group.append(parse_group_envvars(open('/proc/PIDAPACHE/environ').read()))

result = list(set(result))
result = [p for p in result if p != '']
result = 'APACHE_RUN_USER='+user.pop(0)+'\r'+'APACHE_RUN_GROUP'+group.pop(0)



