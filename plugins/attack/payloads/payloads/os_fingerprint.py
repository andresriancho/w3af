#REQUIRE_LINUX
import os

result = []

if open('/proc/sys/kernel/ostype').read()[:-1] == 'Linux':
    result.append('Linux')
else:
    result.append('Windows')
    
    
