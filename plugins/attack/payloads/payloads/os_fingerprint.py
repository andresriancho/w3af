#REQUIRE_LINUX
import os

result = []

#FIX THIS
if read('/proc/sys/kernel/ostype')[:-1] == 'Linux':
    result.append('Linux')
else:
    result.append('Windows')
