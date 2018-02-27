RunLoad - реализация консольного клиента для Yandex.Tank API.

**Установка**

- (Опционально -- если удобнее работать в отдельном окружении) Подготавливаем среду:

`virtualenv ~/work_clean
source ~/work_clean/bin/activate
pip install --upgrade pip`

- Ставим утилиту:

`PyPIHost=<PyPI with runload package>`

`pip install --trusted-host $PyPIHost --index-url http://$PyPIHost:8080/simple/ --upgrade runload`

**Запуск**

Пример удаленного запуска через `runload` (также утилитой подхватыватывается конфиг вида common.ini, если он существует в текущей директории):

`runload -p load_remote.ini -s <tank-server> -r 8888`

**Наблюдение**

Во время теста результаты можно смотреть, например, по порту 8001 на соответствующей нагрузочной станции (хост из ключа `-s` при запуске `runload`; порт должен быть указан в опции `port` секции `[sputnikonline]` ini файла):
- http://\<tank-server\>:8001
