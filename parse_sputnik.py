
import argparse
import json
import re
from pathlib import Path
from typing import Iterable, List, Dict, Optional, Tuple, Set
import sys # Import sys to get command line arguments

import requests
from bs4 import BeautifulSoup

# Страница станции из задания
STATION_URL = "https://www.tutu.ru/station.php?nnst=45807&date=all"

DAY_KEYWORDS = ["ежедневно", "будни", "выходные"]
TRAIN_PREFIXES = ["Электричка", "Спутник", "Иволга", "Ласточка"]


def fetch_html_from_web(url: str = STATION_URL) -> str:
    """Скачивает HTML-страницу с расписанием."""
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    # tutu часто отдает cp1251 — используем apparent_encoding
    response.encoding = response.apparent_encoding or "utf-8"
    return response.text


def read_html_from_file(path: Path) -> str:
    """Читает HTML из локального файла."""
    return path.read_text(encoding="utf-8")


def clean_route(text: str) -> str:
    """
    Очищает строку с маршрутом:
    - убирает тип поезда (Электричка, Спутник, ...),
    - убирает слова про дни следования,
    - убирает хвостовой номер поезда,
    - схлопывает лишние пробелы.
    """
    result = text.strip()

    for prefix in TRAIN_PREFIXES:
        if result.startswith(prefix):
            result = result[len(prefix):].lstrip()

    for key in DAY_KEYWORDS:
        result = re.sub(key, "", result, flags=re.IGNORECASE)

    # Убираем цифры в конце строки (номер поезда)
    result = re.sub(r"\d+\s*$", "", result)

    # Схлопываем пробелы
    result = re.sub(r"\s+", " ", result)

    # Убираем лишние пробелы/знаки по краям, но оставляем дефис между станциями
    return result.strip(" ,")


def extract_time(texts: Iterable[str]) -> Optional[str]:
    #Достаёт время отправления формата HH:MM из списка текстов.
    for t in texts:
        match = re.search(r"\b\d{2}:\d{2}\b", t)
        if match:
            return match.group(0)
    return None


def extract_days(texts: Iterable[str]) -> str:
    # Определяет тип дней (ежедневно, будни, выходные)
    for t in texts:
        lowered = t.lower()
        for key in DAY_KEYWORDS:
            if key in lowered:
                return key
    return ""


def extract_route(texts: Iterable[str]) -> Optional[str]:

    #Ищет строку с маршрутом — первую строку, где есть тире/дефис между станциями.
  
    for t in texts:
        if "—" in t or "–" in t or "-" in t:
            route = clean_route(t)
            if route:
                return route
    return None


def parse_schedule_from_html(html: str, day_filter: Optional[str] = None) -> List[Dict[str, str]]:
    """Разбирает HTML и возвращает список рейсов."""
    soup = BeautifulSoup(html, "lxml")
    rows = soup.find_all("tr")

    results: List[Dict[str, str]] = []
    seen: Set[Tuple[str, str, str]] = set()

    for row in rows:
        cols = row.find_all("td")
        if not cols:
            continue

        texts = [col.get_text(" ", strip=True) for col in cols if col.get_text(strip=True)]
        if not texts:
            continue

        time = extract_time(texts)
        if not time:
            continue

        days = extract_days(texts)

        if day_filter and days != day_filter:
            # Если фильтр задан, но тип дней не совпадает — пропускаем рейс
            continue

        route = extract_route(texts)
        if not route:
            continue

        key = (time, route, days)
        if key in seen:
            # Защита от дублей в разметке
            continue
        seen.add(key)

        results.append(
            {
                "time": time,
                "route": route,
                "days": days,
            }
        )

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Парсер расписания электричек с tutu.ru "
            "для станции https://www.tutu.ru/station.php?nnst=45807"
        )
    )
    parser.add_argument(
        "--days",
        choices=["будни", "ежедневно"],
        help="Фильтр по типу дней (будни / ежедневно). Если не указан — показать все рейсы.",
    )
    parser.add_argument(
        "--file",
        type=str,
        help=(
            "Путь к локальному HTML-файлу со страницей tutu.ru. "
            "Если не указан, страница будет скачана с сайта."
        ),
    )
    parser.add_argument(
        "--output",
        type=str,
        default="schedule.json",
        help="Имя JSON-файла для сохранения результата (по умолчанию schedule.json).",
    )


    args, unknown = parser.parse_known_args()

    if args.file:
        html = read_html_from_file(Path(args.file))
    else:
        html = fetch_html_from_web()

    schedule = parse_schedule_from_html(html, day_filter=args.days)

    # Вывод в консоль (по строке на рейс)
    for trip in schedule:
        print(f"{trip['time']} | {trip['route']} | {trip['days']}")

    # Сохранение в JSON
    output_path = Path(args.output)
    output_path.write_text(
        json.dumps(schedule, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
