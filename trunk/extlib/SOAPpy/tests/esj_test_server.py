#!/usr/bin/python2

#standard imports
import syslog, sys

#domain specific imports
sys.path.insert (1, '..')
import SOAPpy

class test_service:

    run = 1
    
    def test_integer(self,pass_integer):
        print type(pass_integer)
        return pass_integer

    def test_string(self,pass_string):
        print type(pass_string)
        return pass_string

    def test_float(self,pass_float):
        print type(pass_float)
        return pass_float

    def test_tuple(self,pass_tuple):
        print type(pass_tuple), pass_tuple
        return pass_tuple

    def test_list(self,pass_list):
        print type(pass_list), pass_list
        return pass_list

    def test_dictionary(self,pass_dictionary):
        print type(pass_dictionary), pass_dictionary
        return pass_dictionary

    def quit(self):
        self.run = 0

server = SOAPpy.SOAPServer(("localhost",9999))
SOAPpy.Config.simplify_objects=1

access_object = test_service()
server.registerObject(access_object)

while access_object.run:
    server.handle_request()
