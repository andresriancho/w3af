#REQUIRE_LINUX
import re

result = []
users = []
groups = []

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
users.append(parse_user_envvars(read('/etc/apache2/envvars')))
#user.append(parse_user_envvars(open('/proc/PIDAPACHE/environ').read()))
groups.append(parse_group_envvars(read('/etc/apache2/envvars')))
#group.append(parse_group_envvars(open('/proc/PIDAPACHE/environ').read()))

result = list(set(result))
result = [p for p in result if p != '']

for user in users:
    result.append('APACHE_RUN_USER='+user)

for group in groups:
    result.append('APACHE_RUN_GROUP'+group)



