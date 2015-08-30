from events.base_event_raiser import BaseEventRaiser
from decimal import Decimal
from unidecode import unidecode
from utils import redis_get, redis_set
from notifications.base_notification import Notification
import time


class BROUEventRaiser(BaseEventRaiser):
    def __init__(self):
        self.messages = {
            'open': ('Brou exchange started operations', 'New value: {new_value}', 'Old value: {old_value}', "NSUserNotificationDefaultSoundName"),
            'closed': ('Brou exchange finished operations', 'New value: {new_value}', 'Old value: {old_value}', "NSUserNotificationDefaultSoundName")
        }

    def __enter__(self):
        self.driver = BROUEventRaiser.get_selenium_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.close()

    def add_arguments_to_parser(self, parser):
        parser.add_argument("--value-to-check", help="use buy or sell", choices=['buy', 'sell'], default='buy')
        parser.add_argument("--avoid-open-notification", help="skip open market notification", action="store_true")
        parser.add_argument("--small-delta", help="small difference", type=Decimal, required=True)
        parser.add_argument("--big-delta", help="big difference", type=Decimal, required=False)

    def get_notifications(self, args):
        rates = self.get_current_rates()

        current_value = rates['Dolar e-Brou'][args.value_to_check]
        try:
            last_value = Decimal(redis_get('brou:value'))
        except:
            last_value = Decimal('0')

        status = 'open' if abs(rates['Dolar']['buy'] - rates['Dolar e-Brou']['buy']) > Decimal('0.05') else 'closed'
        last_status = redis_get('brou:status')

        notification = None
        variation = abs(current_value - last_value)
        if not args.avoid_open_notification and (not last_status or last_status != status):
            # notify status change
            notification= Notification(*[v.format(new_value=str(rates['Dolar e-Brou'][args.value_to_check]),
                                                  old_value=str(last_value)) if v else None for v in self.messages[status]])
            redis_set('brou:status', status)
        elif args.big_delta and variation >= args.big_delta:
            notification = Notification(title='BIG CHANGE DOWN :(', subtitle='New value: %s' % str(current_value),
                                        sound='sad.aiff', text='Old value: %s' % str(last_value))
            if current_value > last_value:
                notification.title = 'BIG CHANGE UP!!! :)'
                notification.sound = 'perere.aiff'
        elif variation >= args.small_delta:
            notification = Notification(title='change down :(', subtitle='New value: %s' % str(current_value),
                                        sound='boo.aiff', text='Old value: %s' % str(last_value))
            if current_value > last_value:
                notification.title = 'change up!!! :)'
                notification.sound = 'wohoo.aiff'

        if notification:
            redis_set('brou:value', str(current_value))

        return [notification]

    def get_current_rates(self):
        res = {}
        self.driver.get('http://brou.com.uy/web/guest/institucional/cotizaciones')
        while True:
            try:
                table = self.driver.find_element_by_xpath('//table[@title="Cotizaciones"]')
                break
            except:
                time.sleep(0.5)

        for row in table.find_elements_by_xpath('.//tr'):
            cols = row.find_elements_by_xpath('.//td')
            if len(cols) > 1:
                res[unidecode(cols[1].text)] = {
                    'buy': Decimal(cols[2].text) if cols[2].text else None,
                    'sell': Decimal(cols[3].text) if cols[3].text else None
                }
        return res
