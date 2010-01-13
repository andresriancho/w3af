#REQUIRE_LINUX
import re

result = []
users = []

def parse_users_home( etc_passwd ):
    user = re.findall('(?<=/home/)(.*?)\:', etc_passwd)
    if user:
        return user
    else:
        return ''

for user in parse_users_home(open('/etc/passwd').read()):
    result.append('/home/'+str(user)+'/')
