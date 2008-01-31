*ABOUT*

Tested with Python 2.4 on Windows and Linux.

json.py is a simple, pure-python implementation of a JSON (http://json.org)
reader and writer. JSON is used to exchange data across systems written in
various languages. It is particularly suited to dynamic languages like Python,
Javascript, etc. JSON = Javascript Object Notation implies it is suitable for
AJAX applications that exchange data from servers to Javascript applications
running on web browser clients.

The JSON format is simpler than XML and this implementation in Python is
correspondingly simple. jsontests.py accompanies the implementation with unit
tests demonstrating correctness. There are more than 40 tests that all run.

There is one other Python implementation of JSON I have found
(http://json-rpc.org/pyjsonrpc/index.xhtml). My sources shares nothing in
common with this other one. I started this new project because of the
incompleteness and complexity of the existing implementation.

Jim Washington has implemented minjson which is in this same repository. While
json-py is intended to be a simple implementation that could be translated
easily into other languages, minjson is intended to use efficient Python
idioms.

json-py passes all the tests in jsontest. minjson does not. See jsontest.py
for instructions on running the tests with minjson. 

*TODO*

Unicode characters have been somwhat tested. Need to add the ability to choose
encoding when writing json strings.

Reads and writes strings all-at-once. Does not operate on streams of
characters. The internal _StringGenerator class could be modified without too
much trouble to do this.

Boundary conditions, etc. The tests written so far have met my own immediate
needs for developing and using the JSON reader and writer. More thorough tests
are needed to demonstrate completeness.

There is no control over writing decimal numbers, e.g. number of places. The
current behavior is to use Python's %f as-is.

*CONTACT*

mailto:patrickdlogan@stardecisions.com
