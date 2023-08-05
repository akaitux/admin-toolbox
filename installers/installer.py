import abc


class Installer(abc.ABC):
    @abc.abstractmethod
    def install(self):
        """install"""

    @abc.abstractmethod
    def make_activate_replaces(self) -> dict:
        """dict with replaces for activate script"""


