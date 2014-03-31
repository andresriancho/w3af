"""
serialization_perf.py

Copyright 2012 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""

def do_msgpack(obj):
    msg = msgpack.packb([1,2,3])
    msgpack.unpackb(msg)
    
def do_json(obj):
    msg = json.dumps(obj)
    json.loads(msg)

def do_cpickle(obj):
    msg = cPickle.dumps(obj)
    cPickle.loads(msg)

def do_ultrajson(obj):
    msg = ujson.dumps(obj)
    ujson.loads(msg)

def measure(funct, times, *args):
    start = time.time()
    
    for _ in xrange(times):
        funct(*args)
        
    return time.time() - start 

test_objects = [('simple_dict', {'a': 2}),
                ('many_keys_dict', {'a': 1,
                                    'b': 2,
                                    'c': 3,
                                    'd': 4,
                                    'e': 5}),
                ('long_keys_vals', {'a' * 512: 'b' * 512,
                                    'b' * 512: 'c' * 512,}),
                ('very_long_keys_vals', {'a' * 2**16: 'b' * 2**16,
                                         'b' * 2**16: 'c' * 2**16,}),
                ]

tests = [('msgpack', do_msgpack),
         ('json', do_json),
         ('cpickle', do_cpickle),
         ('ujson', do_ultrajson)]

if __name__ == '__main__':
    import time
    import msgpack
    import json
    import cPickle
    import ujson

    for serializator_name, serializator_func in tests:
        total_time = 0
        
        for test_object_name, test_object in test_objects:
            time_spent = measure(serializator_func, 10000, test_object)
            total_time += time_spent
            print '%s took %s seconds to complete %s' % (serializator_name,
                                                         time_spent,
                                                         test_object_name)
            
        print '%s took %s seconds to complete all tests.' % (serializator_name,
                                                             total_time)
        print
    
    """
    msgpack is *very fast*:
    
        msgpack took 0.0302159786224 seconds to complete simple_dict
        msgpack took 0.0301239490509 seconds to complete many_keys_dict
        msgpack took 0.0296750068665 seconds to complete long_keys_vals
        msgpack took 0.029764175415 seconds to complete very_long_keys_vals
        msgpack took 0.119779109955 seconds to complete all tests.
        
        json took 0.101440906525 seconds to complete simple_dict
        json took 0.131711959839 seconds to complete many_keys_dict
        json took 0.26731300354 seconds to complete long_keys_vals
        json took 18.3413910866 seconds to complete very_long_keys_vals
        json took 18.8418569565 seconds to complete all tests.
        
        cpickle took 0.0272090435028 seconds to complete simple_dict
        cpickle took 0.0501630306244 seconds to complete many_keys_dict
        cpickle took 0.184257984161 seconds to complete long_keys_vals
        cpickle took 15.9105920792 seconds to complete very_long_keys_vals
        cpickle took 16.1722221375 seconds to complete all tests.
        
        ujson took 0.00930905342102 seconds to complete simple_dict
        ujson took 0.0165259838104 seconds to complete many_keys_dict
        ujson took 0.165940999985 seconds to complete long_keys_vals
        ujson took 27.2875270844 seconds to complete very_long_keys_vals
        ujson took 27.4793031216 seconds to complete all tests.
    
    To sum up, for sending 10k requests (which I was pickling for logging them)
    I was wasting (around) 16 seconds in the process of pickling them, this is
    very_long_keys_vals. Now with msgpack I spend only 0.02 secs.
    """