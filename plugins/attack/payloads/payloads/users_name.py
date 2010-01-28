#REQUIRE_LINUX
#This payload shows users name parsing the /etc/passwd file
import re

result = []
users = []

def parse_users_name( etc_passwd ):
    user = re.findall('^(.*?)\:', etc_passwd,  re.MULTILINE)
    if user:
        return user
    else:
        return ''

for user in parse_users_name(read('/etc/passwd')):
    result.append(str(user))
