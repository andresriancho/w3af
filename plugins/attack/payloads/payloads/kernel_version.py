import re
from plugins.attack.payloads.base_payload import base_payload

class kernel_version(base_payload):
    '''
    '''
    def run_read(self):
        result = []
        paths = []

        def parse_proc_version ( proc_version ):
               version = re.search('(?<=Linux version ).*?\)', proc_version)
               if version:
                   return version.group(0)
               else:
                   return ''


        def parse_sched_debug ( sched_debug ):
            version = re.search('(?<=Sched Debug Version: )(v\d\.\d\d, )(.*)', sched_debug)
            if version:
                return version.group(2)
            else:
                return ''

        paths.append(parse_proc_version(self.shell.read('/proc/version' )) )
        paths.append(self.shell.read('/proc/sys/kernel/osrelease')[:-1])
        paths.append(parse_sched_debug( self.shell.read('/proc/sched_debug') ) )

        longest=''
        for version in paths:
            if len(version) > len(longest):
                longest = version
        result.append(longest)
        return result
