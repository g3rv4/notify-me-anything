import Foundation
import objc
from notifications.base_notification import BaseNotification


class MacOSNotification(BaseNotification):
    def __enter__(self):
        self.helper = NotificationHelper.alloc().init()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.helper.dealloc()

    def do_notify(self, notifications):
        for notification in notifications:
            self.helper.notify(notification.title, notification.subtitle, notification.text, notification.sound)


class NotificationHelper(Foundation.NSObject):
    def init(self):
        self = objc.super(NotificationHelper, self).init()
        if self is None:
            return None

        # Get objc references to the classes we need.
        self.NSUserNotification = objc.lookUpClass('NSUserNotification')
        self.NSUserNotificationCenter = objc.lookUpClass('NSUserNotificationCenter')

        return self

    def clearNotifications(self):
        """Clear any displayed alerts we have posted. Requires Mavericks."""

        NSUserNotificationCenter = objc.lookUpClass('NSUserNotificationCenter')
        NSUserNotificationCenter.defaultUserNotificationCenter().removeAllDeliveredNotifications()

    def notify(self, title, subtitle, text, sound):
        """Create a user notification and display it."""

        notification = self.NSUserNotification.alloc().init()
        notification.setTitle_(str(title))
        if subtitle:
            notification.setSubtitle_(str(subtitle))
        if text:
            notification.setInformativeText_(str(text))
        if sound:
            notification.setSoundName_("%s.aiff" % sound)

        notification.setHasActionButton_(False)

        self.NSUserNotificationCenter.defaultUserNotificationCenter().setDelegate_(self)
        self.NSUserNotificationCenter.defaultUserNotificationCenter().scheduleNotification_(notification)
