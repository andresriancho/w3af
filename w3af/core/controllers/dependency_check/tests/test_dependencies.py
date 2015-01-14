import unittest
import subprocess
import shlex
import sys

from nose.plugins.attrib import attr


@attr('smoke')
class TestDependenciesInstalled(unittest.TestCase):

    def test_dependencies_installed(self):
        DEPS_CMD = "%s -c 'from w3af.core.controllers.dependency_check."\
                   "dependency_check import dependency_check; dependency_check()'"
        try:
            subprocess.check_output(shlex.split(DEPS_CMD % sys.executable))
        except subprocess.CalledProcessError, cpe:
            self.assertEqual(False, True, cpe.output)
