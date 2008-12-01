# grep demo that find HTTP dump in response body

plugins
output console
output config textFile
set fileName output-w3af.txt
set verbose True
back
output config console
back

grep newline
back

target
set target http://localhost/w3af/grep/newline/abc.html
back

start

assert len( kb.kb.getData( 'newline', 'unix' ) ) == 1

exit
