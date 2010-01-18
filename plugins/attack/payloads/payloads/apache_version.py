#REQUIRE_LINUX
import re

result = []

def parse_apache_binary (binary):
    version = re.search('(?<=/build/buildd/)(.*?)/',  binary)
    version2 = re.search('(?<=Apache)/(\d\.\d\.\d*)(.*?) ',  binary)
    if version and version2:
        return [version.group(1), version2.group(1)]
    elif version:
        return [version.group(1)]
    elif version2:
        return [version.group(1)]
    else:
        return ''

for version in parse_apache_binary(read('/usr/sbin/apache2')):
    result.append(version)

for version in parse_apache_binary(read('/usr/sbin/httpd')):
    result.append(version)

result = list(set(result))
result = [p for p in result if p != '']
