#REQUIRE_LINUX
import re

result = []

def parse_proc_name ( status_file ):
    name = re.search('(?<=Name:\t)(.*)', status_file)
    if name:
        return name.group(1)
    else:
        return ''

def parse_proc_state ( status_file ):
    state = re.search('(?<=State:\t)(.*)', status_file)
    if state:
        return state.group(1)
    else:
        return ''

result.append('PID'.ljust(7)+'NAME'.ljust(15)+'CMD'.ljust(30)+'STATUS'.ljust(20))
max_pid = read('/proc/sys/kernel/pid_max')[:-1]

for i in xrange(1, int(max_pid)):
    try:
        file = read('/proc/'+str(i)+'/status')
        cmd = read('/proc/'+str(i)+'/cmdline')
        if file:
            result.append(str(i).ljust(7)+parse_proc_name(file).ljust(15)+cmd.ljust(30)+parse_proc_state(file).ljust(20))
    except IOError:
        pass

result = [p for p in result if p != '']

