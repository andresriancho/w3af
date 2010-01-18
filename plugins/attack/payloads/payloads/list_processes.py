#REQUIRE_LINUX
import re

result = []

def parse_proc_name ( status_file ):
    name = re.search('.*', status_file)
    if name:
        name.group(0)
    else:
        return ''

def parse_proc_state ( status_file ):
    state = re.search('(?<=State: )(.*)', status_file)
    if state:
        state.group(1)
    else:
        return ''

result.append('PID      CMD')
max_pid = read('/proc/sys/kernel/pid_max')[:-1]

#for i in xrange(1, int(max_pid)):
for i in xrange(1, 5):
    try:
        file = read('/proc/'+str(i)+'/status')
        result.append(str(i)+'      '+str(parse_proc_name(file))+'      '+str(parse_proc_state(file)))
    except IOError:
        pass

result = [p for p in result if p != '']
#TODO: cmdline!
