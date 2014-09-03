import platform

from .ubuntu1204 import Ubuntu1204


class Debian(Ubuntu1204):
    SYSTEM_NAME = 'Debian'

    @staticmethod
    def is_current_platform():
        return 'debian' in platform.dist()

