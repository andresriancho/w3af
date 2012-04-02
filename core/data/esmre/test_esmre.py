from multi_re import multi_re
from test_data import HTTP_RESPONSE, SQL_ERRORS

def main():

    _multi_re = multi_re( SQL_ERRORS )

    for i in xrange(10000):
        _multi_re.query( HTTP_RESPONSE )

    
if __name__ == '__main__':
    main()
