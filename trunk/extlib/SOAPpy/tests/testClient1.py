import gc
import socket
import threading
import time
import unittest
import sys
sys.path.insert(1, "..")

import SOAPpy
#SOAPpy.Config.debug=1

# global to shut down server
quit = 0

def echoDateTime(dt):
    return dt

def echo(s):
    """repeats a string twice"""
    return s + s 

def kill():
    """tell the server to quit"""
    global quit
    quit = 1

def server1():
    """start a SOAP server on localhost:8000"""
    
    print "Starting SOAP Server...",
    server = SOAPpy.Server.SOAPServer(addr=('127.0.0.1', 8000))
    server.registerFunction(echoDateTime)
    server.registerFunction(echo)
    server.registerFunction(kill)
    print "Done."
    
    global quit
    while not quit: 
        server.handle_request()
    quit = 0
    print "Server shut down."

class ClientTestCase(unittest.TestCase):

    server = None
    startup_timeout = 5 # seconds

    def setUp(self):
        '''This is run once before each unit test.'''

        serverthread = threading.Thread(target=server1, name="SOAPServer")
        serverthread.start()

        start = time.time()
        connected = False
        server = None
        while not connected  and time.time() - start < self.startup_timeout:
            print "Trying to connect to the SOAP server...",
            try:
                server = SOAPpy.Client.SOAPProxy('127.0.0.1:8000')
                server.echo('Hello World')
            except socket.error, e:
                print "Failure:", e
                time.sleep(0.5)
            else:
                connected = True
                self.server = server
                print "Success."

        if not connected: raise 'Server failed to start.'

    def tearDown(self):
        '''This is run once after each unit test.'''

        print "Trying to shut down SOAP server..."
        if self.server is not None:
            self.server.kill()
            time.sleep(5)

        return 1

    def testEcho(self):
        '''Test echo function.'''

        server = SOAPpy.Client.SOAPProxy('127.0.0.1:8000')
        s = 'Hello World'
        self.assertEquals(server.echo(s), s+s)

    def testNamedEcho(self):
        '''Test echo function.'''

        server = SOAPpy.Client.SOAPProxy('127.0.0.1:8000')
        s = 'Hello World'
        self.assertEquals(server.echo(s=s), s+s)

    def testEchoDateTime(self):
        '''Test passing DateTime objects.'''

        server = SOAPpy.Client.SOAPProxy('127.0.0.1:8000')
        dt = SOAPpy.Types.dateTimeType(data=time.time())
        dt_return = server.echoDateTime(dt)
        self.assertEquals(dt_return, dt)


#     def testNoLeak(self):
#         '''Test for memory leak.'''

#         gc.set_debug(gc.DEBUG_SAVEALL)
#         for i in range(400):
#             server = SOAPpy.Client.SOAPProxy('127.0.0.1:8000')
#             s = 'Hello World'
#             server.echo(s)
#         gc.collect()
#         self.assertEquals(len(gc.garbage), 0)


if __name__ == '__main__':
    unittest.main()
