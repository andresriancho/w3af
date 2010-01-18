#REQUIRE_LINUX
import re

result = []
groups = []

def parse_group_envvars (envvars_file):
    user = re.search('(?<=APACHE_RUN_GROUP=)(.*)', envvars_file)
    if user:
        return user.group(1)
    else:
        return ''

apache_dir = run_payload('apache_config_directory')
if apache_dir:
    for dir in apache_dir:
        groups.append(parse_group_envvars(read(dir+'envvars')))
#group.append(parse_group_envvars(open('/proc/PIDAPACHE/environ').read()))

for group in groups:
    result.append(group)

result = list(set(result))
result = [p for p in result if p != '']





