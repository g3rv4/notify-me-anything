import importlib
import inspect
from abc import ABCMeta
from glob import glob
import os
import sys
import redis
from settings import settings

redis_cli = redis.StrictRedis(db=settings['redis_db'])
modules_loaded = False


def load_modules():
    global modules_loaded
    if modules_loaded:
        return

    for package in ('events', 'notifications'):
        modules = glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "%s/*.py" % package))
        for module in modules:
            name = module[:-3]
            name = '%s.' % package + name.split('/%s/' % package)[1].replace('/', '.')
            importlib.import_module(name)

    modules_loaded = True


def instantiate_class(module, name):
    load_modules()
    parts = name.split('.')
    module = '%s.%s' % (module, parts[0])
    if len(parts) == 2:
        return getattr(sys.modules[module], parts[1])()
    else:
        c = [m[1] for m in inspect.getmembers(sys.modules[module], inspect.isclass) if
             issubclass(m[1], InstantiateThisByDefault) and not inspect.isabstract(m[1])]
        if len(c) > 1:
            print 'Too many InstantiateThisByDefault classes on %s module, please specify the class to use' % module
            exit(1)
        elif len(c) == 0:
            print 'No InstantiateThisByDefault on %s module' % module
            exit(1)
        return c[0]()


def get_events_raiser(events_raiser_name):
    return instantiate_class('events', events_raiser_name)


def get_notification(notification_name):
    return instantiate_class('notifications', notification_name)


def redis_set(name, *args, **kwargs):
    redis_cli.set('notify_me_anything:%s' % name, *args, **kwargs)


def redis_get(name):
    return redis_cli.get('notify_me_anything:%s' % name)

class InstantiateThisByDefault(object):
    __metaclass__ = ABCMeta
