from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
from webdriver_manager.chrome import ChromeDriverManager
import time
import requests as rq
import base64
from config import *
import json
from loguru import logger
from bs4 import BeautifulSoup as bs
from pprint import pprint



options = Options()
options.add_argument('headless')
options.add_argument('--no-sandbox')
# options.add_argument(f'--proxy-server=194.67.202.81:9138')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.maximize_window()

options.add_argument(f'user-agent={headers["User-Agent"]}')


def check_tag_exists(selector):
    try:
        driver.find_element(By.CSS_SELECTOR, selector)
    except NoSuchElementException:
        return False
    return True


def bypass_captcha(drv: webdriver.Chrome):
    count = 1
    logger.info(f'Запущена функция bypass_captcha')
    while True:
        logger.info(f'Попытка расшифровки капчи {count}')
        try:
            captcha_img = drv.find_element(By.CSS_SELECTOR, '#capchaVisual')
        except Exception:
            logger.debug(f'Капча не найдена - {Exception}')
            break
        src = captcha_img.get_attribute('src').replace('data:image/jpeg;base64,', '')
        answer = rq.post(
            f"https://rucaptcha.com/in.php",
            json={"key": API_KEY, "method": "base64", "body": src, "json": 1, "lang": "ru"},
        )
        logger.info(f'Запрос в рукаптча отправлен')
        task_id = json.loads(answer.text)['request']
        logger.info(f'TASK ID - {task_id}')
        while True:
            time.sleep(3)
            task_answer = rq.get(
                f"https://rucaptcha.com/res.php?key={API_KEY}&action=get&id={task_id}&json=1"
            )
            result = json.loads(task_answer.text)
            status = result['status']
            if status == 1:
                count += 1
                try:
                    logger.info('Получен ответ от RuCaptcha')
                    captcha = json.loads(task_answer.text)['request']
                    if drv.find_element(By.CSS_SELECTOR, '#capchaVisual').get_attribute('src').replace('data:image/jpeg;base64,', '') == src:
                        captcha_field = driver.find_element(By.CSS_SELECTOR, '#captcha-popup-code')
                        captcha_field.send_keys(captcha)
                        time.sleep(0.1)
                        send_captcha_button = driver.find_element(By.CSS_SELECTOR, '#ncapcha-submit')
                        send_captcha_button.click()
                        time.sleep(3)
                        logger.info('Каптча отправлена')
                        break
                    else:
                        logger.info('Каптча сменилась')
                        break
                except Exception:
                    logger.error(f'Неизвестная ошибка {Exception}')
                    logger.exception(f'Неизвестная ошибка')
                    break
            else:
                logger.info('Ответ от RuCaptcha еще не получен')
                continue


def collect_results(source: webdriver.Chrome.page_source):
    with open('index.html', 'w') as file:
        file.write(source)
    soup = bs(source, 'html.parser')
    table = soup.select_one('.results-frame tbody')
    region_rows = table.select('tr.region-title')
    for i in range(len(region_rows)):
        table.select_one('tr.region-title').decompose()
    br_tags = table.find_all('br')
    for i in range(len(br_tags)):
        table.select_one('br').decompose()
    rows = table.find_all('tr')[1:]
    # logger.info(f'ROWS2 - {[i.text for i in rows]}')
    # logger.info(f'LEN ROWS2 - {len(rows)}')
    results_from_page = []
    for row in rows:
        debtor_info = row.select_one('td.first')
        # br_count = len(debtor_info.find_all('br'))
        # for i in range(br_count):
        #     a.find('br').decompose()
        logger.info(f'DEBTOR INFO {debtor_info}')
        debtor_info_results = [i.text for i in debtor_info]
        debtor_name = debtor_info_results[0]
        debtor_dob = debtor_info_results[1]
        if len(debtor_info_results) > 2:
            debtor_address = debtor_info_results[2]
        else:
            debtor_address = ''
        process_info = list(row.select_one('td:nth-child(2)').children)
        # logger.info(f'PROCCESS - {process_info}, {type(process_info)}')
        process_title, process_date = process_info[0].split(' от ')
        if len(process_info) > 1:
            process_total = process_info[1].text
        else:
            process_total = ''
        document_info = list(row.select_one('td:nth-child(3)').children)
        document_title = document_info[0].text
        document_type = document_title.split(' от ')[0]
        document_num = document_title.split(' № ')[-1]
        document_date = document_title.split(' от ')[1].split(' № ')[0]
        if len(document_info) == 3:
            document_organization = document_info[1].text
            document_claimer_inn = document_info[2].text
        elif len(document_info) == 4:
            document_organization = document_info[2].text
            document_claimer_inn = document_info[3].text
        else:
            document_organization = ''
            document_claimer_inn = ''
            logger.debug(f'!!!LEN DOCUMENT INFO {len(document_info)} {document_info}')

        subject_info = list(row.select_one('td:nth-child(6)').children)
        subjects = []
        for subject in subject_info:
            subject_parameters = subject.text.split(': ')
            if len(subject_parameters) == 1:
                subjects.append(
                    {
                        'title': subject_parameters[0],
                        'sum': ''
                    }
                )
            elif len(subject_parameters) == 2:
                subjects.append(
                    {
                        'title': subject_parameters[0],
                        'sum': subject_parameters[1]
                    }
                )

        department_info = list(row.select_one('td:nth-child(7)').children)

        department_title = department_info[0].text
        department_address = department_info[1].text

        officer_info = list(row.select_one('td:nth-child(8)').children)
        officer_name = officer_info[0].text
        officer_phones = [officer_info[1].text]

        single_result = {'debtor_name': debtor_name, 'debtor_address': debtor_address, 'debtor_dob': debtor_dob,
                         'process_title': process_title, 'process_date': process_date, 'process_total': process_total,
                         'document_title': document_title, 'document_type': document_type, 'document_num': document_num,
                         'document_date': document_date, 'document_organization': document_organization,
                         'document_claimer_inn': document_claimer_inn, 'subjects': subjects,
                         'department_title': department_title, 'department_address': department_address,
                         'officer_name': officer_name, 'officer_phones': officer_phones
                         }
        results_from_page.append(single_result)
        # print(f'LEN - {len(list(debtor_info.children))}')
        # print(f'RES - {[s.text for s in debtor_info.children]}')
        # print('-' * 10)

    pprint(results_from_page)
    return results_from_page


