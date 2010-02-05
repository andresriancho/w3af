#REQUIRE_LINUX
#This payload check if the Server is running through a VM
import re

result = []

def parse_pci_id( uevent ):
    processor = re.search('(?<=PCI_ID=)(.*)', uevent)
    if processor:
        return processor.group(1)
    else:
        return ''

def find_devices(path):
    for i in range(10):
        for j in range(10):
            for abc in ['a', 'b', 'c', 'd', 'e', 'f']:
                        if read(path+'0000:00:'+str(i)+str(j)+'.'+str(j)+'/uevent'):
                            result.append(path+'0000:00:'+str(i)+str(j)+'.'+str(j)+'/uevent')
                            
                        if read(path+'0000:00:'+str(i)+abc+'.'+str(j)+'/uevent'):
                            result.append(path+'0000:00:'+str(i)+abc+'.'+str(j)+'/uevent')
                        
                        if read(path+'0000:00:'+abc+str(i)+'.'+str(j)+'/uevent'):
                            result.append(path+'0000:00:'+abc+str(i)+'.'+str(j)+'/uevent')


find_devices('/sys/bus/pci/devices/')
result = [p for p in result if p != '']
