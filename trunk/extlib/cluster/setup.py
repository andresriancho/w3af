from distutils.core import setup

readmeContents = open("README").read()
parastart = readmeContents.find('=\n')+3 # index where the first paragraph starts

setup(name='cluster',
      version='1.1.1b3',
      author='Michel Albert',
      author_email='exhuma@users.sourceforge.net',
      url='http://python-cluster.sourceforge.net/',
      py_modules=['cluster'],
      license='LGPL',
      description=readmeContents[parastart: readmeContents.find('.', parastart)], # first sentence of first paragraph
      long_description = readmeContents
      )
