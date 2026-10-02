import json
import secrets
import string
import time

import requests

from datetime import datetime
from pathlib import Path


URL = "https://players.pokemon-card.com/event_search"

# 大阪府
PREFECTURE_ID = 27

# APIは1ページ20件
PAGE_SIZE = 20


def generate_terminal_id():
    alphabet = string.ascii_letters + string.digits

    return "".join(
        secrets.choice(alphabet)
        for _ in range(100)
    )


def fetch_events():
    terminal_id = generate_terminal_id()

    headers = {
        "Accept": "application/json, text/plain, */*",

        "Referer": (
            "https://players.pokemon-card.com/event/search"
            "?prefecture[]=27"
            "&offset=0"
            "&order=1"
        ),

        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/154.0.0.0 Safari/537.36"
        ),

        "x-accept-version": "v1",
        "x-terminal-id": terminal_id,
    }

    events = []
    offset = 0
    total_count = None

    while True:
        params = {
            "prefecture[]": PREFECTURE_ID,
            "offset": offset,
            "order": 1,
        }

        response = requests.get(
            URL,
            params=params,
            headers=headers,
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        if total_count is None:
            total_count = data.get(
                "eventCount",
                0,
            )

            print(
                f"API上の大会件数: "
                f"{total_count}件"
            )

            print()

        page_events = data.get(
            "event",
            [],
        )

        if not page_events:
            break

        events.extend(
            page_events
        )

        print(
            f"取得中: "
            f"{len(events)}"
            f" / "
            f"{total_count}件"
        )

        # 全件取得できた
        if (
            total_count
            and len(events) >= total_count
        ):
            break

        # 最終ページ
        if len(page_events) < PAGE_SIZE:
            break

        offset += PAGE_SIZE

        # APIへの負荷を抑える
        time.sleep(0.5)

    return events


def create_source_url(event):
    """
    ポケモンカード公式の大会詳細URLを生成する。

    確認したURL形式:
    /event/detail/
    {event_holding_id}/
    1/
    {shop_id}/
    {event_date_params}/
    {date_id}
    """

    return (
        "https://players.pokemon-card.com/event/detail/"
        f"{event['event_holding_id']}/"
        f"1/"
        f"{event['shop_id']}/"
        f"{event['event_date_params']}/"
        f"{event['date_id']}"
    )


def normalize_event(event):
    date_params = str(
        event["event_date_params"]
    )

    event_date = datetime.strptime(
        date_params,
        "%Y%m%d",
    ).strftime("%Y-%m-%d")

    return {
        "id":
            f"pokemon-{event['date_id']}",

        "game":
            "pokemon",

        "event_name":
            event.get("event_title"),

        "date":
            event_date,

        "start_time":
            event.get(
                "event_started_at"
            ),

        "end_time":
            event.get(
                "event_ended_at"
            ),

        "shop_name":
            event.get("shop_name"),

        "prefecture":
            event.get(
                "prefecture_name"
            ),

        "address":
            event.get("address"),

        "capacity":
            event.get("capacity"),

        "entry_fee":
            event.get("entry_fee"),

        "regulation":
            event.get("regulation"),

        "distance":
            event.get("distance"),

        "full":
            bool(
                event.get(
                    "fullOccupiedFlg",
                    0,
                )
            ),

        "cancelled":
            bool(
                event.get(
                    "cancelFlg",
                    0,
                )
            ),

        # 公式大会詳細ページ
        "source_url":
            create_source_url(event),
    }


def main():
    print(
        "ポケモン大会を取得します"
    )

    print(
        "対象: 大阪府全域"
    )

    print()

    raw_events = fetch_events()

    print()

    print(
        f"取得完了: "
        f"{len(raw_events)}件"
    )

    events = [
        normalize_event(event)
        for event in raw_events
    ]

    output = {
        "updated_at":
            datetime
            .now()
            .astimezone()
            .isoformat(),

        "events":
            events,
    }

    output_path = Path(
        "data/pokemon.json"
    )

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

    print(
        f"保存先: "
        f"{output_path}"
    )


if __name__ == "__main__":
    main()