#REQUIRE_LINUX

import re

result = []
files = []

files.append('/etc/fstab')
files.append('/etc/vfstab')
files.append('/etc/mtab')
files.append('/proc/mounts')

for file in files:
    if read(file) != '':
        result.append('-------------------------')
        result.append('FILE => '+file)
        result.append(read(file))

result = [p for p in result if p != '']
