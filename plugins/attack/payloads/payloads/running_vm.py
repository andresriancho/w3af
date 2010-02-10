import re
from plugins.attack.payloads.base_payload import base_payload

class running_vm(base_payload):
    '''
    This payload check if the Server is running through a VM
    '''
    def run_read(self):
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
        pci_list.append('15AD:0405')
        pci_list.append('15AD:1976')
        pci_list.append('15AD:07a0')
        pci_list.append('15AD:0790')
        pci_list.append('15AD:0770')
        pci_list.append('15AD:0740')

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

        condition = False
        for candidate in candidates:
            file = read('/sys/bus/pci/devices/'+candidate)
            pci_id = parse_pci_id(file)
            pci_subsys_id = parse_subsys_id(file)
            if pci_id in pci_list or pci_subsys_id in pci_list:
                condition = True

        files.append('/var/log/dmesg')
        files.append('/proc/interrupts')
        files.append('/proc/cpuinfo')
        files.append('/proc/iomem')
        files.append('/proc/meminfo')
        for file in files:
            if 'VMware' in read(file):
                condition = True
        if 'VMware' in self.exec_payload('list_kernel_modules'):
            condition = True

        result = [p for p in result if p != '']
        return result
