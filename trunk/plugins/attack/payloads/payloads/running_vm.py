import re
from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class running_vm(base_payload):
    '''
    This payload check if the Server is running through a VM
    '''
    def api_read(self, parameters):
        result = {}
        result['running_vm'] = False
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


        for candidate in candidates:
            file = self.shell.read('/sys/bus/pci/devices/'+candidate+'/uevent')
            pci_id = parse_pci_id(file)
            pci_subsys_id = parse_subsys_id(file)
            for pci_item in pci_list:
                if pci_item in pci_id or pci_item in pci_subsys_id:
                    result['running_vm'] = True

        files.append('/var/log/dmesg')
        files.append('/proc/interrupts')
        files.append('/proc/cpuinfo')
        files.append('/proc/iomem')
        files.append('/proc/meminfo')
        for file in files:
            file_content = self.shell.read(file)
            if 'vmware' in file_content.lower() or 'qemu' in file_content.lower() \
                or 'virtualbox' in file_content.lower() or 'bochs' in file_content.lower():
                result['running_vm'] = True
        
        kernel_modules = self.exec_payload('list_kernel_modules').keys()
        if 'vmware' in str(kernel_modules).lower() or 'qemu' in str(kernel_modules).lower() \
            or 'virtualbox' in str(kernel_modules).lower() or 'bochs' in str(kernel_modules).lower():
            result['running_vm'] = True
        
        return result
    
    def api_win_read(self):
        result = []
        iis6log_content = self.shell.read('/windows/iis6.log')
        #if 'VMWare'
    
    def run_read(self, parameters):
        api_result = self.api_read( parameters )

        rows = []
        rows.append( ['Running inside Virtual Machine',] ) 
        rows.append( [] )
        
        if api_result['running_vm']:
            rows.append(['The remote host is a virtual machine.',])
        else:
            rows.append(['The remote host is NOT a virtual machine.',])
            
        result_table = table( rows )
        result_table.draw( 80 )                    
        return
