#REQUIRE_LINUX
import re

result = []
values = []
values.append(open( '/etc/hostname').read()[:-1])
values.append(open( '/proc/sys/kernel/hostname').read()[:-1])

for v in values:
    if not v in result:
       result.append(v)

result = [p for p in result if p != '']
