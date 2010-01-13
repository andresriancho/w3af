#REQUIRE_LINUX
import re

result = []
allow = []
deny = []
hosts = []

def parse_etc_hosts (etc_hosts):
    hosts = re.findall('(?!#)(.*?)$', etc_hosts)
    if hosts:
        return hosts
    else:
        return ''

def parse_hosts_allow(hosts_allow):
    allow = re.findall('(?!#)(.*?)$', hosts_allow)
    if allow:
        return allow
    else:
        return ''

def parse_hosts_deny(hosts_deny):
    deny = re.findall('(?!#)(.*?)$', hosts_deny)
    if deny:
        return deny
    else:
        return ''

hosts = parse_etc_hosts(read('/etc/hosts'))
allow = parse_hosts_allow(read('/etc/hosts.allow'))
deny = parse_hosts_deny(read('/etc/hosts.deny'))
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
