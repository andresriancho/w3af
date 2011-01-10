from itertools import groupby
from operator import itemgetter

def groupbyMinKey( inputList ):
    '''
    This function takes a list with tuples of length two inside:
        [(1,'a'),(1,'b'),('c',True),('d','x')]
    
    And return a dict with a list as value:
        {1:['a','b'], 'c': [True], 'd':['x']}
        
    The good thing about this function is that it will find the min key, as you saw, in the first case
    1, 'c' and 'd' were selected as keys ( the items on the left of the tuples ); but if the input is this:
        [(1,'a'),(2,'a'),('c','a'),('d','x')]
    
    It will return a dict with a list as value:
        {'a':[1,2,'c'], 'x':['d']}
    
    Additionally, this function returns the item number of the tuple that was used to groupby ( 0 or 1 ).
    
    This function was created to show information to the user in a better way.
    '''
    
    # So, first, we groupby the first item in the tuples
    key = itemgetter(0)
    value = itemgetter(1)
    resDict1 = {}
    for key, group in groupby(inputList, key):
        resDict1[ key ] = [ value(x) for x in group ]

    # Now, we groupby the second item in the tuples
    key = itemgetter(1)
    value = itemgetter(0)
    resDict2 = {}
    for key, group in groupby(inputList, key):
        resDict2[ key ] = [ value(x) for x in group ]
    
    # Finally we compare which dict has more keys, and return the one with less keys.
    if len( resDict1 ) > len( resDict2 ):
        return resDict2, 1
    else:
        return resDict1, 0

if __name__ == '__main__':
    print groupbyMinKey( [('a', 1) , ('a', 2) , ('a', 3)] )
    print groupbyMinKey( [(1, 'a') , (2, 'a') , (3, 'a')] )
    
