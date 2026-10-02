import json
import re
import requests

from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
from pathlib import Path


URL = "https://www.takaratomy.co.jp/products/disneylorcana/event/search/"


def fetch_events():
    today = date.today()
    date_to = today + timedelta(days=31)

    params = {
        "category_event_search": "イベントを選択",
        "word": "",
        "prefecture": "大阪府",
        "date_from": today.strftime("%Y/%m/%d"),
        "date_to": date_to.strftime("%Y/%m/%d"),
        "anchor": "true",
        "submit": "search",
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/154.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(
        URL,
        params=params,
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    return soup.select(".p-event-search-accordion__list")


def normalize_event(event, index):
    # 大会名
    event_name = event.select_one("h5").get_text(strip=True)

    # 店舗名
    shop_name = event.select_one(
        ".p-event-search-accordion__area h6"
    ).get_text(strip=True)

    # 住所
    address_element = event.select_one(
        ".p-event-search-accordion__area-address"
    )

    address = address_element.get_text(
        " ",
        strip=True,
    )

    # 「MAP」を削除
    address = re.sub(r"\s*MAP$", "", address)

    # 郵便番号を削除
    address = re.sub(
        r"^〒\d{3}-\d{4}\s*",
        "",
        address,
    )

    # 日時
    datetime_text = event.select_one(
        ".p-event-search-accordion__toggle-date"
    ).get_text(strip=True)

    match = re.search(
        r"(\d{4})年(\d{2})月(\d{2})日"
        r"\([^)]+\)\s*(\d{2}:\d{2})",
        datetime_text,
    )

    if not match:
        raise ValueError(
            f"日時を解析できません: {datetime_text}"
        )

    year, month, day, start_time = match.groups()

    event_date = f"{year}-{month}-{day}"

    # 定員
    capacity_text = event.select_one(
        ".p-event-search-accordion__toggle-capacity"
    ).get_text(strip=True)

    capacity_match = re.search(
        r"(\d+)",
        capacity_text,
    )

    capacity = (
        int(capacity_match.group(1))
        if capacity_match
        else None
    )

    # 参加条件
    entry_fee = None

    rows = event.select(
        ".p-event-search-accordion__table tr"
    )

    for row in rows:
        cells = row.select("td")

        if len(cells) < 2:
            continue

        label = cells[0].get_text(
            " ",
            strip=True,
        )

        value = cells[1].get_text(
            " ",
            strip=True,
        )

        if label == "参加条件":
            entry_fee = value

    return {
        "id": f"lorcana-{event_date}-{index}",
        "game": "lorcana",
        "event_name": event_name,
        "date": event_date,
        "start_time": start_time,
        "end_time": None,
        "shop_name": shop_name,
        "prefecture": "大阪府",
        "address": address,
        "capacity": capacity,
        "entry_fee": entry_fee,
        "regulation": None,
        "distance": None,
        "full": False,
        "cancelled": False,
    }


def main():
    raw_events = fetch_events()

    print(f"取得: {len(raw_events)}件")

    events = []

    for index, event in enumerate(raw_events):
        normalized = normalize_event(
            event,
            index,
        )

        events.append(normalized)

    output = {
        "updated_at": datetime.now().astimezone().isoformat(),
        "events": events,
    }

    output_path = Path("data/lorcana.json")

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"完了: {len(events)}件")
    print(f"保存先: {output_path}")


if __name__ == "__main__":
    main()