#REQUIRE_LINUX
import re

result = []

result.append(read( '/proc/sys/kernel/domainname')[:-1])
result = [p for p in result if p != '']
