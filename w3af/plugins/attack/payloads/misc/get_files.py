import w3af.core.data.kb.knowledge_base as kb
import re

files = []


def check_files(file_list):
    """
    Verify if a list of files exist and have content.

    :param file_list: The list of files to check.
    :return: The list of files that exist.
    """
    checked = []
    for file in file_list:
        try:
            if open(file).read() != '':
                checked.append(file)
        except IOError:
            pass
    return checked


def get_files(file_content):
    files = re.findall('.*', file_content, re.MULTILINE)
    if files:
        #files = check_files(files)
        for file in files:
            #get_files(file)
            files.append(file)
        return files
    else:
        return ''
