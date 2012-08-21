import re

import core.controllers.outputManager as om

from core.controllers.threads.threadManager import thread_manager
from core.ui.consoleUi.tables import table

from plugins.attack.payloads.base_payload import base_payload


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
    
    def _thread_read(self, pid):
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
            self.result[ str(pid) ] = {'name':name, 'state':state, 'cmd':cmd}
            om.out.console('+', newLine=False)
        
        #TODO: Check how to append to the KB
        #if kb.kb:
            #kb.kb.append(str(i), [str(i), name, state, cmd])

    def api_read(self, parameters):
        self.result = {}
        self.k = 400
        
        max_pid = self.shell.read('/proc/sys/kernel/pid_max')[:-1]
        
        if len(parameters) == 1:
            max_pid_user = parameters[0]
            try:
                max_pid = int(max_pid_user)
            except:
                om.out.console('Invalid max_pid: %s' % max_pid_user)
        
        pid_iter = xrange(1, int(max_pid))
        thread_manager.threadpool.map(self._thread_read, pid_iter)
        
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
        
    def run_read(self, parameters):
        api_result = self.api_read( parameters )
        
        if not api_result:
            return 'Failed to list proccesses.'
        else:
            rows = []
            rows.append( ['PID', 'Name', 'Status', 'Cmd'] ) 
            rows.append( [] )
            
            pids = api_result.keys()
            pids.sort()
            
            for pid in pids:
                name = api_result[pid]['name']
                state = api_result[pid]['state']
                cmd = api_result[pid]['cmd']
                
                rows.append( [pid, name, state, cmd] )
                              
            result_table = table( rows )
            result_table.draw( 80 )                    
            return rows
