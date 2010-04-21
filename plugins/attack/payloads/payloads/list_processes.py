import re
from core.controllers.threads.threadManager import threadManagerObj as tm
from plugins.attack.payloads.base_payload import base_payload
import core.controllers.outputManager as om
import core.data.kb.knowledgeBase as kb

class list_processes(base_payload ):
    '''
    This payload shows current proccesses on the system.
    '''
    def parse_proc_name( self, status_file ):
        name = re.search('(?<=Name:\t)(.*)', status_file)
        if name:
            return name.group(1)
        else:
            return ''

    def parse_proc_state( self, status_file ):
        state = re.search('(?<=State:\t)(.*)', status_file)
        if state:
            return state.group(1)
        else:
            return ''
    
    def _thread_read( self, i):
    #   "progress bar"  
        self.k -= 1
        if self.k == 0:
            om.out.console('.', newLine=False)
            self.k=400
        #   end "progress bar"

        status_file = self.shell.read('/proc/'+str(i)+'/status')
        cmd = ''
        if status_file:
            name = self.parse_proc_name(status_file)
            state = self.parse_proc_state(status_file)
            cmd = self.shell.read('/proc/'+str(i)+'/cmdline')
            if not cmd:
                cmd = '[kernel process]'
            cmd = cmd.replace('\x00',' ')
            self.result[i] = {'name':name, 'state':state, 'cmd':cmd}
            om.out.console('+', newLine=False)
            #TODO: VER APPEND KNOWDLEDGE BASE
        #if kb.kb:
            #kb.kb.append(str(i), [str(i), name, state, cmd])

    def api_read(self):
        self.result = {}
        self.k = 400
        max_pid = self.shell.read('/proc/sys/kernel/pid_max')[:-1]
        #max_pid = 400 Uncomment to debug
        for pid in xrange(1, int(max_pid)):
            targs = (pid, )
            tm.startFunction( target=self._thread_read, args=targs, ownerObj=self )
        tm.join( self )
        return self.result
    
    def run_read(self):
        hashmap= self.api_read()
        hashmap_keys = sorted(hashmap)
        print hashmap
        result = []
        
        if hashmap:
            result.append('PID'.ljust(7)+'NAME'.ljust(20)+'STATUS'.ljust(20)+'CMD'.ljust(30))
            for k in hashmap_keys:
                v = hashmap[k]
                msg = str(k).ljust(7) + v['name'].ljust(20)
                msg += v['state'].ljust(20) + v['cmd'].ljust(30)
                result.append( msg )
            om.out.console('')
        if result == [ ]:
            result.append('Cant list proccesses.')
        return result
