import platform

from .ubuntu1204 import Ubuntu1204


class Ubuntu1804(Ubuntu1204):
    SYSTEM_NAME = 'Ubuntu 18.04'

    @staticmethod
    def is_current_platform():
        return 'Ubuntu' in platform.dist() and '18.04' in platform.dist()