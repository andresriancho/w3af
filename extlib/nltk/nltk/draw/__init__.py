# Natural Language Toolkit: graphical representations package
#
# Copyright (C) 2001-2009 NLTK Project
# Author: Edward Loper <edloper@gradient.cis.upenn.edu>
#         Steven Bird <sb@csse.unimelb.edu.au>
# URL: <http://www.nltk.org/>
# For license information, see LICENSE.TXT
#
# $Id: __init__.py 7524 2009-02-04 05:25:18Z StevenBird1 $

# Import Tkinter-based modules if Tkinter is installed
try:
    import Tkinter
    from cfg import *
    from plot import *
    from tree import *
    from dispersion import dispersion_plot

    # Make sure that nltk.draw.cfg and nltk.draw.tree refer to the correct
    # modules (and not to nltk.cfg & nltk.tree)
    import cfg, tree

except ImportError:
    print "Warning: nltk.draw package not loaded (please install Tkinter library)."
