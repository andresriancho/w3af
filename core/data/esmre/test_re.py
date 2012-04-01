from multire import multire
from test_data import HTTP_RESPONSE, SQL_ERRORS
import re

def main():

    C_SQL_ERRORS = [ re.compile(et[0], re.IGNORECASE) for et in SQL_ERRORS ]

    for i in xrange(10000):
        for cregex in C_SQL_ERRORS:
            cregex.search( HTTP_RESPONSE )
    
if __name__ == '__main__':
    main()
