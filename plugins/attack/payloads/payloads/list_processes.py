import re
from plugins.attack.payloads.base_payload import base_payload
import core.controllers.outputManager as om
import core.data.kb.knowledgeBase as kb

class list_processes(base_payload):
    '''
    This payload shows current proccesses on the system.
    '''
    def api_read(self):
        result = []
        table = []
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
                om.out.console('.', newLine=False)
                k=400
            #   end "progress bar"

            status_file = self.shell.read('/proc/'+str(i)+'/status')
            name = parse_proc_name(status_file)
            state = parse_proc_state(status_file)

            if status_file:
                cmd = self.shell.read('/proc/'+str(i)+'/cmdline')
                if kb.kb:
                    kb.kb.append(name, [i, name, state, cmd])
                if not cmd:
                    cmd = '[kernel process]'
                cmd = cmd.replace('\x00',' ')
                result.append([i, name, state, cmd])
                om.out.console('+', newLine=False)

        om.out.console('')
        result = [p for p in result if p != '']
        return result
    
    def run_read(self):
        result = self.api_read()
        for line in result:
            msg = str(line[0]).ljust(7) + line[1].ljust(20)
            msg += line[2].ljust(20) + line[3].ljust(30)
            result.append( msg )
        om.out.console('')
        if result == [ ]:
            result.append('Cant list proccesses.')
        return result
