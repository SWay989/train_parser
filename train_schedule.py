import requests
from bs4 import BeautifulSoup
import json
import re

DAY_KEYWORDS = ["ежедневно", "будни", "выходные"]

def fetch_html(url):
    resp = requests.get(url)
    resp.encoding = resp.apparent_encoding
    return resp.text

def clean_route(text):

    # Убираем названия поездов
    for prefix in ["Электричка", "Спутник", "Иволга", "Ласточка"]:
        if text.startswith(prefix):
            text = text[len(prefix):]

    # Убираем ключевые слова дней
    for key in DAY_KEYWORDS:
        text = re.sub(key, "", text, flags=re.IGNORECASE)

    # Убираем номера поездов в конце
    text = re.sub(r'\d+$', '', text)

    # Убираем лишние пробелы
    return text.strip()

def parse_schedule_from_html(html, day_filter=None):
    soup = BeautifulSoup(html, "lxml")
    results = []

    rows = soup.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if not cols:
            continue
        texts = [td.get_text(strip=True) for td in cols if td.get_text(strip=True)]
        if not texts:
            continue

        # Ищем время
        time = None
        for t in texts:
            match = re.match(r"\d{2}:\d{2}", t)
            if match:
                time = match.group()
                break
        if not time:
            continue

        # Ищем день рейса
        days = ""
        for key in DAY_KEYWORDS:
            for t in texts:
                if key.lower() in t.lower():
                    days = key.lower()
                    break
            if days:
                break

        if day_filter and days != day_filter:
            continue

        # Ищем маршрут — первую колонку с дефисом/тире
        route = ""
        for t in texts:
            if '—' in t or '–' in t:
                route = clean_route(t)
                break
        if not route:
            continue

        results.append({
            "time": time,
            "route": route,
            "days": days
        })
    return results

if __name__ == "__main__":
    url = "https://www.tutu.ru/station.php?nnst=45807&date=all"
    html = fetch_html(url)

    # day_filter = "будни" / "ежедневно" / None
    schedule = parse_schedule_from_html(html, day_filter=None)

    for trip in schedule:
        print(f"{trip['time']} | {trip['route']} | {trip['days']}")

    with open("schedule.json", "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)
