#REQUIRE_LINUX
import re

result = []
allow = []
deny = []
hosts = []

def parse_hosts (etc_hosts):
    hosts = re.findall('^(?!#)(.*?)$', etc_hosts, re.MULTILINE)
    if hosts:
        return hosts
    else:
        return ''

hosts = parse_hosts(read('/etc/hosts'))
allow = parse_hosts(read('/etc/hosts.allow'))
deny = parse_hosts(read('/etc/hosts.deny'))
#Resolv.conf?

result.append('Hosts:')
for host in hosts:
    result.append(host)

result.append('Hosts Allowed:')
for all in allow:
    result.append(all)

result.append('Hosts Denied:')
for den in deny:
    result.append(den)

result = [p for p in result if p != '']
