#REQUIRE_LINUX
import re

result = []
values = []
values.append(read( '/etc/hostname')[:-1])
values.append(read('/proc/sys/kernel/hostname')[:-1])

for v in values:
    if not v in result:
       result.append(v)

result = [p for p in result if p != '']
