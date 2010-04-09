#NOT FINISHED
import re
from plugins.attack.payloads.base_payload import base_payload

class apache_modsecurity(base_payload):
    '''
    This payload shows ModSecurity version,rules and configuration files.
    '''
    def api_read(self):
        result = {}
        result['files'] = {}
        modules = []
        files = []

        modules.append('mods-available/mod-security.load')
        modules.append('mods-available/mod-security2.load')


        def parse_version(binary):
            version = re.search('(?<=ModSecurity for Apache/)(.*?) ', binary)
            print version.group(0)
            if version:
                return version.group(0)
            else:
                return ''

        def parse_binary_location(module_config):
            binary = re.search('(?<=module )(.*)', module_config)
            if binary:
                return binary.group(0)
            else:
                return ''

        bin_location = []
        apache_config_files = self.exec_payload('apache_config_files')['apache_config']
        apache_config_dir = self.exec_payload('apache_config_directory')['apache_directory']
        if apache_config_files:
            for file in apache_config_files:
                if re.search('security2_module', self.shell.read(file)) or re.search('security_module', self.shell.read(file)):
                    bin_location.append(parse_binary_location(self.shell.read(file)))
                
        if bin_location == []:
            if apache_config_dir:
                for dir in apache_config_dir:
                    for module in modules:
                        dirmodule = self.shell.read(dir+module)
                        if dirmodule:
                            bin_location.append(parse_binary_location(dirmodule))

        bin=[]
        for location in bin_location:
            if location[0] != '/':
                bin.append('/usr/lib/apache2/'+location)
                bin.append('/usr/lib/httpd/'+location)
                bin.append('/usr/local/'+location)
                bin.append('/usr/lib/'+location)
                for item in bin:
                    version_item = parse_version(self.shell.read(item))
                    if version_item:
                        result['version'] = version_item
            else:
                version_location = parse_version(self.shell.read(location))
                if version_location:
                    result['version'] = version_location


        files.append(dir+'conf/mod_security.conf')
        files.append(dir+'conf.d/mod_security.conf')
        files.append(dir+'modsecurity.d/modsecurity_crs_10_config.conf')
        files.append(dir+'modsecurity.d/modsecurity_crs_10_global_config.conf')
        files.append(dir+'modsecurity.d/modsecurity_localrules.conf')
        files.append(dir+'conf/modsecurity.conf')
        files.append(dir+'mods-available/mod-security.conf')

        for file in files:
            file_content = self.shell.read(file)
            if file_content:
                result['files'].update({file:file_content})

        return result
    
    def run_read(self):
        hashmap = self.api_read()
        result = []
        if hashmap['version']:
            result.append('ModSecurity Version: ' + hashmap['version'])
            
        for file, content in hashmap['files'].iteritems():
            result.append('-------------------------')
            result.append(file)
            result.append('-------------------------')
            result.append(content)
  
        if result == [ ]:
            result.append('ModSecurity configuration files not found.')
        return result
