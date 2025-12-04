# Парсер расписания электричек (tutu.ru)

Скрипт `train_schedule.py` парсит расписание электричек со страницы станции  
[`https://www.tutu.ru/station.php?nnst=45807&date=all`](https://www.tutu.ru/station.php?nnst=45807&date=all).

Он:
- берёт HTML со страницы (или из локального файла);
- для каждого рейса извлекает **время**, **маршрут** и **тип дней** (`ежедневно`, `будни`, `выходные`);
- убирает дубликаты;
- выводит рейсы в консоль и сохраняет их в JSON.

---

Запуск

Базовый формат:

python train_schedule.py [--days будни|ежедневно] [--file ПУТЬ_К_HTML] [--output ИМЯ_JSON]

Примеры:

# Все рейсы, HTML берётся с сайта, вывод + schedule.json
python train_schedule.py

# Только рейсы по будням
python train_schedule.py --days будни

# Парсинг сохранённого файла station.html
python train_schedule.py --file station.html

# Только ежедневные рейсы, результат в daily_trains.json
python train_schedule.py --days ежедневно --output daily_trains.json

Пример вывода

09:15 | Москва Ярославская — Сергиев Посад | будни
10:05 | Москва Ярославская — Александров | ежедневно

Результат в JSON — список объектов вида:

{
  "time": "09:15",
  "route": "Москва Ярославская — Сергиев Посад",
  "days": "будни"
}
