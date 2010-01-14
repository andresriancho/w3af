#REQUIRE_LINUX
import re

result = []

def parse_proc_name ( status_file ):
    name = re.search('(?<=Name:\t)(.*)', status_file)
    if name:
        name.group(1)
    else:
        return ''

def parse_proc_state ( status_file ):
    state = re.search('(?<=State:\t)(.*)', status_file)
    if state:
        state.group(1)
    else:
        return ''

result.append('PID      CMD')
max_pid = read('/proc/sys/kernel/pid_max')[:-1]

for i in xrange(1, int(max_pid)):
   print i
   result.append(str(i)+'      '+parse_proc_name(read('/proc/'+str(i)+'/status')))
result = [p for p in result if p != '']
#TODO: cmdline!
