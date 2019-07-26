from abc import ABCMeta
from abc import abstractmethod


class BaseHook(object):  # pragma: no cover
    """This is an abstract class to define Hooks API. A hook is an alerting system
    that allows you connect your server scanning results to your larger ecosystem
    (e.g. email alerts, IRC pings...)
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def alert(self, repo_name, secrets):
        """
        :type repo_name: str
        :param repo_name: the repository where secrets were found.

        :type secrets: dict
        :param secrets: dictionary; where keys are filenames
        """
        pass
