#REQUIRE_LINUX
import re

result = []
files = []


def parse_binary(bin_ssh):
    version = re.search('(OpenSSH(.*?))\%s', bin_ssh)
    if version:
        return version.group(1)
    else:
        return ''

result.append('Version => '+parse_binary(read('/usr/sbin/sshd')))
