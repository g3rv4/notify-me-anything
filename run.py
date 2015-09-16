import argparse
import time
from utils import get_events_raiser, get_notification


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", help="event raiser class", required=True)
    parser.add_argument("--notification", help="notification class", required=True)
    args = parser.parse_known_args()[0]

    events_raiser = get_events_raiser(args.event)
    events_raiser.add_arguments_to_parser(parser)
    args = parser.parse_args()

    with events_raiser:
        with get_notification(args.notification) as notification_helper:
            for i in range(0, 2):
                notifications = events_raiser.get_notifications(args)
                if len(notifications):
                    notification_helper.notify(notifications)
                time.sleep(20)

if __name__ == "__main__":
    main()
