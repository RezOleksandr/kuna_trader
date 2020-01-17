import requests
import json
import kuna.kuna as kuna
from time import *

# Курсы валют предоставлены https://www.minfin.com.ua/currency/ и https://api.privatbank.ua

print("Курсы валют предоставлены https://www.minfin.com.ua/currency/ и https://api.privatbank.ua\n")

config = json.load(open(r'build\config.json', 'r'))

while True:
    try:
        config['buy_volume'] = float(input('Введите обьем ордера для покупки: '))
        config['sell_volume'] = float(input('Введите обьем ордера для продажи: '))
        config['currency_rate_change_percent'] = float(input("Введите процент на который увеличивается/уменшается курс валют(базовое знчение 0.5): ")) / 100
        buy_volume = config['buy_volume']
        sell_volume = config['sell_volume']
        json.dump(config, open(r'build\config.json', 'w'), indent=2)
        break
    except ValueError:
        print('ОШИБКА Введенные данные должны быть числами')
    except Exception:
        print('ОШИБКА Произошла неизвестная ошибка')
        input('Завершение работы >>>...')
        raise SystemExit

MARKET_1 = 'usdtuah'
MARKET_2 = 'tusduah'

graph_kuna = kuna.KunaAPI(access_key=config['keys']['access_key'],
                          secret_key=config['keys']['secret_key'])

PRIVAT_CURRENCY_RATE_REQUEST = 'https://api.privatbank.ua/p24api/pubinfo?exchange&json&coursid=11'
MINFIN_CURRENCY_RATE_REQUEST = 'http://api.minfin.com.ua/summary/0e5bb35206edff8a21758a054172ca3dc08c1d4c/'


def put_buy_order(market, volume, buy_rate, target_order=None):
    users_active_orders = graph_kuna.get_orders(market)
    all_active_buy_orders: list = requests.request('GET', 'https://kuna.io/api/v2/depth', params={'market': f'{market}'}).json()['bids']
    all_active_buy_orders.sort(key=lambda order1: -float(order1[0]))
    market_buy_rate = round(float(all_active_buy_orders[0][0]), 2)
    buy_config = json.load(open(r'build\config.json', 'r'))
    for active_buy_order in all_active_buy_orders[1:]:
        if float(active_buy_order[1]) >= 100:
            market_buy_rate = round(float(active_buy_order[0]) + 0.01, 2)
            break
    for users_active_order in users_active_orders:
        if target_order is not None and users_active_order['id'] == target_order['id']:
            price = round(float(all_active_buy_orders[1][0]) + 0.01, 2)
            for active_buy_order in all_active_buy_orders[1:]:
                if float(active_buy_order[1]) >= 100:
                    price = round(float(active_buy_order[0]) + 0.01, 2)
                    break   
            if round(float(target_order['price']), 2) != round(buy_rate, 2) and (round(buy_rate, 2) <= round(market_buy_rate, 2)):
                try:
                    graph_kuna.cancel_order(target_order['id'])
                    order = graph_kuna.put_order(side='buy', volume=volume, market=market, price=round(buy_rate, 2))
                    print(f"Заменён на покупку ордер на сумму {volume} на рынок {market} по цене {round(buy_rate, 2)}")
                    buy_config['orders_placement_time'][market] = time()
                    json.dump(buy_config, open(r'build\config.json', 'w'), indent=1)
                    return order
                except kuna.APIError:
                    print(
                        f'ОШИБКА Ошибка при замене ордера на покупку на сумму {volume} на рынок {market} по цене {buy_rate}')
                    return None
            elif round(buy_rate, 2) > round(market_buy_rate, 2) and round(float(target_order['price']), 2) != round(price, 2):
                try:
                    graph_kuna.cancel_order(target_order['id'])
                    print(buy_volume, market, price)
                    order = graph_kuna.put_order(side='buy', volume=volume, market=market, price=round(price, 2))
                    print(f"Заменён на покупку ордер на сумму {volume} на рынок {market} по цене {round(price, 2)}")
                    buy_config['orders_placement_time'][market] = time()
                    json.dump(buy_config, open(r'build\config.json', 'w'), indent=1)
                    return order
                except kuna.APIError:
                    print(
                        f'ОШИБКА Ошибка при замене ордера на покупку на сумму {volume} на рынок {market} по цене {round(buy_rate, 2)}')
                    return None
            elif time() - buy_config["orders_placement_time"][market] > 7200:
                print(time())
                print(buy_config["orders_placement_time"][market])
                graph_kuna.cancel_order(target_order['id'])
                order = graph_kuna.put_order(side='buy', volume=volume, market=market, price=round(float(target_order['price']), 2))
                print(f"Заменён на покупку ордер на сумму {volume} на рынок {market} по цене {round(float(target_order['price']), 2)}, причина - ордер активен более 2-х часов")
                buy_config['orders_placement_time'][market] = time()
                json.dump(buy_config, open(r'build\config.json', 'w'), indent=1)
                return order
            else:
                print(f'Ордер на покупку на рынке {market} уже выставлен')
                return target_order
    if round(buy_rate, 2) <= round(market_buy_rate, 2):
        try:
            order = graph_kuna.put_order(side='buy', volume=volume, market=market, price=round(buy_rate, 2))
            print(f'Выставлен на покупку ордер на сумму {volume} на рынок {market} по цене {round(buy_rate, 2)}')
            buy_config['orders_placement_time'][market] = time()
            json.dump(buy_config, open(r'build\config.json', 'w'), indent=1)
        except kuna.APIError:
            print(f'ОШИБКА Ошибка при выставлении ордера на покупку на сумму {volume}'
                  f' на рынок {market} по цене {round(buy_rate, 2)}')
            order = None
    else:
        price = round(float(market_buy_rate) + 0.01, 2)
        for active_buy_order in all_active_buy_orders:
            if float(active_buy_order[1]) >= 100:
                price = round(float(active_buy_order[0]) + 0.01, 2)
                break
        try:
            order = graph_kuna.put_order(side='buy', volume=volume, market=market, price=round(price, 2))
            print(f"Выставлен на покупку ордер на сумму {volume} на рынок {market} по цене {round(price, 2)}")
            buy_config['orders_placement_time'][market] = time()
            json.dump(buy_config, open(r'build\config.json', 'w'), indent=1)
        except kuna.APIError:
            print(
                f'ОШИБКА Ошибка при выставлении ордера на покупку на сумму {volume} на рынок {market} по цене {round(buy_rate, 2)}')
            order = None
    return order


