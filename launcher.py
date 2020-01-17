import os
import json


config = json.load(open(r'build\config.json', 'r'))

try:
    while True:
        answer = input('Вводить ключи доступа к API? (да/нет): ')
        if answer == 'да' or answer == '+':
            config['access_key'] = input('Введите access_key: ')
            config['secret_key'] = input('Введите secret_key: ')
            json.dump(config, open(r'build\config.json', 'w'), indent=2)
            break
        elif answer == 'нет' or answer == '-':
            if (config['access_key'] != '') and (config['secret_key'] != ''):
                break
            else:
                print('Ключи не введены')
                continue
        else:
            print('Введите ответ (да или нет)')
            continue

    if os.system(r'build\main.exe') == 1:
        if os.system(r'main.py') == 1:
            os.system(r'build\main.py')
        
except FileNotFoundError:
    print('ОШИБКА Отсутствуют необходимые файлы')

input('~~~')
