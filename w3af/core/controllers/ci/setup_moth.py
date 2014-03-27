#!/usr/bin/env python

# I want to perform the following steps:
#	* Get the source code for the django-moth project from the repository
#	* Install any dependencies required by that project
#	* Start the Django application which will listen both on HTTP and HTTPS.
#     This step is done by a script which is present in the django-moth 
#     repository.
#
# This script MUST be runnable from the circle.yml configuration file, in order
# to allow this to run in our CI system, but also in a direct way so that
# developers can start it in their workstations and run the unittests.
#
# The dependencies will be installed inside a virtualenv.
#
# The script itself won't daemonize itself, you should do that when calling it.
# 
# When running, the script will print classic "manage.py runserver" output to
# the console, which will help debug any issues. The output looks like this:
#     [20/Nov/2013 23:27:45] "GET /grep/svn_users/ HTTP/1.1" 200 2245
#     [20/Nov/2013 23:27:45] "GET /grep/svn_users/DhHg3l4E.cgi HTTP/1.1" 404 1615
#
# The output from the runserver command will also be written to a temporary file
# which will be made available to the build system as an artifact.
#
import os
import shlex
import logging
import tempfile
import subprocess

from utils import configure_logging


DJANGO_MOTH_REPO = 'https://github.com/andresriancho/django-moth.git'
DJANGO_MOTH_DIR = 'django-moth'
VIRTUALENV_DIR = os.path.join(DJANGO_MOTH_DIR, 'venv')
ARTIFACTS_DIR = os.environ.get('CIRCLE_ARTIFACTS', tempfile.gettempdir())
INSTALL_DIR = tempfile.gettempdir()
LOG_FILE = os.path.join(ARTIFACTS_DIR, 'setup-moth.log')


def get_source_code():
    """
    Download the source code to a location which Circle will then cache in
    order to avoid getting the source code each time we run our tests. If the
    target directory already exists, we should simply "git pull".
    """
    if os.path.exists(DJANGO_MOTH_DIR):
        # CircleCI restored the cache and this was already there. We simply
        # "git pull". This is possible because we ask circle to cache the
        # django-moth directory.
        run_cmd('git pull', cwd=DJANGO_MOTH_DIR)
    else:
        # We need to "git clone" the repository
        run_cmd('git clone %s' % DJANGO_MOTH_REPO)
        

def install_dependencies():
    """
    Create a virtualenv where all dependencies will be installed.
    
    Once again, do this in a location where circleci will cache in order to
    avoid installing all dependencies each time. Also, if the virtualenv is
    already there, we just need to run "pip install -r requirements.txt" to get
    the new dependencies.
    """
    if not os.path.exists(VIRTUALENV_DIR):
        run_cmd('virtualenv %s' % VIRTUALENV_DIR)
        
    run_cmd('%s/bin/pip install -r %s/requirements.txt' % (VIRTUALENV_DIR,
                                                           DJANGO_MOTH_DIR,))

def start_daemons(log_directory=ARTIFACTS_DIR):
    """
    Start the django application in HTTP and HTTPS.
    """
    cmd = '%s/bin/python %s/start_daemons.py --log-directory=%s' % (VIRTUALENV_DIR,
                                                                    DJANGO_MOTH_DIR,
                                                                    log_directory)
    run_cmd(cmd)

def run_cmd(cmd, cwd=None):
    logging.debug('[s] %s (cwd: %s)' % (cmd, cwd))
    p = subprocess.Popen(shlex.split(cmd), cwd=cwd)
    p.wait()
    logging.debug('[e] %s (retcode: %s) (cwd: %s)' % (cmd, p.returncode, cwd))
    return p.returncode

if __name__ == '__main__':
    configure_logging(LOG_FILE)
    get_source_code()
    install_dependencies()
    start_daemons()