def put_sale_order(market, volume, sell_rate, target_order=None):
    users_active_orders = graph_kuna.get_orders(market)
    all_active_sell_orders: list = requests.request('GET', 'https://kuna.io/api/v2/depth', params={'market': f'{market}'}).json()['asks']
    all_active_sell_orders.sort(key=lambda order1: float(order1[0]))
    market_sell_rate = round(float(all_active_sell_orders[0][0]), 2)
    sale_config = json.load(open(r'build\config.json', 'r'))
    for active_sell_order in all_active_sell_orders[1:]:
        if float(active_sell_order[1]) >= 100:
            market_sell_rate = round(float(active_sell_order[0]) - 0.01, 2)
            break
    for users_active_order in users_active_orders:
        if target_order is not None and users_active_order['id'] == target_order['id']:
            price = round(float(all_active_sell_orders[1][0]) - 0.01, 2)
            for active_buy_order in all_active_sell_orders[1:]:
                if float(active_buy_order[1]) >= 100:
                    price = round(float(active_buy_order[0]) - 0.01, 2)
                    break
            if round(float(target_order['price']), 2) != round(sell_rate, 2) and (round(sell_rate, 2) >= round(market_sell_rate, 2)):
                try:
                    graph_kuna.cancel_order(target_order['id'])
                    order = graph_kuna.put_order(side='sell', volume=volume, market=market, price=round(sell_rate, 2))
                    print(f"Заменён на продажу ордер на сумму {volume} на рынок {market} по цене {round(sell_rate, 2)}")
                    sale_config['orders_placement_time'][market] = time()
                    json.dump(sale_config, open(r'build\config.json', 'w'), indent=1)
                    return order
                except kuna.APIError:
                    print(f'ОШИБКА Ошибка при замене ордера на покупку на сумму {volume} на рынок {market} по цене {sell_rate}')
                    return None
            elif round(sell_rate, 2) < round(market_sell_rate, 2) and round(float(users_active_order['price']), 2) != round(price, 2):
                try:
                    graph_kuna.cancel_order(target_order['id'])
                    order = graph_kuna.put_order(side='sell', volume=volume, market=market, price=round(price, 2))
                    print(f"Заменён на покупку ордер на сумму {volume} на рынок {market} по цене {round(price, 2)}")
                    sale_config['orders_placement_time'][market] = time()
                    json.dump(sale_config, open(r'build\config.json', 'w'), indent=1)
                    return order
                except kuna.APIError:
                    print(f'ОШИБКА Ошибка при замене ордера на покупку на сумму {volume} на рынок {market} по цене {round(sell_rate, 2)}')
                    return None
            elif time() - sale_config["orders_placement_time"][market] > 7200:
                graph_kuna.cancel_order(target_order['id'])
                order = graph_kuna.put_order(side='sell', volume=volume, market=market, price=round(float(target_order['price']), 2))
                print(f"Заменён на продажу ордер на сумму {volume} на рынок {market} по цене {round(float(target_order['price']), 2)}")
                sale_config['orders_placement_time'][market] = time()
                json.dump(sale_config, open(r'build\config.json', 'w'), indent=1)
                return order
            else:
                print(f'Ордер на продажу на рынке {market} уже выставлен')
                return target_order

    if round(sell_rate, 2) >= round(market_sell_rate, 2):
        try:
            order = graph_kuna.put_order(side='sell', volume=volume, market=market, price=round(sell_rate, 2))
            print(f'Выставлен на продажу ордер на сумму {volume} на рынок {market} по цене {round(sell_rate, 2)}')
            sale_config['orders_placement_time'][market] = time()
            json.dump(sale_config, open(r'build\config.json', 'w'), indent=1)
        except kuna.APIError:
            print(f'ОШИБКА Ошибка при выставлении ордера на покупку на сумму {volume} на рынок {market} по цене {round(sell_rate, 2)}')
            order = None
    else:
        price = round(float(market_sell_rate) - 0.01, 2)
        for active_buy_order in all_active_sell_orders:
            if float(active_buy_order[1]) >= 100:
                price = round(float(active_buy_order[0]) - 0.01, 2)
                break
        try:
            order = graph_kuna.put_order(side='sell', volume=volume, market=market, price=round(price, 2))
            print(f"Выставлен на продажу ордер на сумму {volume} на рынок {market} по цене {round(price, 2)}")
            sale_config['orders_placement_time'][market] = time()
            json.dump(sale_config, open(r'build\config.json', 'w'), indent=1)
        except kuna.APIError:
            print(
                f'ОШИБКА Ошибка при выставлении ордера на покупку на сумму {volume} на рынок {market} по цене {round(sell_rate, 2)}')
            order = None
    return order


