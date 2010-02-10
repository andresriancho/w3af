import re
from plugins.attack.payloads.base_payload import base_payload

class list_processes(base_payload):
    '''
    '''
    def run_read(self):
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

        result.append('PID'.ljust(7)+'NAME'.ljust(20)+'STATUS'.ljust(20)+'CMD'.ljust(30))
        max_pid = self.shell.read('/proc/sys/kernel/pid_max')[:-1]

        k=400
        for i in xrange(1, int(max_pid)):

            #   "progress bar"    
            k -= 1
            if k == 0:
                console('.', newLine=False)
                k=400
            #   end "progress bar"

            status_file = self.shell.read('/proc/'+str(i)+'/status')

            if status_file:

                cmd = self.shell.read('/proc/'+str(i)+'/cmdline')
                if not cmd:
                    cmd = '[kernel process]'
                cmd = cmd.replace('\x00',' ')

                msg = str(i).ljust(7) + parse_proc_name(status_file).ljust(20)
                msg += parse_proc_state(status_file).ljust(20) + cmd.ljust(30)
                result.append( msg )
                console('+', newLine=False)

        console('')
        result = [p for p in result if p != '']
        return result
