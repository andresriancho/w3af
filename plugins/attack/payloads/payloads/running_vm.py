import re
from plugins.attack.payloads.base_payload import base_payload

class running_vm(base_payload):
    '''
    This payload check if the Server is running through a VM
    '''
    def api_read(self):
        result = []
        files = []

        candidates = []
        candidates.append('0000:00:0f.0')
        candidates.append('0000:00:00.0')
        candidates.append('0000:00:07.0')
        candidates.append('0000:00:07.3')
        candidates.append('0000:00:07.7')
        candidates.append('0000:00:10.0')
        candidates.append('0000:00:11.0')
        candidates.append('0000:00:15.0')
        candidates.append('0000:00:15.1')
        candidates.append('0000:00:16.0')
        candidates.append('0000:00:16.1')
        candidates.append('0000:00:17.0')
        candidates.append('0000:00:18.0')
        candidates.append('0000:02:00.0')
        candidates.append('0000:02:03.0')

        pci_list = []
        pci_list.append('15AD')
        pci_list.append('1233')
        pci_list.append('1af4:1100')
        pci_list.append('80ee:beef')
        pci_list.append('80ee:cafe')


        def parse_pci_id( uevent ):
            processor = re.search('(?<=PCI_ID=)(.*)', uevent)
            if processor:
                return processor.group(1)
            else:
                return ''

        def parse_subsys_id( uevent ):
            processor = re.search('(?<=PCI_SUBSYS_ID=)(.*)', uevent)
            if processor:
                return processor.group(1)
            else:
                return ''

        condition = 'Is not running through a VM'
        for candidate in candidates:
            file = self.shell.read('/sys/bus/pci/devices/'+candidate)
            pci_id = parse_pci_id(file)
            pci_subsys_id = parse_subsys_id(file)
            for pci_item in pci_list:
                if pci_item in pci_id or pci_item in pci_subsys_id:
                    condition = 'Its running through a VM!'

        files.append('/var/log/dmesg')
        files.append('/proc/interrupts')
        files.append('/proc/cpuinfo')
        files.append('/proc/iomem')
        files.append('/proc/meminfo')
        for file in files:
            file_content = self.shell.read(file)
            if 'vmware' in file_content.lower() or 'qemu' in file_content.lower() \
                or 'virtualbox' in file_content.lower() or 'bochs' in file_content.lower():
                condition = 'Is running through a VM !'
        
        kernel_modules = self.exec_payload('list_kernel_modules')
        if 'vmware' in kernel_modules.lower() or 'qemu' in kernel_modules.lower() \
            or 'virtualbox' in kernel_modules.lower() or 'bochs' in kernel_modules.lower():
            condition = 'Is running through a VM !'
        
        result.append(condition)

        result = [p for p in result if p != '']
        
        return result
    
    def run_read(self):
        result = self.api_read()
        return result
