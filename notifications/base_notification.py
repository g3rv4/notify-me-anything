from abc import ABCMeta, abstractmethod
from utils import InstantiateThisByDefault


class BaseNotification(InstantiateThisByDefault):
    __metaclass__ = ABCMeta

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def do_notify(self, notifications):
        pass

    def notify(self, notifications):
        self.do_notify([n for n in notifications if n])


class Notification(object):
    def __init__(self, title=None, subtitle=None, text=None, sound=None):
        self.title = title
        self.subtitle = subtitle
        self.text = text
        self.sound = sound
