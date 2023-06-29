from flask import Flask, jsonify
import json
from main import *

app = Flask(__name__)
# app.config['JSON_AS_ASCII'] = False

@app.route('/')
def index():
    return """<p>Сервис для получения данных о задолженностях с сайта ФССП РФ.</p>
<p>Структура запроса http://185.185.71.35:{PORT}/get_info/api/v1.0/{name}/{birthday}/{token}/.</p>
<p>Метод GET.</p>
<p>{PORT} - по умолчанию 5001. В зависимости от настроек nginx или мэпинга портов при запуске Docker контейнера, может отличаться</p>
<p>{name} - 'Фамилия Имя Отчество' (пример - 'Иванов Иван Иванович').</p>
<p>{birthday} - дата рождения в формате 'дд.мм.гггг' (пример - '01.01.1990').</p>
<p>{token} - токен</p>
<br>
<p>Структура ответа:</p>
<ul>
<li><p>в случае наличия задолженностей - </p>
<p>{"result": [{</p>
<p>      "debtor_name": "КИСЕЛЕВ МАКСИМ СЕРГЕЕВИЧ ",</p>
<p>      "debtor_address": "РЕСП. ДАГЕСТАН, Г. МАХАЧКАЛА",</p>
<p>      "debtor_dob": "02.03.1987 ",</p>
<p>      "process_title": "142062/23/26039-ИП",</p>
<p>      "process_date": "12.05.2023",</p>
<p>      "process_total": "",</p>
<p>      "document_title": "Судебный приказ от 14.08.2017 № 2-467-29-513/2017",</p>
<p>      "document_type": "Судебный приказ",</p>
<p>      "document_num": "2-467-29-513/2017",</p>
<p>      "document_date": "14.08.2017",</p>
<p>      "document_organization": "СУДЕБНЫЙ УЧАСТОК № 4 ПЕТРОВСКОГО РАЙОНА СТАВРОПОЛЬСКОГО КРАЯ",</p>
<p>      "document_claimer_inn": "7735057951",</p>
<p>      "subjects": [</p>
<p>        {</p>
<p>          "title": "Задолженность по кредитным платежам (кроме ипотеки)",</p>
<p>          "sum": "58297.07 руб."</p>
<p>        }</p>
<p>      ],</p>
<p>      "department_title": "Промышленный районный отдел судебных приставов города Ставрополя",</p>
<p>      "department_address": "355037, Россия, Ставропольский край, , г. Ставрополь, , ул. Шпаковская, 107, А,",</p>
<p>      "officer_name": "КУРБАНОВ М. К.",</p>
<p>      "officer_phones": [</p>
<p>        "+7(8652)25-81-91"</p>
<p>      ]}],</p>
<p>  "done": 1}</p>
</li>
<li><p>в случае отсутствия задолженностей - {"result": "Задолженностей нет", "done": 1}</p></li>
<li><p>в случае ошибки на сайте ФССП РФ - {"result": "Сервис не отвечает", "done": 0}</p></li>
"""


@app.route('/get_info/api/v1.0/<name>/<birthday>/<token>/')
def get_info(name, birthday, token):
    logger.info(f'Старт обработки запроса {name}, {birthday}')
    with open('token.txt', 'r') as file:
        api_token = file.read()
        logger.info(f'API TOKEN - {api_token}')
    logger.info(f'TOKEN - {token}')
    if token == api_token:
        logger.info('TOKEN TRUE')
        result = main(name, birthday)
    else:
        logger.info('TOKEN FALSE')
        result = {'result': 'Ошибка аутентификации', 'done': 0}
    return json.dumps(result, ensure_ascii=False)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
    # app.run()
