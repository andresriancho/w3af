#!/bin/bash -x

# The order in which these are run doesn't really matter, but I do need to
# take care of "grouping" (which directory is run) because of an incompatibility
# between "w3af/core/ui/gui/" and "w3af/core/ui/tests/" which comes from
# Gtk2 vs. Gtk3.

PARAMS="--with-doctest --doctest-tests"
SELECTORS="smoke and not internet and not moth and not root"

nosetests $PARAMS -A "$SELECTORS" w3af/core/controllers/
nosetests $PARAMS -A "$SELECTORS" w3af/core/data/
nosetests $PARAMS -A "$SELECTORS" w3af/core/ui/tests/
nosetests $PARAMS -A "$SELECTORS" w3af/core/ui/console/
nosetests $PARAMS -A "$SELECTORS" w3af/core/ui/gui/
nosetests $PARAMS -A "$SELECTORS" w3af/plugins/
        
# TODO: Run the tests which require moth
