#REQUIRE_LINUX
#This payload shows DHCP Server configuration files
result = []
files = []

files.append('/etc/dhcpd.conf')
files.append('/var/lib/dhcp/dhcpd')
files.append('/etc/dhcp3/dhclient.conf')
files.append('/etc/dhclient.conf')
files.append('/usr/local/etc/dhcpd.conf')

for file in files:
    if read(file) != '':
        result.append('-------------------------')
        result.append('FILE => '+file)
        result.append(read(file))

result = [p for p in result if p != '']
