from settings import settings
from selenium import webdriver
from abc import ABCMeta, abstractmethod
from utils import InstantiateThisByDefault


class BaseEventRaiser(InstantiateThisByDefault):
    __metaclass__ = ABCMeta

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def add_arguments_to_parser(self, parser):
        pass

    @staticmethod
    def get_selenium_driver():
        browser_config = settings['selenium']['browsers'][settings['selenium']['browser']]
        klass = getattr(globals()['webdriver'], browser_config['driver_class'])
        return klass(executable_path=browser_config['executable_path'])

    @abstractmethod
    def get_notifications(self, args):
        pass
