__author__ = "Pavel Samodurov"
__version__ = "1.0.1"
__email__ = "psamodurov13@gmail.com"

from selenium_webdriver import *
from loguru import logger
import json


logger.add('debug.log', level='INFO', format='{time} {level} {message}', compression='zip', rotation='15MB')


@logger.catch
def main(name, birthday):
    logger.info(f'Запуск функции main')
    res, rucaptcha_count, rucaptcha_time = load_website(name, birthday)
    final_result = {'result': res}
    logger.info(f'Final result - {final_result}')
    if type(final_result['result']) == list:
        final_result['done'] = 1
    else:
        if final_result['result'] == 'Извините, что-то пошло не так. Попробуйте позже':
            final_result['error'] = 'Извините, что-то пошло не так. Попробуйте позже'
            final_result['result'] = "Сервис не отвечает"
            final_result['done'] = 0
        if final_result['result'] == 'Код ответа 503':
            final_result['result'] = "Сервис не отвечает"
            final_result['error'] = 'Код ответа 503'
            final_result['done'] = 0
        elif final_result['result'].startswith('Сервис не отвечает'):
            final_result['error'] = final_result['result'].split('/ ')[-1]
            final_result['result'] = "Сервис не отвечает"
            final_result['done'] = 0
        elif final_result['result'].startswith("Непредвиденный заголовок H4"):
            final_result['result'] = final_result['result'].split('/ ')[-1]
            final_result['error'] = "Непредвиденный заголовок H4"
            final_result['done'] = 0
        elif final_result['result']:
            final_result['done'] = 1
        else:
            final_result['result'] = 'Ошибка при загрузке страницы'
            final_result['error'] = "Не удолось обойти каптчу"
            final_result['done'] = 0
    if rucaptcha_count:
        final_result['rucaptcha_count'] = rucaptcha_count
    if rucaptcha_time:
        final_result['rucaptcha_time'] = rucaptcha_time
    with open('result.json', 'w', encoding='utf-8') as file:
        json.dump(final_result, file, indent=4, ensure_ascii=False)
    return final_result


if __name__ == '__main__':
    # name = 'киселев максим сергеевич'
    # birthday = '02.03.1987'
    # name = 'киселев максим сергеевич'
    # birthday = '02.03.1987'
    name = 'Самодуров Павел Сергеевич'
    birthday = '26.06.1991'
    a = main(name, birthday)
    print(a)