buy_order1 = None
sale_order1 = None

market1_state = 'buy'

for placement_time in config['orders_placement_time']:
    config['orders_placement_time'][placement_time] = 0
json.dump(config, open(r'build\config.json', 'w'), indent=1)

is_first_loop = True

try:
    while True:
        try:
            privat_currency_rate = requests.get(PRIVAT_CURRENCY_RATE_REQUEST).json()[0]
        except requests.exceptions.ConnectionError:
            print('ОШИБКА Ошибка получения курса валют ПриватБанка, повторный запрос через 20 секунд')
            sleep(20)
            continue

        config = json.load(open(r'build\config.json', 'r'))

        if is_first_loop:
            try:
                minfin_currency_rate = requests.get(MINFIN_CURRENCY_RATE_REQUEST).json()['usd']
                config['minfin_values']['last_check'] = time()
                config['minfin_values']['buy_rate'] = round(float(minfin_currency_rate['bid']), 2)
                config['minfin_values']['sell_rate'] = round(float(minfin_currency_rate['ask']), 2)
                json.dump(config, open(r'build\config.json', 'w'), indent=1)
                is_first_loop = False
            except requests.exceptions.ConnectionError:
                print('ОШИБКА Ошибка получения курса валют МИНФИНа, повторный запрос через 5 минут')
                is_first_loop = False
                sleep(300)
                continue
        else:
            if time() - config['minfin_values']['last_check'] > 300:
                try:
                    minfin_currency_rate = requests.get(MINFIN_CURRENCY_RATE_REQUEST).json()['usd']
                    config['minfin_values']['last_check'] = time()
                    config['minfin_values']['buy_rate'] = round(float(minfin_currency_rate['bid']), 2)
                    config['minfin_values']['sell_rate'] = round(float(minfin_currency_rate['ask']), 2)
                    json.dump(config, open(r'build\config.json', 'w'), indent=1)
                except requests.exceptions.ConnectionError:
                    print('ОШИБКА Ошибка получения курса валют МИНФИНа, повторный запрос через 5 минут')
                    sleep(300)
                    continue

        minfin_buy_rate = round(float(config['minfin_values']['buy_rate']))
        minfin_sell_rate = round(float(config['minfin_values']['sell_rate']))

        privat_buy_rate = round(float(privat_currency_rate['buy']), 2)
        target_buy_rate = round(privat_buy_rate - privat_buy_rate * config['currency_rate_change_percent'], 2)
        privat_sell_rate = round(float(privat_currency_rate['sale']), 2)
        target_sell_rate = round(privat_sell_rate + privat_sell_rate * config['currency_rate_change_percent'], 2)

        if abs(minfin_buy_rate / privat_buy_rate - 1) > 0.03:
            print('Слишком большая разница между курсами Приватбанка и МИНФИНА, повтор запроса через 5 минут')
            sleep(300)
            continue
        elif abs(minfin_sell_rate / privat_sell_rate - 1) > 0.03:
            print('Слишком большая разница между курсами Приватбанка и МИНФИНА, повтор запроса через 5 минут')
            sleep(300)
            continue

        buy_trade1_complete = False
        if (buy_order1 is not None) and (market1_state == 'buy'):
            buy_trade1_complete = True
            sale_trade1_complete = False
            active_orders1 = graph_kuna.get_orders(MARKET_1)
            for active_order1 in active_orders1:
                if active_order1['market'] == MARKET_1:
                    if active_order1['side'] == 'buy' and active_order1['id'] == buy_order1['id']:
                        buy_trade1_complete = False
                        sale_trade1_complete = True
                        break

        sale_trade1_complete = False
        if (sale_order1 is not None) and (market1_state == 'sell'):
            sale_trade1_complete = True
            buy_trade1_complete = False
            active_orders1 = graph_kuna.get_orders(MARKET_1)
            for active_order1 in active_orders1:
                if active_order1['market'] == MARKET_1:
                    if active_order1['side'] == 'sell' and active_order1['id'] == sale_order1['id']:
                        sale_trade1_complete = False
                        buy_trade1_complete = True
                        break

        if buy_trade1_complete and market1_state == 'buy':
            market1_state = 'sell'
            buy_order1 = None

        if sale_trade1_complete and market1_state == 'sell':
            market1_state = 'buy'
            sale_order1 = None

        if market1_state == 'buy':
            if buy_order1 is not None and config['buy_volume'] != buy_volume:
                graph_kuna.cancel_order(buy_order1['id'])
                buy_order1 = put_buy_order(MARKET_1, round(config['buy_volume'], 2), round(target_buy_rate, 2), buy_order1)

            else:
                buy_order1 = put_buy_order(MARKET_1, round(config['buy_volume'], 2), round(target_buy_rate, 2), buy_order1)

        else:
            if sale_order1 is not None and config['sell_volume'] != sell_volume:
                graph_kuna.cancel_order(sale_order1['id'])
                sale_order1 = put_sale_order(MARKET_1, round(config['sell_volume'], 2), round(target_sell_rate, 2), sale_order1)
            else:
                sale_order1 = put_sale_order(MARKET_1, round(config['sell_volume'], 2), round(target_sell_rate, 2), sale_order1)

        buy_volume = config['buy_volume']
        sell_volume = config['sell_volume']
        sleep(20)

except EOFError:
    print('ОШИБКА Возникла неизвестная критическая ошибка')

input('Завершение работы >>>...')
