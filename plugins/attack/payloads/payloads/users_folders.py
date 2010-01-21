#REQUIRE_LINUX
import re

result = []
users = []

def parse_users_folders( etc_passwd ):
    user = re.findall('(?<=/)(.*?)\:', etc_passwd)
    if user:
        return user
    else:
        return ''

for user in parse_users_folders(read('/etc/passwd')):
    result.append('/'+str(user)+'/')
