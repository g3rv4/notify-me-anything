from events.base_event_raiser import BaseEventRaiser
from decimal import Decimal
from unidecode import unidecode
from utils import redis_get, redis_set
from notifications.base_notification import Notification
import time


class BROUEventRaiser(BaseEventRaiser):
    def __init__(self):
        self.messages = {
            'open': ('Brou exchange started operations', 'New value: {new_value_real} - {new_value}', 'Old value: {old_value_real} - {old_value}', "NSUserNotificationDefaultSoundName"),
            'closed': ('Brou exchange finished operations', 'New value: {new_value_real} - {new_value}', 'Old value: {old_value_real} - {old_value}', "NSUserNotificationDefaultSoundName")
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
        if not rates:
            return []

        current_value = rates['Dolar e-Brou'][args.value_to_check]
        current_value_real = rates['Dolar'][args.value_to_check]
        try:
            last_value = Decimal(redis_get('brou:value'))
        except:
            last_value = Decimal('0')
        try:
            last_value_real = Decimal(redis_get('brou:value_real'))
        except:
            last_value_real = Decimal('0')

        status = 'open' if rates['Dolar e-Brou']['buy'] - rates['Dolar']['buy'] > Decimal('0.10') else 'closed'
        last_status = redis_get('brou:status')

        real_variation = current_value_real - last_value_real
        variation = current_value - last_value

        notifications = []
        if not args.avoid_open_notification and (not last_status or last_status != status):
            notifications.append('market_status')
        if abs(real_variation) >= args.small_delta:
            notifications.append('real')
        elif abs(variation) >= args.small_delta and 'market_status' not in notifications:
            notifications.append('ebrou')

        res = []
        if 'market_status' in notifications:
            # notify status change
            notification = Notification(*[v.format(new_value=str(current_value),
                                                   new_value_real=str(current_value_real),
                                                   old_value=str(last_value),
                                                   old_value_real=str(last_value_real)) if v else None
                                          for v in self.messages[status]])
            if len(notifications) > 1:
                notification.sound = None

            redis_set('brou:status', status)
            notifications.remove('market_status')
            res.append(notification)

        if len(notifications):
            notification = None
            variation = real_variation if 'real' in notifications else variation

            if args.big_delta and abs(variation) >= args.big_delta:
                notification = Notification(title='BIG CHANGE DOWN :(', subtitle='New value: %s - %s' % (str(current_value_real), str(current_value)),
                                            sound='sad', text='Old value: %s - %s' % (str(last_value_real), str(last_value)))
                if variation > 0:
                    notification.title = 'BIG CHANGE UP!!! :)'
                    notification.sound = 'perere'
            elif abs(variation) >= args.small_delta:
                notification = Notification(title='change down :(', subtitle='New value: %s - %s' % (str(current_value_real), str(current_value)),
                                            sound='boo', text='Old value: %s - %s' % (str(last_value_real), str(last_value)))
                if variation > 0:
                    notification.title = 'change up!!! :)'
                    notification.sound = 'wohoo'

            if 'real' not in notifications:
                notification.sound = None

            res.append(notification)

        if len([n for n in res if n]):
            redis_set('brou:value', str(current_value))
            redis_set('brou:value_real', str(current_value_real))

        return res

    def get_current_rates(self):
        res = {}
        urls = ['http://brou.com.uy/web/guest/home', 'http://brou.com.uy/web/guest/institucional/cotizaciones']
        i = 0
        while not len(res) and i < len(urls):
            self.driver.get(urls[i % len(urls)])
            i += 1

            attempts = 0
            table = None
            while True:
                try:
                    table = self.driver.find_element_by_xpath('//table[@title="Cotizaciones"]')
                    break
                except:
                    time.sleep(0.5)
                    attempts += 1
                    if len(attempts) >= 10:
                        break

            if table:
                for row in table.find_elements_by_xpath('.//tr'):
                    cols = row.find_elements_by_xpath('.//td')
                    if len(cols) > 1:
                        res[unidecode(cols[1].text).replace('\n', ' ')] = {
                            'buy': Decimal(cols[2].text) if cols[2].text else None,
                            'sell': Decimal(cols[3].text) if cols[3].text else None
                        }
        return res
