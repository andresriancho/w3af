#import core.data.kb.knowledgeBase as kb
import re

files = []

def check_files( files ):
    checked = []
    for file in files:
        if read(file) != '':
            checked.append(file)
    return checked

def get_files( file_content ):
    #Check regex
    files = re.findall('(/.*/)+(.*)(?!/)', file_content, re.MULTILINE)
    if files:
        #files = check_files(files)
        for file in files:
            #get_files(file)
            files.append(file)
        return files
    else:
        return ''


