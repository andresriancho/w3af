import re

result = []

def parse_proc_name ( status_file ):
    name = re.search('(?<=Name:\t)(.*)', status_file)
    return name.group(1)
    
#NO OLVIARME: EN ENVIRON ESTAN TODAS LAS VARIABLES E ENTORNO DE CADA PROCESO!! SOLO CON PERMISO DE ROOT.

max_pid = open('/proc/sys/kernel/pid_max').read()[:-1]
result.append('PID      CMD')
for i in xrange(1, int(max_pid) ):
        result.append(str(i)+'      '+parse_proc_name(open('/proc/'+str(i)+'/status').read()))
result = [p for p in result if p != '']
