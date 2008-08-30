'''
wizard.py

Copyright 2008 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''
from core.controllers.w3afException import w3afException
from core.controllers.wizard.wizards.short_wizard import short_wizard

# How to select wizards:
#   import core.controllers.wizard.wizards as wiz
#   dir(wiz)
#       ['__builtins__', '__doc__', '__file__', '__name__', '__path__', 'short_wizard']

# Get a wizard instance:
sw = short_wizard()
# description:
#    sw.getWizardDescription()

# Get the firs step of the wizard
q1 = sw.next()
print 'q1 title:', q1.getQuestionTitle()
print 'q1 question:', q1.getQuestionString()

# View the questions in this step, and answer with null
options = q1.getOptionObjects()
for i in options:
    print i.getDesc()
    i.setValue('')

# this has to fail, because the question requires that
# you enter some value in the field
try:
    sw.setAnswer(options)
except Exception, e:
    print 'Failed (as expected):', e

# Now we fill it with a valid value
i.setValue('http://localhost/')
try:
    sw.setAnswer(options)
except Exception, e:
    print 'Failed! (not expected... something went wrong):', e
else:
    print 'Ok'

# Now that we have setted the answer, we get the next question
q2 = sw.next()
print 'q2 title:', q1.getQuestionTitle()
print 'q2 question:', q1.getQuestionString()

# The user doesn't change anything
options = q2.getOptionObjects()
sw.setAnswer(options)

if sw.next() == None:
    print 'Finished the wizard'

