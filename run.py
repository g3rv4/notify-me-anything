import argparse
import time
from utils import get_events_raiser, get_notification
from notifications.base_notification import Notification


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", help="event raiser class", required=True)
    parser.add_argument("--notification", help="notification class", required=True)
    parser.add_argument("--just-notify", help="just raise a notification", action='store_true')
    args = parser.parse_known_args()[0]

    events_raiser = get_events_raiser(args.event)
    events_raiser.add_arguments_to_parser(parser)
    args = parser.parse_args()

    with events_raiser:
        with get_notification(args.notification) as notification_helper:
            if args.just_notify:
                notif = Notification('asd', 'qwe')
                notification_helper.notify([notif])
                exit()
            while True:
                notifications = events_raiser.get_notifications(args)
                if len(notifications):
                    notification_helper.notify(notifications)
                time.sleep(30)

if __name__ == "__main__":
    main()
