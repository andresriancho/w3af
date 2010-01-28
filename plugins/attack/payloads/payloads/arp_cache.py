#REQUIRE_LINUX
#This payload shows the ARP CACHE

result = []
files = []

files.append('/proc/net/arp')
files.append('/etc/networks')
files.append('/etc/ethers')

for file in files:
    if read(file) != '':
        result.append('-------------------------')
        result.append('FILE => '+file)
        result.append(read(file))
