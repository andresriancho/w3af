from core.controllers.threads.threadManager import threadManagerObj as tm
from plugins.attack.payloads.base_payload import base_payload
import core.controllers.outputManager as om
from core.ui.consoleUi.tables import table

#    Rootkit information taken from:
#    Rootkit Hunter Shell Script by Michael Boelen


class rootkit_hunter(base_payload ):
    '''
    This payload checks for current rootkits, trojans, backdoors and local exploits installed on system.
    '''
    def _thread_read( self, file):
        #   "progress bar"  
        self.k -= 1
        if self.k == 0:
            om.out.console('.', newLine=False)
            self.k=400
        #   end "progress bar"
        
        content = self.shell.read(file)
        if content:
            self.result['backdoor_files'].append( file )
        
        return self.result
    
    def api_read(self, parameters):
        files = []
        self.result = {}
        self.result['bad_kernel_modules'] = []
        self.result['backdoor_files'] = []
        self.k = 400
        
        # AjaKit Rootkit
        files.append('/dev/tux/.addr')
        files.append('/dev/tux/.proc')
        files.append('/dev/tux/.file')
        files.append('/lib/.libgh-gh/cleaner')
        files.append('/lib/.libgh-gh/Patch/patch')
        files.append('/lib/.libgh-gh/sb0k')
        files.append('/dev/tux')
        files.append('/lib/.libgh-gh')

        # aPa Kit Rootkit
        files.append('/usr/share/.aPa')

        # Apache Worm
        files.append('/bin/.log')

        # Ambient (ark) Rootkit
        files.append('/usr/lib/.ark?')
        files.append('/dev/ptyxx/.log')
        files.append('/dev/ptyxx/.file')
        files.append('/dev/ptyxx/.proc')
        files.append('/dev/ptyxx/.addr')
        files.append('/dev/ptyxx')
        


        # Balaur Rootkit 2.0 (LRK5 based)
        files.append('/usr/lib/liblog.o')
        files.append('/usr/lib/.kinetic')
        files.append('/usr/lib/.egcs')
        files.append('/usr/lib/.wormie')
        


        # Beastkit Rootkit
        files.append('/usr/sbin/arobia')
        files.append('/usr/sbin/idrun')
        files.append('/usr/lib/elm/arobia/elm')
        files.append('/usr/lib/elm/arobia/elm/hk')
        files.append('/usr/lib/elm/arobia/elm/hk.pub')
        files.append('/usr/lib/elm/arobia/elm/sc')
        files.append('/usr/lib/elm/arobia/elm/sd.pp')
        files.append('/usr/lib/elm/arobia/elm/sdco')
        files.append('/usr/lib/elm/arobia/elm/srsd')
        files.append('/lib/ldd.so/bktools')
        


        # beX2 Rootkit
        files.append('/usr/info/termcap.info-5.gz')
        files.append('/usr/bin/sshd2')
        files.append('/usr/include/bex')
        
        # BOBkit Rootkit
        files.append('/usr/sbin/ntpsx')
        files.append('/usr/sbin/.../bkit-ava')
        files.append('/usr/sbin/.../bkit-d')
        files.append('/usr/sbin/.../bkit-shd')
        files.append('/usr/sbin/.../bkit-f')
        files.append('/usr/include/.../proc.h')
        files.append('/usr/include/.../.bash_history')
        files.append('/usr/include/.../bkit-get')
        files.append('/usr/include/.../bkit-dl')
        files.append('/usr/include/.../bkit-screen')
        files.append('/usr/include/.../bkit-sleep')
        files.append('/usr/lib/.../bkit-adore.o')
        files.append('/usr/lib/.../ls')
        files.append('/usr/lib/.../netstat')
        files.append('/usr/lib/.../lsof')
        files.append('/usr/lib/.../bkit-ssh/bkit-shdcfg')
        files.append('/usr/lib/.../bkit-ssh/bkit-shhk')
        files.append('/usr/lib/.../bkit-ssh/bkit-pw')
        files.append('/usr/lib/.../bkit-ssh/bkit-shrs')
        files.append('/usr/lib/.../bkit-ssh/bkit-mots')
        files.append('/usr/lib/.../uconf.inv')
        files.append('/usr/lib/.../psr')
        files.append('/usr/lib/.../find')
        files.append('/usr/lib/.../pstree')
        files.append('/usr/lib/.../slocate')
        files.append('/usr/lib/.../du')
        files.append('/usr/lib/.../top')
        files.append('/usr/sbin/...')
        files.append('/usr/include/...')
        files.append('/usr/include/.../.tmp')
        files.append('/usr/lib/...')
        files.append('/usr/lib/.../.ssh')
        files.append('/usr/lib/.../bkit-ssh')
        files.append('/usr/lib/.bkit-')
        files.append('/tmp/.bkp')
        

        # Boxer-0.99b3

        # cb Rootkit (w00tkit by ZeeN) ')
        # The '%' character represents a space.')
        # xC.o = Adore LKM')
        files.append('/dev/srd0')
        files.append('/lib/libproc.so.2.0.6')
        files.append('/dev/mounnt')
        files.append('/etc/rc.d/init.d/init')
        files.append('/usr/bin/.zeen/..%/cl')
        files.append('/usr/bin/.zeen/..%/.x.tgz')
        files.append('/usr/bin/.zeen/..%/statdx')
        files.append('/usr/bin/.zeen/..%/wted')
        files.append('/usr/bin/.zeen/..%/write')
        files.append('/usr/bin/.zeen/..%/scan')
        files.append('/usr/bin/.zeen/..%/sc')
        files.append('/usr/bin/.zeen/..%/sl2')
        files.append('/usr/bin/.zeen/..%/wroot')
        files.append('/usr/bin/.zeen/..%/wscan')
        files.append('/usr/bin/.zeen/..%/wu')
        files.append('/usr/bin/.zeen/..%/v')
        files.append('/usr/bin/.zeen/..%/read')
        files.append('/usr/lib/sshrc')
        files.append('/usr/lib/ssh_host_key')
        files.append('/usr/lib/ssh_host_key.pub')
        files.append('/usr/lib/ssh_random_seed')
        files.append('/usr/lib/sshd_config')
        files.append('/usr/lib/shosts.equiv')
        files.append('/usr/lib/ssh_known_hosts')
        files.append('/u/zappa/.ssh/pid')
        files.append('/usr/bin/.system/..%/tcp.log')
        files.append('/usr/bin/.zeen/..%/curatare/attrib')
        files.append('/usr/bin/.zeen/..%/curatare/chattr')
        files.append('/usr/bin/.zeen/..%/curatare/ps')
        files.append('/usr/bin/.zeen/..%/curatare/pstree')
        files.append('/usr/bin/.system/..%/.x/xC.o')
        files.append('/usr/bin/.zeen')
        files.append('/usr/bin/.zeen/..%/curatare')
        files.append('/usr/bin/.zeen/..%/scan')
        files.append('/usr/bin/.system/..%')
        


        # CiNIK Worm (Slapper.B variant)
        files.append('/tmp/.cinik')
        files.append('/tmp/.font-unix/.cinik')
        


        # CX Rootkit
        files.append('/usr/lib/ldlibso')
        files.append('/usr/lib/configlibso')
        files.append('/usr/lib/shklibso')
        files.append('/usr/lib/randomlibso')
        files.append('/usr/lib/ldlibstrings.so')
        files.append('/usr/lib/ldlibdu.so')
        files.append('/usr/lib/ldlibns.so')
        files.append('/usr/include/db')
        files.append('/usr/include/cxk')
        


        # Danny-Boy's Abuse Kit
        files.append('/dev/mdev')
        files.append('/usr/lib/libX.a')
        
        


        # Devil Rootkit
        files.append('/var/lib/games/.src')
        files.append('/dev/dsx')
        files.append('/dev/caca')
        files.append('/dev/pro')
        files.append('/bin/bye')
        files.append('/bin/homedir')
        files.append('/usr/bin/xfss')
        files.append('/usr/sbin/tzava')
        files.append('/usr/doc/tar/.../.dracusor/stuff/holber')
        files.append('/usr/doc/tar/.../.dracusor/stuff/sense')
        files.append('/usr/doc/tar/.../.dracusor/stuff/clear')
        files.append('/usr/doc/tar/.../.dracusor/stuff/tzava')
        files.append('/usr/doc/tar/.../.dracusor/stuff/citeste')
        files.append('/usr/doc/tar/.../.dracusor/stuff/killrk')
        files.append('/usr/doc/tar/.../.dracusor/stuff/searchlog')
        files.append('/usr/doc/tar/.../.dracusor/stuff/gaoaza')
        files.append('/usr/doc/tar/.../.dracusor/stuff/cleaner')
        files.append('/usr/doc/tar/.../.dracusor/stuff/shk')
        files.append('/usr/doc/tar/.../.dracusor/stuff/srs')
        files.append('/usr/doc/tar/.../.dracusor/utile.tgz')
        files.append('/usr/doc/tar/.../.dracusor/webpage')
        files.append('/usr/doc/tar/.../.dracusor/getpsy')
        files.append('/usr/doc/tar/.../.dracusor/getbnc')
        files.append('/usr/doc/tar/.../.dracusor/getemech')
        files.append('/usr/doc/tar/.../.dracusor/localroot.sh')
        files.append('/usr/doc/tar/.../.dracusor/stuff/old/sense')
        files.append('/usr/doc/tar/.../.dracusor')
        


        # Dica-Kit (T0rn variant) Rootkit
        files.append('/lib/.sso')
        files.append('/lib/.so')
        files.append('/var/run/...dica/clean')
        files.append('/var/run/...dica/dxr')
        files.append('/var/run/...dica/read')
        files.append('/var/run/...dica/write')
        files.append('/var/run/...dica/lf')
        files.append('/var/run/...dica/xl')
        files.append('/var/run/...dica/xdr')
        files.append('/var/run/...dica/psg')
        files.append('/var/run/...dica/secure')
        files.append('/var/run/...dica/rdx')
        files.append('/var/run/...dica/va')
        files.append('/var/run/...dica/cl.sh')
        files.append('/var/run/...dica/last.log')
        files.append('/usr/bin/.etc')
        files.append('/etc/sshd_config')
        files.append('/etc/ssh_host_key')
        files.append('/etc/ssh_random_seed')
        files.append('/var/run/...dica')
        files.append('/var/run/...dica/mh')
        files.append('/var/run/...dica/scan')
        


        # Dreams Rootkit
        files.append('/dev/ttyoa')
        files.append('/dev/ttyof')
        files.append('/dev/ttyop')
        files.append('/usr/bin/sense')
        files.append('/usr/bin/sl2')
        files.append('/usr/bin/logclear')
        files.append('/usr/bin/(swapd)')
        files.append('/usr/bin/initrd')
        files.append('/usr/bin/crontabs')
        files.append('/usr/bin/snfs')
        files.append('/usr/lib/libsss')
        files.append('/usr/lib/libsnf.log')
        files.append('/usr/lib/libshtift/top')
        files.append('/usr/lib/libshtift/ps')
        files.append('/usr/lib/libshtift/netstat')
        files.append('/usr/lib/libshtift/ls')
        files.append('/usr/lib/libshtift/ifconfig')
        files.append('/usr/include/linseed.h')
        files.append('/usr/include/linpid.h')
        files.append('/usr/include/linkey.h')
        files.append('/usr/include/linconf.h')
        files.append('/usr/include/iceseed.h')
        files.append('/usr/include/icepid.h')
        files.append('/usr/include/icekey.h')
        files.append('/usr/include/iceconf.h" ')
        files.append('/dev/ida/.hpd')
        files.append('/usr/lib/libshtift')
        


        # Duarawkz Rootkit
        files.append('/usr/bin/duarawkz/loginpass')
        files.append('/usr/bin/duarawkz')
        


        # ENYE LKM v1.1, v1.2')
        # Installer default.
        files.append('/etc/.enyelkmHIDE^IT.ko')
        files.append('/etc/.enyelkmOCULTAR.ko')
        
        


        # Flea Linux Rootkit
        files.append('/etc/ld.so.hash')
        files.append('/lib/security/.config/ssh/sshd_config')
        files.append('/lib/security/.config/ssh/ssh_host_key')
        files.append('/lib/security/.config/ssh/ssh_host_key.pub')
        files.append('/lib/security/.config/ssh/ssh_random_seed')
        files.append('/usr/bin/ssh2d')
        files.append('/usr/lib/ldlibns.so')
        files.append('/usr/lib/ldlibps.so')
        files.append('/usr/lib/ldlibpst.so')
        files.append('/usr/lib/ldlibdu.so')
        files.append('/usr/lib/ldlibct.so')
        files.append('/lib/security/.config/ssh')
        files.append('/dev/..0')
        files.append('/dev/..0/backup')
        


        # FreeBSD Rootkit (FBRK) catering to versions and compile-time defaults used by: 
        # 1.0 (1997, Method), 1.2 (1997, Method), "ImperialS-FBRK 1.0" (2001, Nyo)
        files.append('/dev/ptyp')
        files.append('/dev/ptyq')
        files.append('/dev/ptyr')
        files.append('/dev/ptys')
        files.append('/dev/ptyt')
        files.append('/dev/fd/.88/freshb-bsd')
        files.append('/dev/fd/.88/fresht')
        files.append('/dev/fd/.88/zxsniff')
        files.append('/dev/fd/.88/zxsniff.log')
        files.append('/dev/fd/.99/.ttyf00')
        files.append('/dev/fd/.99/.ttyp00')
        files.append('/dev/fd/.99/.ttyq00')
        files.append('/dev/fd/.99/.ttys00')
        files.append('/dev/fd/.99/.pwsx00')
        files.append('/etc/.acid')
        files.append('/usr/lib/.fx/sched_host.2')
        files.append('/usr/lib/.fx/random_d.2')
        files.append('/usr/lib/.fx/set_pid.2')
        files.append('/usr/lib/.fx/setrgrp.2')
        files.append('/usr/lib/.fx/TOHIDE')
        files.append('/usr/lib/.fx/cons.saver')
        files.append('/usr/lib/.fx/adore/ava/ava')
        files.append('/usr/lib/.fx/adore/adore/adore.ko')
        files.append('/bin/sysback')
        files.append('/usr/local/bin/sysback')
        files.append('/dev/fd/.88')
        files.append('/dev/fd/.99')
        files.append('/usr/lib/.fx')
        files.append('/usr/lib/.fx/adore')
        


        # Fu Rootkit
        files.append('/sbin/xc')
        files.append('/usr/include/ivtype.h')
        files.append('/bin/.lib')
        
        


        # Fuckit Rootkit
        files.append('/lib/libproc.so.2.0.7')
        files.append('/dev/proc/.bash_profile')
        files.append('/dev/proc/.bashrc')
        files.append('/dev/proc/.cshrc')
        files.append('/dev/proc/fuckit/hax0r')
        files.append('/dev/proc/fuckit/hax0rshell')
        files.append('/dev/proc/fuckit/config/lports')
        files.append('/dev/proc/fuckit/config/rports')
        files.append('/dev/proc/fuckit/config/rkconf')
        files.append('/dev/proc/fuckit/config/password')
        files.append('/dev/proc/fuckit/config/progs')
        files.append('/dev/proc/fuckit/system-bins/init')
        files.append('/usr/lib/libcps.a')
        files.append('/usr/lib/libtty.a')
        files.append('/dev/proc')
        files.append('/dev/proc/fuckit')
        files.append('/dev/proc/fuckit/system-bins')
        files.append('/dev/proc/toolz')
        


        # GasKit Rootkit
        files.append('/dev/dev/gaskit/sshd/sshdd')
        files.append('/dev/dev')
        files.append('/dev/dev/gaskit')
        files.append('/dev/dev/gaskit/sshd')
        
        # HjC Kit Rootkit
        
        files.append('/dev/.hijackerz')
        

        # ignoKit Rootkit
        files.append('/lib/defs/p')
        files.append('/lib/defs/q')
        files.append('/lib/defs/r')
        files.append('/lib/defs/s')
        files.append('/lib/defs/t')
        files.append('/usr/lib/defs/p')
        files.append('/usr/lib/defs/q')
        files.append('/usr/lib/defs/r')
        files.append('/usr/lib/defs/s')
        files.append('/usr/lib/defs/t')
        files.append('/usr/lib/.libigno/pkunsec')
        files.append('/usr/lib/.libigno/.igno/psybnc/psybnc')
        files.append('/usr/lib/.libigno')
        files.append('/usr/lib/.libigno/.igno')
        
        # iLLogiC Rootkit (SunOS Rootkit variant)')
        files.append('/dev/kmod')
        files.append('/dev/dos')
        files.append('/usr/lib/crth.o')
        files.append('/usr/lib/crtz.o')
        files.append('/etc/ld.so.hash')
        files.append('/usr/bin/sia')
        files.append('/usr/bin/ssh2d')
        files.append('/lib/security/.config/sn')
        files.append('/lib/security/.config/iver')
        files.append('/lib/security/.config/uconf.inv')
        files.append('/lib/security/.config/ssh/ssh_host_key')
        files.append('/lib/security/.config/ssh/ssh_host_key.pub')
        files.append('/lib/security/.config/ssh/sshport')
        files.append('/lib/security/.config/ssh/ssh_random_seed')
        files.append('/lib/security/.config/ava')
        files.append('/lib/security/.config/cleaner')
        files.append('/lib/security/.config/lpsched')
        files.append('/lib/security/.config/sz')
        files.append('/lib/security/.config/rcp')
        files.append('/lib/security/.config/patcher')
        files.append('/lib/security/.config/pg')
        files.append('/lib/security/.config/crypt')
        files.append('/lib/security/.config/utime')
        files.append('/lib/security/.config/wget')
        files.append('/lib/security/.config/instmod')
        files.append('/lib/security/.config/bin/find')
        files.append('/lib/security/.config/bin/du')
        files.append('/lib/security/.config/bin/ls')
        files.append('/lib/security/.config/bin/psr')
        files.append('/lib/security/.config/bin/netstat')
        files.append('/lib/security/.config/bin/su')
        files.append('/lib/security/.config/bin/ping')
        files.append('/lib/security/.config/bin/passwd')
        files.append('/lib/security/.config')
        files.append('/lib/security/.config/ssh')
        files.append('/lib/security/.config/bin')
        files.append('/lib/security/.config/backup')
        files.append('/root/%%%/.dir')
        files.append('/root/%%%/.dir/mass-scan')
        files.append('/root/%%%/.dir/flood')
        

        # Irix Rootkit (for Irix 6.x)')
        
        files.append('/dev/pts/01')
        files.append('/dev/pts/01/backup')
        files.append('/dev/pts/01/etc')
        files.append('/dev/pts/01/tmp')
        
        # Kitko Rootkit')
        
        files.append('/usr/src/redhat/SRPMS/...')
        


        # Knark Rootkit')
        files.append('/proc/knark/pids')
        files.append('/proc/knark')
        


        # ld-linuxv.so (LD_PRELOAD shared library rootkit)')
        files.append('/lib/ld-linuxv.so.1')
        files.append('/var/opt/_so_cache')
        files.append('/var/opt/_so_cache/ld')
        files.append('/var/opt/_so_cache/lc')
        

        # Lion Worm')
        files.append('/bin/in.telnetd')
        files.append('/bin/mjy')
        files.append('/usr/man/man1/man1/lib/.lib/mjy')
        files.append('/usr/man/man1/man1/lib/.lib/in.telnetd')
        files.append('/usr/man/man1/man1/lib/.lib/.x')
        files.append('/dev/.lib/lib/scan/1i0n.sh')
        files.append('/dev/.lib/lib/scan/hack.sh')
        files.append('/dev/.lib/lib/scan/bind')
        files.append('/dev/.lib/lib/scan/randb')
        files.append('/dev/.lib/lib/scan/scan.sh')
        files.append('/dev/.lib/lib/scan/pscan')
        files.append('/dev/.lib/lib/scan/star.sh')
        files.append('/dev/.lib/lib/scan/bindx.sh')
        files.append('/dev/.lib/lib/scan/bindname.log')
        files.append('/dev/.lib/lib/1i0n.sh')
        files.append('/dev/.lib/lib/lib/netstat')
        files.append('/dev/.lib/lib/lib/dev/.1addr')
        files.append('/dev/.lib/lib/lib/dev/.1logz')
        files.append('/dev/.lib/lib/lib/dev/.1proc')
        files.append('/dev/.lib/lib/lib/dev/.1file')
        
        

        # LKH-1.1')

        # Lockit (a.k.a. LJK2) Rootkit')
        files.append('/usr/lib/libmen.oo/.LJK2/ssh_config')
        files.append('/usr/lib/libmen.oo/.LJK2/ssh_host_key')
        files.append('/usr/lib/libmen.oo/.LJK2/ssh_host_key.pub')
        files.append('/usr/lib/libmen.oo/.LJK2/ssh_random_seed*')
        files.append('/usr/lib/libmen.oo/.LJK2/sshd_config')
        files.append('/usr/lib/libmen.oo/.LJK2/backdoor/RK1bd')
        files.append('/usr/lib/libmen.oo/.LJK2/backup/du')
        files.append('/usr/lib/libmen.oo/.LJK2/backup/ifconfig')
        files.append('/usr/lib/libmen.oo/.LJK2/backup/inetd.conf')
        files.append('/usr/lib/libmen.oo/.LJK2/backup/locate')
        files.append('/usr/lib/libmen.oo/.LJK2/backup/login')
        files.append('/usr/lib/libmen.oo/.LJK2/backup/ls')
        files.append('/usr/lib/libmen.oo/.LJK2/backup/netstat')
        files.append('/usr/lib/libmen.oo/.LJK2/backup/ps')
        files.append('/usr/lib/libmen.oo/.LJK2/backup/pstree')
        files.append('/usr/lib/libmen.oo/.LJK2/backup/rc.sysinit')
        files.append('/usr/lib/libmen.oo/.LJK2/backup/syslogd')
        files.append('/usr/lib/libmen.oo/.LJK2/backup/tcpd')
        files.append('/usr/lib/libmen.oo/.LJK2/backup/top')
        files.append('/usr/lib/libmen.oo/.LJK2/clean/RK1sauber')
        files.append('/usr/lib/libmen.oo/.LJK2/clean/RK1wted')
        files.append('/usr/lib/libmen.oo/.LJK2/hack/RK1parse')
        files.append('/usr/lib/libmen.oo/.LJK2/hack/RK1sniff')
        files.append('/usr/lib/libmen.oo/.LJK2/hide/.RK1addr')
        files.append('/usr/lib/libmen.oo/.LJK2/hide/.RK1dir')
        files.append('/usr/lib/libmen.oo/.LJK2/hide/.RK1log')
        files.append('/usr/lib/libmen.oo/.LJK2/hide/.RK1proc')
        files.append('/usr/lib/libmen.oo/.LJK2/hide/RK1phidemod.c')
        files.append('/usr/lib/libmen.oo/.LJK2/modules/README.modules')
        files.append('/usr/lib/libmen.oo/.LJK2/modules/RK1hidem.c')
        files.append('/usr/lib/libmen.oo/.LJK2/modules/RK1phide')
        files.append('/usr/lib/libmen.oo/.LJK2/sshconfig/RK1ssh')
        files.append('/usr/lib/libmen.oo/.LJK2')
        


        # MRK (MiCrobul?) RootKit (based on Devil RootKit, also see Xzibit)')
        files.append('/dev/ida/.inet/pid')
        files.append('/dev/ida/.inet/ssh_host_key')
        files.append('/dev/ida/.inet/ssh_random_seed')
        files.append('/dev/ida/.inet/tcp.log')
        files.append('/dev/ida/.inet')
        files.append('/var/spool/cron/.sh')
        


        # Mood-NT Rootkit')
        # Binary is by default called "mood-nt" but can be anywhere.')
        # Here we look for collaterals, from include/prefs.h defaults')
        # until sig-based dirscan() is added.')
        files.append('/sbin/init__mood-nt-_-_cthulhu')
        files.append('/_cthulhu/mood-nt.init')
        files.append('/_cthulhu/mood-nt.conf')
        files.append('/_cthulhu/mood-nt.sniff')
        files.append('/_cthulhu')
        


        # Ni0 Rootkit')
        files.append('/var/lock/subsys/...datafile.../...net...')
        files.append('/var/lock/subsys/...datafile.../...port...')
        files.append('/var/lock/subsys/...datafile.../...ps...')
        files.append('/var/lock/subsys/...datafile.../...file...')
        files.append('/tmp/waza')
        files.append('/var/lock/subsys/...datafile...')
        files.append('/usr/sbin/es')
        


        # Ohhara Rootkit')
        files.append('/var/lock/subsys/...datafile.../...datafile.../in.smbd.log')
        files.append('/var/lock/subsys/...datafile...')
        files.append('/var/lock/subsys/...datafile.../...datafile...')
        files.append('/var/lock/subsys/...datafile.../...datafile.../bin')
        files.append('/var/lock/subsys/...datafile.../...datafile.../usr/bin')
        files.append('/var/lock/subsys/...datafile.../...datafile.../usr/sbin')
        files.append('/var/lock/subsys/...datafile.../...datafile.../lib/security')
        
        # Optic Kit (Tux variant) Rootkit')
        
        files.append('/dev/tux')
        files.append('/usr/bin/xchk')
        files.append('/usr/bin/xsf')
        files.append('/usr/bin/ssh2d')
        


        # OSX Rootkit 0.2.1')
        files.append('/dev/.rk/nc')
        files.append('/dev/.rk/diepu')
        files.append('/dev/.rk/backd')
        files.append('/dev/.rk')
        files.append('/users/LDAP-daemon')
        files.append('/tmp/.work')
        files.append('/Library/StartupItems/opener')
        


        # Oz Rootkit')
        files.append('/dev/.oz/.nap/rkit/terror')
        files.append('/dev/.oz')
        


        # Phalanx Rootkit')
        files.append('/uNFuNF')
        files.append('/etc/host.ph1')
        files.append('/bin/host.ph1')
        files.append('/usr/share/.home.ph1/phalanx')
        files.append('/usr/share/.home.ph1/cb')
        files.append('/usr/share/.home.ph1/kebab')
        files.append('/usr/share/.home.ph1')
        files.append('/usr/share/.home.ph1/tty')
        


        # Phalanx2 Rootkit')
        files.append('/etc/khubd.p2/.p2rc')
        files.append('/etc/khubd.p2/.phalanx2')
        files.append('/etc/khubd.p2/.sniff')
        files.append('/etc/khubd.p2/sshgrab.py')
        files.append('/etc/lolzz.p2/.p2rc')
        files.append('/etc/lolzz.p2/.phalanx2')
        files.append('/etc/lolzz.p2/.sniff')
        files.append('/etc/lolzz.p2/sshgrab.py')
        files.append('/etc/cron.d/zupzzplaceholder')
        files.append('/usr/lib/zupzz.p2/.p-2.3d')
        files.append('/usr/lib/zupzz.p2/.p2rc')
        files.append('/etc/khubd.p2')
        files.append('/etc/lolzz.p2')
        files.append('/usr/lib/zupzz.p2')
        

        # Portacelo Rootkit')
        files.append('/var/lib/.../.ak')
        files.append('/var/lib/.../.hk')
        files.append('/var/lib/.../.rs')
        files.append('/var/lib/.../.p')
        files.append('/var/lib/.../getty')
        files.append('/var/lib/.../lkt.o')
        files.append('/var/lib/.../show')
        files.append('/var/lib/.../nlkt.o')
        files.append('/var/lib/.../ssshrc')
        files.append('/var/lib/.../sssh_equiv')
        files.append('/var/lib/.../sssh_known_hosts')
        files.append('/var/lib/.../sssh_pid ~/.sssh/known_hosts')
        
        


        # R3dstorm Toolkit')
        files.append('/var/log/tk02/see_all')
        files.append('/var/log/tk02/.scris')
        files.append('/bin/.../sshd/sbin/sshd1')
        files.append('/bin/.../hate/sk')
        files.append('/bin/.../see_all')
        files.append('/var/log/tk02')
        files.append('/var/log/tk02/old')
        files.append('/bin/...')
        


        # RH-Sharpe's Rootkit')
        files.append('/bin/lps')
        files.append('/usr/bin/lpstree')
        files.append('/usr/bin/ltop')
        files.append('/usr/bin/lkillall')
        files.append('/usr/bin/ldu')
        files.append('/usr/bin/lnetstat')
        files.append('/usr/bin/wp')
        files.append('/usr/bin/shad')
        files.append('/usr/bin/vadim')
        files.append('/usr/bin/slice')
        files.append('/usr/bin/cleaner')
        files.append('/usr/include/rpcsvc/du')
        
        


        # RSHA's Rootkit')
        files.append('/bin/kr4p')
        files.append('/usr/bin/n3tstat')
        files.append('/usr/bin/chsh2')
        files.append('/usr/bin/slice2')
        files.append('/usr/src/linux/arch/alpha/lib/.lib/.1proc')
        files.append('/etc/rc.d/arch/alpha/lib/.lib/.1addr')
        files.append('/etc/rc.d/rsha')
        files.append('/etc/rc.d/arch/alpha/lib/.lib')
        


        # Shutdown Rootkit')
        # The '%' character represents a space.')
        files.append('/usr/man/man5/..%/.dir/scannah/asus')
        files.append('/usr/man/man5/..%/.dir/see')
        files.append('/usr/man/man5/..%/.dir/nscd')
        files.append('/usr/man/man5/..%/.dir/alpd')
        files.append('/etc/rc.d/rc.local%')
        files.append('/usr/man/man5/..%/.dir')
        files.append('/usr/man/man5/..%/.dir/scannah')
        files.append('/etc/rc.d/rc0.d/..%/.dir')
        


        # Scalper (FreeBSD.Scalper.Worm) Worm')
        files.append('/tmp/.a')
        files.append('/tmp/.uua')
        
        


        # SHV4 Rootkit')
        files.append('/etc/ld.so.hash')
        files.append('/lib/libext-2.so.7')
        files.append('/lib/lidps1.so')
        files.append('/lib/libproc.a')
        files.append('/lib/libproc.so.2.0.6')
        files.append('/lib/ldd.so/tks')
        files.append('/lib/ldd.so/tkp')
        files.append('/lib/ldd.so/tksb')
        files.append('/lib/security/.config/sshd')
        files.append('/lib/security/.config/ssh/ssh_host_key')
        files.append('/lib/security/.config/ssh/ssh_host_key.pub')
        files.append('/lib/security/.config/ssh/ssh_random_seed')
        files.append('/usr/include/file.h')
        files.append('/usr/include/hosts.h')
        files.append('/usr/include/lidps1.so')
        files.append('/usr/include/log.h')
        files.append('/usr/include/proc.h')
        files.append('/usr/sbin/xntps')
        files.append('/dev/srd0')
        files.append('/lib/ldd.so')
        files.append('/lib/security/.config')
        files.append('/lib/security/.config/ssh')
        


        # SHV5 Rootkit')
        files.append('/etc/sh.conf')
        files.append('/lib/libproc.a')
        files.append('/lib/libproc.so.2.0.6')
        files.append('/lib/lidps1.so')
        files.append('/lib/libsh.so/bash')
        files.append('/usr/include/file.h')
        files.append('/usr/include/hosts.h')
        files.append('/usr/include/log.h')
        files.append('/usr/include/proc.h')
        files.append('/lib/libsh.so/shdcf2')
        files.append('/lib/libsh.so/shhk')
        files.append('/lib/libsh.so/shhk.pub')
        files.append('/lib/libsh.so/shrs')
        files.append('/usr/lib/libsh/.bashrc')
        files.append('/usr/lib/libsh/shsb')
        files.append('/usr/lib/libsh/hide')
        files.append('/usr/lib/libsh/.sniff/shsniff')
        files.append('/usr/lib/libsh/.sniff/shp')
        files.append('/dev/srd0')
        files.append('/lib/libsh.so')
        files.append('/usr/lib/libsh')
        files.append('/usr/lib/libsh/utilz')
        files.append('/usr/lib/libsh/.backup')
        


        # Sin Rootkit')
        files.append('/dev/.haos/haos1/.f/Denyed')
        files.append('/dev/ttyoa')
        files.append('/dev/ttyof')
        files.append('/dev/ttyop')
        files.append('/dev/ttyos')
        files.append('/usr/lib/.lib')
        files.append('/usr/lib/sn/.X')
        files.append('/usr/lib/sn/.sys')
        files.append('/usr/lib/ld/.X')
        files.append('/usr/man/man1/...')
        files.append('/usr/man/man1/.../.m')
        files.append('/usr/man/man1/.../.w')
        files.append('/usr/lib/sn')
        files.append('/usr/lib/man1/...')
        files.append('/dev/.haos')
        


        # Slapper Worm')
        files.append('/tmp/.bugtraq')
        files.append('/tmp/.uubugtraq')
        files.append('/tmp/.bugtraq.c')
        files.append('/tmp/httpd')
        files.append('/tmp/.unlock')
        files.append('/tmp/update')
        files.append('/tmp/.cinik')
        files.append('/tmp/.b')
        
        


        # Sneakin Rootkit')
        
        files.append('/tmp/.X11-unix/.../rk')
        


        # 'Spanish' Rootkit')
        files.append('/dev/ptyq')
        files.append('/bin/ad')
        files.append('/bin/ava')
        files.append('/bin/server')
        files.append('/usr/sbin/rescue')
        files.append('/usr/share/.../chrps')
        files.append('/usr/share/.../chrifconfig')
        files.append('/usr/share/.../netstat')
        files.append('/usr/share/.../linsniffer')
        files.append('/usr/share/.../charbd')
        files.append('/usr/share/.../charbd2')
        files.append('/usr/share/.../charbd3')
        files.append('/usr/share/.../charbd4')
        files.append('/usr/man/tmp/update.tgz')
        files.append('/var/lib/rpm/db.rpm')
        files.append('/var/cache/man/.cat')
        files.append('/var/spool/lpd/remote/.lpq')
        files.append('/usr/share/...')


        # Suckit Rootkit')
        files.append('/sbin/initsk12')
        files.append('/sbin/initxrk')
        files.append('/usr/bin/null')
        files.append('/usr/share/locale/sk/.sk12/sk')
        files.append('/etc/rc.d/rc0.d/S23kmdac')
        files.append('/etc/rc.d/rc1.d/S23kmdac')
        files.append('/etc/rc.d/rc2.d/S23kmdac')
        files.append('/etc/rc.d/rc3.d/S23kmdac')
        files.append('/etc/rc.d/rc4.d/S23kmdac')
        files.append('/etc/rc.d/rc5.d/S23kmdac')
        files.append('/etc/rc.d/rc6.d/S23kmdac')
        files.append('/dev/sdhu0/tehdrakg')
        files.append('/etc/.MG')
        files.append('/usr/share/locale/sk/.sk12')
        files.append('/usr/lib/perl5/site_perl/i386-linux/auto/TimeDate/.packlist')
        


        # SunOS / NSDAP Rootkit')
        files.append('/dev/pts/01/55su')
        files.append('/dev/pts/01/55ps')
        files.append('/dev/pts/01/55ping')
        files.append('/dev/pts/01/55login')
        files.append('/dev/pts/01/PATCHER_COMPLETED')
        files.append('/dev/prom/sn.l')
        files.append('/dev/prom/dos')
        files.append('/usr/lib/vold/nsdap/.kit')
        files.append('/usr/lib/vold/nsdap/defines')
        files.append('/usr/lib/vold/nsdap/patcher')
        files.append('/usr/lib/vold/nsdap/pg')
        files.append('/usr/lib/vold/nsdap/cleaner')
        files.append('/usr/lib/vold/nsdap/utime')
        files.append('/usr/lib/vold/nsdap/crypt')
        files.append('/usr/lib/vold/nsdap/findkit')
        files.append('/usr/lib/vold/nsdap/sn2')
        files.append('/usr/lib/vold/nsdap/sniffload')
        files.append('/usr/lib/vold/nsdap/runsniff')
        files.append('/usr/lib/lpset')
        files.append('/usr/lib/lpstart')
        files.append('/usr/bin/mc68000')
        files.append('/usr/bin/mc68010')
        files.append('/usr/bin/mc68020')
        files.append('/usr/ucb/bin/ps')
        files.append('/usr/bin/m68k')
        files.append('/usr/bin/sun2')
        files.append('/usr/bin/mc68030')
        files.append('/usr/bin/mc68040')
        files.append('/usr/bin/sun3')
        files.append('/usr/bin/sun3x')
        files.append('/usr/bin/lso')
        files.append('/usr/bin/u370')
        files.append('/dev/pts/01')
        files.append('/dev/prom')
        files.append('/usr/lib/vold/nsdap')
        files.append('/.pat')
        


        # SunOS Rootkit')
        files.append('/etc/ld.so.hash')
        files.append('/lib/libext-2.so.7')
        files.append('/usr/bin/ssh2d')
        files.append('/bin/xlogin')
        files.append('/usr/lib/crth.o')
        files.append('/usr/lib/crtz.o')
        files.append('/sbin/login')
        files.append('/lib/security/.config/sn')
        files.append('/lib/security/.config/lpsched')
        files.append('/dev/kmod')
        files.append('/dev/dos')
        
        


        # Superkit Rootkit (Suckit 1.3b-based)')
        files.append('/usr/man/.sman/sk/backsh')
        files.append('/usr/man/.sman/sk/izbtrag')
        files.append('/usr/man/.sman/sk/sksniff')
        files.append('/var/www/cgi-bin/cgiback.cgi')
        files.append('/usr/man/.sman/sk')
        


        # Telnet Backdoor')
        files.append('/usr/lib/.tbd')
        
        


        # TeLeKiT Rootkit')
        files.append('/usr/man/man3/.../TeLeKiT/bin/sniff')
        files.append('/usr/man/man3/.../TeLeKiT/bin/telnetd')
        files.append('/usr/man/man3/.../TeLeKiT/bin/teleulo')
        files.append('/usr/man/man3/.../cl')
        files.append('/dev/ptyr')
        files.append('/dev/ptyp')
        files.append('/dev/ptyq')
        files.append('/dev/hda06')
        files.append('/usr/info/libc1.so')
        files.append('/usr/man/man3/...')
        files.append('/usr/man/man3/.../lsniff')
        files.append('/usr/man/man3/.../TeLeKiT')
        


        # T0rn (and misc) Rootkit')
        files.append('/dev/.lib/lib/lib/t0rns')
        files.append('/dev/.lib/lib/lib/du')
        files.append('/dev/.lib/lib/lib/ls')
        files.append('/dev/.lib/lib/lib/t0rnsb')
        files.append('/dev/.lib/lib/lib/ps')
        files.append('/dev/.lib/lib/lib/t0rnp')
        files.append('/dev/.lib/lib/lib/find')
        files.append('/dev/.lib/lib/lib/ifconfig')
        files.append('/dev/.lib/lib/lib/pg')
        files.append('/dev/.lib/lib/lib/ssh.tgz')
        files.append('/dev/.lib/lib/lib/top')
        files.append('/dev/.lib/lib/lib/sz')
        files.append('/dev/.lib/lib/lib/login')
        files.append('/dev/.lib/lib/lib/in.fingerd')
        files.append('/dev/.lib/lib/lib/1i0n.sh')
        files.append('/dev/.lib/lib/lib/pstree')
        files.append('/dev/.lib/lib/lib/in.telnetd')
        files.append('/dev/.lib/lib/lib/mjy')
        files.append('/dev/.lib/lib/lib/sush')
        files.append('/dev/.lib/lib/lib/tfn')
        files.append('/dev/.lib/lib/lib/name')
        files.append('/dev/.lib/lib/lib/getip.sh')
        files.append('/usr/info/.torn/sh*')
        files.append('/usr/src/.puta/.1addr')
        files.append('/usr/src/.puta/.1file')
        files.append('/usr/src/.puta/.1proc')
        files.append('/usr/src/.puta/.1logz')
        files.append('/usr/info/.t0rn')
        files.append('/dev/.lib')
        files.append('/dev/.lib/lib')
        files.append('/dev/.lib/lib/lib')
        files.append('/dev/.lib/lib/lib/dev')
        files.append('/dev/.lib/lib/scan')
        files.append('/usr/src/.puta')
        files.append('/usr/man/man1/man1')
        files.append('/usr/man/man1/man1/lib')
        files.append('/usr/man/man1/man1/lib/.lib')
        files.append('/usr/man/man1/man1/lib/.lib/.backup')
        


        # trNkit Rootkit')
        files.append('/usr/lib/libbins.la')
        files.append('/usr/lib/libtcs.so')
        files.append('/dev/.ttpy/ulogin.sh')
        files.append('/dev/.ttpy/tcpshell.sh')
        files.append('/dev/.ttpy/bupdu')
        files.append('/dev/.ttpy/buloc')
        files.append('/dev/.ttpy/buloc1')
        files.append('/dev/.ttpy/buloc2')
        files.append('/dev/.ttpy/stat')
        files.append('/dev/.ttpy/backps')
        files.append('/dev/.ttpy/tree')
        files.append('/dev/.ttpy/topk')
        files.append('/dev/.ttpy/wold')
        files.append('/dev/.ttpy/whoold')
        files.append('/dev/.ttpy/backdoors')
        
        


        # Trojanit Kit Rootkit')
        files.append('/bin/.ls')
        files.append('/bin/.ps')
        files.append('/bin/.netstat')
        files.append('/usr/bin/.nop')
        files.append('/usr/bin/.who')
        
        


        # Tuxtendo (Tuxkit) Rootkit')
        files.append('/lib/libproc.so.2.0.7')
        files.append('/usr/bin/xchk')
        files.append('/usr/bin/xsf')
        files.append('/dev/tux/suidsh')
        files.append('/dev/tux/.addr')
        files.append('/dev/tux/.cron')
        files.append('/dev/tux/.file')
        files.append('/dev/tux/.log')
        files.append('/dev/tux/.proc')
        files.append('/dev/tux/.iface')
        files.append('/dev/tux/.pw')
        files.append('/dev/tux/.df')
        files.append('/dev/tux/.ssh')
        files.append('/dev/tux/.tux')
        files.append('/dev/tux/ssh2/sshd2_config')
        files.append('/dev/tux/ssh2/hostkey')
        files.append('/dev/tux/ssh2/hostkey.pub')
        files.append('/dev/tux/ssh2/logo')
        files.append('/dev/tux/ssh2/random_seed')
        files.append('/dev/tux/backup/crontab')
        files.append('/dev/tux/backup/df')
        files.append('/dev/tux/backup/dir')
        files.append('/dev/tux/backup/find')
        files.append('/dev/tux/backup/ifconfig')
        files.append('/dev/tux/backup/locate')
        files.append('/dev/tux/backup/netstat')
        files.append('/dev/tux/backup/ps')
        files.append('/dev/tux/backup/pstree')
        files.append('/dev/tux/backup/syslogd')
        files.append('/dev/tux/backup/tcpd')
        files.append('/dev/tux/backup/top')
        files.append('/dev/tux/backup/updatedb')
        files.append('/dev/tux/backup/vdir')
        files.append('/dev/tux')
        files.append('/dev/tux/ssh2')
        files.append('/dev/tux/backup')
        


        # Universal Rootkit by K2 (URK) Release 0.9.8')
        files.append('/dev/prom/sn.l')
        files.append('/usr/lib/ldlibps.so')
        files.append('/usr/lib/ldlibnet.so')
        files.append('/dev/pts/01/uconf.inv')
        files.append('/dev/pts/01/cleaner')
        files.append('/dev/pts/01/bin/psniff')
        files.append('/dev/pts/01/bin/du')
        files.append('/dev/pts/01/bin/ls')
        files.append('/dev/pts/01/bin/passwd')
        files.append('/dev/pts/01/bin/ps')
        files.append('/dev/pts/01/bin/psr')
        files.append('/dev/pts/01/bin/su')
        files.append('/dev/pts/01/bin/find')
        files.append('/dev/pts/01/bin/netstat')
        files.append('/dev/pts/01/bin/ping')
        files.append('/dev/pts/01/bin/strings')
        files.append('/dev/pts/01/bin/bash')
        files.append('/usr/man/man1/xxxxxxbin/du')
        files.append('/usr/man/man1/xxxxxxbin/ls')
        files.append('/usr/man/man1/xxxxxxbin/passwd')
        files.append('/usr/man/man1/xxxxxxbin/ps')
        files.append('/usr/man/man1/xxxxxxbin/psr')
        files.append('/usr/man/man1/xxxxxxbin/su')
        files.append('/usr/man/man1/xxxxxxbin/find')
        files.append('/usr/man/man1/xxxxxxbin/netstat')
        files.append('/usr/man/man1/xxxxxxbin/ping')
        files.append('/usr/man/man1/xxxxxxbin/strings')
        files.append('/usr/man/man1/xxxxxxbin/bash')
        files.append('/tmp/conf.inv')
        files.append('/dev/prom')
        files.append('/dev/pts/01')
        files.append('/dev/pts/01/bin')
        files.append('/usr/man/man1/xxxxxxbin')
        
        # Also-see: /usr/lib/lpset (esniff), /var/lp/lpacct/ (files), /usr/lib/bnclp, /usr/lib/lpsys (identd),')
        # Also-see: /usr/lib/lptd (backdoor?), /sbin/rc2 and /sbin/rc3 containing string "/usr/lib/lpstart",')
        # Also-see: dos, psbnc, lpacct, USER, lp,')
        # Also see: /etc/lpconfig vs /etc/ttyhash, uconv.inv vs urk.conf.')


        # VcKit Rootkit')
        
        files.append('/usr/include/linux/modules/lib.so')
        files.append('/usr/include/linux/modules/lib.so/bin')
        
        # Volc Rootkit')
        # Omit listing system binaries that should be picked up by changed hashes.')
        files.append('/usr/bin/volc')
        files.append('/usr/lib/volc/backdoor/divine')
        files.append('/usr/lib/volc/linsniff')
        files.append('/etc/rc.d/rc1.d/S25sysconf')
        files.append('/etc/rc.d/rc2.d/S25sysconf')
        files.append('/etc/rc.d/rc3.d/S25sysconf')
        files.append('/etc/rc.d/rc4.d/S25sysconf')
        files.append('/etc/rc.d/rc5.d/S25sysconf')
        files.append('/var/spool/.recent')
        files.append('/var/spool/.recent/.files')
        files.append('/usr/lib/volc')
        files.append('/usr/lib/volc/backup')
        


        # weaponX 0.1')
        files.append('/System/Library/Extensions/WeaponX.kext')
        files.append('/tmp/...')
        


        # Xzibit Rootkit (also see MRK (MiCrobul?) RootKit)')
        files.append('/dev/dsx')
        files.append('/dev/caca')
        files.append('/dev/ida/.inet/linsniffer')
        files.append('/dev/ida/.inet/logclear')
        files.append('/dev/ida/.inet/sense')
        files.append('/dev/ida/.inet/sl2')
        files.append('/dev/ida/.inet/sshdu')
        files.append('/dev/ida/.inet/s')
        files.append('/dev/ida/.inet/ssh_host_key')
        files.append('/dev/ida/.inet/ssh_random_seed')
        files.append('/dev/ida/.inet/sl2new.c')
        files.append('/dev/ida/.inet/tcp.log')
        files.append('/home/httpd/cgi-bin/becys.cgi')
        files.append('/usr/local/httpd/cgi-bin/becys.cgi')
        files.append('/usr/local/apache/cgi-bin/becys.cgi')
        files.append('/www/httpd/cgi-bin/becys.cgi')
        files.append('/www/cgi-bin/becys.cgi')
        files.append('/dev/ida/.inet')
        


        # X-Org SunOS Rootkit')
        files.append('/usr/lib/libX.a/bin/tmpfl')
        files.append('/usr/lib/libX.a/bin/rps')
        files.append('/usr/bin/srload')
        files.append('/usr/lib/libX.a/bin/sparcv7/rps')
        files.append('/usr/sbin/modcheck')
        files.append('/usr/lib/libX.a')
        files.append('/usr/lib/libX.a/bin')
        files.append('/usr/lib/libX.a/bin/sparcv7')
        files.append('/usr/share/man...')
        


        # zaRwT.KiT Rootkit')
        files.append('/dev/rd/s/sendmeil')
        files.append('/dev/ttyf')
        files.append('/dev/ttyp')
        files.append('/dev/ttyn')
        files.append('/rk/tulz')
        files.append('/rk')
        files.append('/dev/rd/s')
        
        # ZK Rootkit')
        files.append('/usr/share/.zk/zk')
        files.append('/usr/X11R6/.zk/xfs')
        files.append('/usr/X11R6/.zk/echo')
        files.append('/etc/1ssue.net')
        files.append('/etc/sysconfig/console/load.zk')
        files.append('/usr/share/.zk')
        files.append('/usr/X11R6/.zk')
        


        # Miscellaneous login backdoors')
        files.append('/sbin/.login')
        files.append('/bin/.login')



        # Suspicious directories')
        files.append('/usr/X11R6/bin/.,/copy')
        files.append('/dev/rd/cdb')

        # Known bad Linux kernel modules')
        bad_kernel_modules = []
        bad_kernel_modules.append('adore.o')
        bad_kernel_modules.append('bkit-adore.o')
        bad_kernel_modules.append('cleaner.o')
        bad_kernel_modules.append('flkm.o')
        bad_kernel_modules.append('knark.o')
        bad_kernel_modules.append('modhide.o')
        bad_kernel_modules.append('mod_klgr.o')
        bad_kernel_modules.append('phide_mod.o')
        bad_kernel_modules.append('vlogger.o')
        bad_kernel_modules.append('p2.ko')
        bad_kernel_modules.append('rpldev.o')
        bad_kernel_modules.append('xC.o')
        bad_kernel_modules.append('rpldev.o')
        bad_kernel_modules.append('strings.o')
        bad_kernel_modules.append('wkmr26.ko')
        bad_kernel_modules.append('backd00r')
        bad_kernel_modules.append('backdoor')
        bad_kernel_modules.append('darkside')
        bad_kernel_modules.append('nekit')
        bad_kernel_modules.append('rpldev')
        bad_kernel_modules.append('rpldev_mod')
        bad_kernel_modules.append('spapem_core')
        bad_kernel_modules.append('spapem_genr00t')
        
        for file in files:
                targs = (file, )
                tm.startFunction( target=self._thread_read, args=targs, ownerObj=self )
        tm.join( self )
        
        kernel_modules = self.exec_payload('list_kernel_modules')
        for module in bad_kernel_modules:
            if module in kernel_modules:
                self.result['bad_kernel_modules'].append(module)

        return self.result
    
    def run_read(self, parameters):
        api_result = self.api_read( parameters )
        
        if not api_result:
            return 'Rootkit hunter failed to run.'
        else:
            rows = []
            rows.append( ['Description', 'Value'] ) 
            rows.append( [] )
            for key in api_result:
                for value in api_result[key]:
                    rows.append( [key, value] )
                              
            result_table = table( rows )
            result_table.draw( 80 )                    
            return

