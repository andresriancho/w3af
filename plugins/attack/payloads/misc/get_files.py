import core.data.kb.knowledgeBase as kb
import re

files = []

def check_files( files ):
    checked = []
    for file in files:
        try:
            if open(file).read() != '':
                checked.append(file)
        except IOError:
            pass
    return checked

def get_files( file_content ):
    files = re.findall('.*', file_content, re.MULTILINE)
    if files:
        #files = check_files(files)
        for file in files:
            #get_files(file)
            files.append(file)
        return files
    else:
        return ''


