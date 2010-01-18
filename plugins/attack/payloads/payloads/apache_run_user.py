#REQUIRE_LINUX
import re

result = []
users = []

def parse_user_envvars (envvars_file):
    user = re.search('(?<=APACHE_RUN_USER=)(.*)', envvars_file)
    if user:
        return user.group(1)
    else:
        return ''

apache_dir = run_payload('apache_config_directory')
if apache_dir:
    for dir in apache_dir:
        users.append(parse_user_envvars(read(dir+'envvars')))

#TODO: ROOT users.append(parse_user_envvars(open('/proc/PIDAPACHE/environ').read()))

for user in users:
    result.append(user)

result = list(set(result))
result = [p for p in result if p != '']

