import re
from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class running_vm(Payload):
    """
    This payload check if the Server is running through a VM
    """
    def fname_generator(self):
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
        candidates.append('0000:00:02.0')

        for candidate in candidates:
            yield '/sys/bus/pci/devices/' + candidate + '/uevent'

        files = []
        files.append('/var/log/dmesg')
        files.append('/proc/interrupts')
        files.append('/proc/cpuinfo')
        files.append('/proc/iomem')
        files.append('/proc/meminfo')

        for file_ in files:
            yield file_

    def api_read(self):
        result = {}
        result['running_vm'] = False

        pci_list = []
        pci_list.append('15AD')
        pci_list.append('1233')
        pci_list.append('1af4:1100')
        pci_list.append('80ee:beef')
        pci_list.append('80ee:cafe')

        def parse_pci_id(uevent):
            processor = re.search('(?<=PCI_ID=)(.*)', uevent)
            if processor:
                return processor.group(1).lower()
            else:
                return ''

        def parse_subsys_id(uevent):
            processor = re.search('(?<=PCI_SUBSYS_ID=)(.*)', uevent)
            if processor:
                return processor.group(1).lower()
            else:
                return ''

        for fname, content in self.read_multi(self.fname_generator()):
            pci_id = parse_pci_id(content)
            pci_subsys_id = parse_subsys_id(content)
            for pci_item in pci_list:
                if pci_item in pci_id or pci_item in pci_subsys_id:
                    result['running_vm'] = True
                    break

            content_lower = content.lower()
            for vm_engine in ('vmware', 'qemu', 'virtualbox', 'bochs'):
                if vm_engine in content_lower:
                    result['running_vm'] = True
                    break

        kernel_modules = self.exec_payload('list_kernel_modules').keys()
        str_kernel_modules = str(kernel_modules).lower()
        for vm_engine in ('vmware', 'qemu', 'virtualbox', 'bochs'):
            if vm_engine in str_kernel_modules:
                result['running_vm'] = True
                break

        return result

    def api_win_read(self):
        result = []
        iis6log_content = self.shell.read('/windows/iis6.log')
        #if 'VMWare'

    def run_read(self):
        api_result = self.api_read()

        rows = []
        rows.append(['Running inside Virtual Machine', ])
        rows.append([])

        if api_result['running_vm']:
            rows.append(['The remote host is a virtual machine.', ])
        else:
            rows.append(['The remote host is NOT a virtual machine.', ])

        result_table = table(rows)
        result_table.draw(80)
        return rows
