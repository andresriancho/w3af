# This scripts tests the wordnet plugin

plugins
output console,textFile
output config textFile
set fileName output-w3af.txt
set verbose True
back
output config console
set verbose False
back

discovery favicon_identification
back

target
set target http://www.google.com/
back

start

assert len( kb.kb.getData('favicon_identification', 'info') ) == 1

exit