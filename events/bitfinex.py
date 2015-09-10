from decimal import Decimal
from events.base_event_raiser import BaseEventRaiser
import requests
import json
from utils import redis_get, redis_set
from notifications.base_notification import Notification


class BitfinexEventRaiser(BaseEventRaiser):
    def add_arguments_to_parser(self, parser):
        parser.add_argument("--small-delta", help="small difference", type=Decimal, required=True)
        parser.add_argument("--big-delta", help="big difference", type=Decimal, required=False)

    def get_notifications(self, args):
        try:
            response = requests.get('https://api.bitfinex.com/v1/pubticker/btcusd')
            current_value = Decimal(json.loads(response.content)['last_price'])
        except:
            return []

        try:
            last_value = Decimal(redis_get('bitfinex:value'))
        except:
            last_value = Decimal('0')

        variation = abs(current_value - last_value)

        notification = None
        if args.big_delta and variation > args.big_delta:
            notification = Notification(title='BIG CHANGE DOWN',
                                        text='Old value: %s\nNew value: %s' % (str(last_value), str(current_value)))
            if current_value > last_value:
                notification.title = 'BIG CHANGE UP!!!'
        elif variation > args.small_delta:
            notification = Notification(title='change down',
                                        text='Old value: %s\nNew value: %s' % (str(last_value), str(current_value)))
            if current_value > last_value:
                notification.title = 'change up!!!'

        if notification:
            redis_set('bitfinex:value', str(current_value))

        return [notification]
