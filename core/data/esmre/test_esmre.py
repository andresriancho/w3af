from multire import multire
from test_data import HTTP_RESPONSE, SQL_ERRORS

def main():

    _multire = multire( SQL_ERRORS )

    for i in xrange(10000):
        _multire.query( HTTP_RESPONSE )

    
if __name__ == '__main__':
    main()
