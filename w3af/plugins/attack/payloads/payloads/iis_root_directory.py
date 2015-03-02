import re
from w3af.plugins.attack.payloads.base_payload import Payload

#TODO: TEST


class iis_root_directory(Payload):
    """
    This payload finds IIS Root Directories where websites are hosted.
    """
    def api_read(self):
        self.result = {}
        files = []

        def parse_www_root(iis6_log):
            root1 = re.findall(
                '(?<=OC_INIT_COMPONENT:32770=)(.*?) ', iis6_log, re.MULTILINE)
            root2 = re.findall(
                '(?<=m_csPathWWWRoot=)(.*?) ', iis6_log, re.MULTILINE)
            root3 = re.findall(
                '(?<=VRoot to create:/=)(.*?),', iis6_log, re.MULTILINE)
            root4 = re.findall('(?<=iis_www:CreateMDVRootTree():Start.LM/W3SVC/1./.)(.*?),', iis6_log, re.MULTILINE)
            root = root1 + root2 + root3 + root4
            if root:
                self.result['iis_root_directory'] = root

        def parse_ftp_root(iis6_log):
            ftp = re.findall('(?<=csPathFTPRoot=)(.*)', iis6_log, re.MULTILINE)
            if ftp:
                ftp = list(set(ftp))
                self.result['iis_ftp_directory'] = ftp

        def parse_web_pub(iis6_log):
            webpub = re.findall(
                '(?<=m_csPathWebPub=)(.*)', iis6_log, re.MULTILINE)
            if webpub:
                webpub = list(set(webpub))
                self.result['iis_webpub_directory'] = webpub

        files.append('/Windows/iis6.log')

        for file_ in files:
            content = self.shell.read(file_)
            if content:
                parse_www_root(content)
                parse_ftp_root(content)
                parse_web_pub(content)

        return self.result

    def run_read(self):
        api_result = self.api_read()
        result = []
        for k, v in api_result.iteritems():
            k = k.replace('_', ' ')
            print
            result.append(k.title() + " : " + v)
        if result == []:
            result.append('IIS root directory not found.')
        return result