def load_website(name, birthday):
    try:
        driver.get('https://old.fssp.gov.ru')
        logger.info(f'Главная страница загружена')
        logger.info(driver.page_source[:100])
        if '<title>503 Service Temporarily Unavailable</title>' in driver.page_source:
            logger.info(f'Обнаружен 503 код ответа')
            return 'Код ответа 503'
        if 'Извините, что-то пошло не так. Попробуйте позже' in driver.page_source:
            logger.info(f'Обноружено сообщение "Извините, что-то пошло не так. Попробуйте позже"')
            return 'Извините, что-то пошло не так. Попробуйте позже'
        time.sleep(5)
        # ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        close_try = 0
        while True:
            try:
                close_button = driver.find_element(By.CSS_SELECTOR, '.tingle-modal__closeIcon')
                close_button.click()
                break
            except NoSuchElementException:
                logger.info('Всплывающее окно не появилось')
                close_try += 1
                if close_try == 5:
                    break
                else:
                    driver.get('https://old.fssp.gov.ru')
                    time.sleep(5)
            except ElementNotInteractableException:
                logger.info('не удалось закрыть окно')
                close_try += 1
                if close_try == 5:
                    break
                else:
                    driver.get('https://old.fssp.gov.ru')
                    time.sleep(5)
        logger.info(f'Закрыт попап')
        time.sleep(2)
        more_fields_button = driver.find_element(By.CSS_SELECTOR, '.main-form__btns .btn-light')
        more_fields_button.click()
        logger.info(f'Раскрыты доп поля')
        time.sleep(1)
        f_name, surname, father_name = name.split(' ')
        name_field = driver.find_element(By.CSS_SELECTOR, 'input[name="is[first_name]"]')
        name_field.send_keys(f_name)
        logger.info(f'Заполнено имя')
        time.sleep(2)
        surname_field = driver.find_element(By.CSS_SELECTOR, 'input[name="is[last_name]"]')
        surname_field.send_keys(surname)
        logger.info(f'Заполнена фамилия')
        time.sleep(2)
        birthday_field = driver.find_element(By.CSS_SELECTOR, 'input[name="is[date]"]')
        birthday_field.send_keys(birthday)
        logger.info(f'Заполнена дата рождения')
        time.sleep(2)
        father_name_field = driver.find_element(By.CSS_SELECTOR, 'input[name="is[patronymic]"]')
        father_name_field.send_keys(father_name)
        logger.info(f'Заполнено отчество')
        # ActionChains(driver).send_keys(Keys.TAB)
        # ActionChains(driver).send_keys(Keys.TAB)
        # ActionChains(driver).send_keys(Keys.TAB)
        birthday_field.send_keys(Keys.RETURN)

        time.sleep(2)
        logger.info(f'Форма отправлена')
        page = 1
        result = []
        while True:
            logger.info(f'Запущен цикл обхода страниц')
            bypass_captcha(driver)
            if page == 1 and check_tag_exists('.results h4'):
                message = driver.find_element(By.CSS_SELECTOR, '.results h4').text
                if message == 'По вашему запросу ничего не найдено':
                    logger.info('Задолженностей нет')
                    return 'Задолженностей нет'
                else:
                    logger.info(f'Непредвиденный h4 {message}')
                    return f'Непредвиденный заголовок H4 / {message}'
            elif page == 1 and check_tag_exists('.results .empty'):
                message = driver.find_element(By.CSS_SELECTOR, '.results .empty').text
                if message == 'Извините, что-то пошло не так. Попробуйте позже':
                    logger.info('Извините, что-то пошло не так. Попробуйте позже')
                    return 'Извините, что-то пошло не так. Попробуйте позже'
                else:
                    logger.info(f'Непредвиденный div .empty {message}')
                    return f'Непредвиденный div .empty / {message}'
            if check_tag_exists('.results-frame'):
                logger.info(f'Переход на страницу {page}')
                result.extend(collect_results(driver.page_source))
                if check_tag_exists('.pagination .context a:last-child'):
                    next_page_button = driver.find_element(By.CSS_SELECTOR, '.pagination .context a:last-child')
                    next_page_button.click()
                    time.sleep(5)
                    page += 1
                else:
                    logger.debug(f'Нет следующей страницы')
                    break
            else:
                logger.debug(f'Нет результатов')
                break
        time.sleep(10)
    except Exception as exception:
        logger.exception(Exception)
        print("Exception: {}".format(type(exception).__name__))
        print("Exception message: {}".format(exception))
        result = f'Сервис не отвечает / {type(exception).__name__}'
    return result


if __name__ == '__main__':
    load_website('аббасов мамед магарлам', '18.09.1992')
