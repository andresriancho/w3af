"""
------------------------------------------------------------------
Author:    Gregory R. Warnes <Gregory.R.Warnes@Pfizer.com>
Date:      2005-02-24
Version:   0.7.2
Copyright: (c) 2003-2005 Pfizer, Licensed to PSF under a Contributor Agreement
License:   Licensed under the Apache License, Version 2.0 (the"License");
	   you may not use this file except in compliance with the License.
	   You may obtain a copy of the License at

	       http://www.apache.org/licenses/LICENSE-2.0

	   Unless required by applicable law or agreed to in
	   writing, software distributed under the License is
	   distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
	   CONDITIONS OF ANY KIND, either express or implied.  See
	   the License for the specific language governing
	   permissions and limitations under the License.
------------------------------------------------------------------
"""



from distutils.core import setup

url="http://www.analytics.washington.edu/statcomp/projects/rzope/fpconst/"

import fpconst

setup(name="fpconst",
      version=fpconst.__version__,
      description="Utilities for handling IEEE 754 floating point special values",
      author="Gregory Warnes",
      author_email="Gregory.R.Warnes@Pfizer.com",
      url = url,
      long_description=fpconst.__doc__,
      py_modules=['fpconst']
     )

