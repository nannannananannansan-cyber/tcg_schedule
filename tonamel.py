import json
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests


BASE_URL = "https://tonamel.com"

SEARCH_URL = (
    "https://tonamel.com/competitions"
    "?game=pokemon_card"
    "&region=JP"
    "&nt=0"
    "&sr=%E5%A4%A7%E9%98%AA"
)

CSRF_URL = "https://tonamel.com/api/csrf_token"

GRAPHQL_URL = (
    "https://tonamel.com/graphql/"
    "competition_management"
)

GAME_ID = "pokemon_card"

# 大阪府
OSAKA_PREFECTURE_ID = (
    "cmVnaW9uUHJlZmVjdHVyZS8yNw"
)

OUTPUT_PATH = Path(
    "data/tonamel_pokemon.json"
)

PAGE_SIZE = 32

JST = ZoneInfo("Asia/Tokyo")


QUERY = """
query getPublicCompetitions(
  $condition: PublicCompetitionsCondition!,
  $filter: PublicCompetitionsFilter!
) {
  publicCompetitions(
    condition: $condition,
    filter: $filter
  ) {
    edges {
      cursor
      node {
        id
        title

        game {
          id
          name
        }

        organization {
          id
          name
        }

        status

        tournaments {
          id
          style
          status
          displayStartAt
          isOnline

          location {
            venueName

            address {
              input
            }
          }
        }

        entryMenus {
          id
          status
          title
          forParticipation
          participantChosenNum

          countSummary {
            currentEntrantNum
          }

          startAt
          endAt

          payment {
            price {
              price

              currency {
                type
                decimalPoint
              }
            }
          }
        }

        publicStatus
        region
      }
    }

    pageInfo {
      startCursor
      endCursor
      hasNextPage
      hasPreviousPage
    }
  }
}
"""


def get_today_timestamp():
    """
    今日の00:00 JSTをUnix timestampにする。
    """

    now = datetime.now(JST)

    today = datetime(
        now.year,
        now.month,
        now.day,
        tzinfo=JST,
    )

    return str(int(today.timestamp()))


def create_session():
    """
    Tonamelの匿名セッションを作成し、
    CSRFトークンを取得する。
    """

    session = requests.Session()

    session.headers.update(
        {
            "Accept": "*/*",
            "Accept-Language": (
                "ja,en-US;q=0.9,en;q=0.8"
            ),
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/154.0.0.0 "
                "Safari/537.36"
            ),
        }
    )

    print("Tonamel匿名セッション作成中")

    response = session.get(
        SEARCH_URL,
        timeout=30,
    )

    print(
        "  大会一覧:",
        response.status_code,
    )

    response.raise_for_status()

    print(
        "  Cookie数:",
        len(session.cookies),
    )

    print("CSRFトークン取得中")

    response = session.get(
        CSRF_URL,
        headers={
            "Referer": SEARCH_URL,
        },
        timeout=30,
    )

    print(
        "  CSRF:",
        response.status_code,
    )

    response.raise_for_status()

    data = response.json()

    csrf_token = data.get(
        "csrf_token"
    )

    if not csrf_token:
        raise RuntimeError(
            "CSRFトークンを取得できませんでした: "
            + json.dumps(
                data,
                ensure_ascii=False,
            )
        )

    print(
        "  CSRFトークン取得成功"
    )

    return session, csrf_token


def fetch_page(
    session,
    csrf_token,
    after="",
):
    payload = {
        "operationName": (
            "getPublicCompetitions"
        ),
        "variables": {
            "condition": {
                "gameId": GAME_ID,
                "startAfter": (
                    get_today_timestamp()
                ),
                "statuses": [],
                "onlineOrOffline": (
                    "OFFLINE"
                ),
                "region": "JP",
                "regionPrefectureIds": [
                    OSAKA_PREFECTURE_ID
                ],
            },
            "filter": {
                "first": PAGE_SIZE,
                "last": 0,
                "before": "",
                "after": after,
            },
        },
        "query": QUERY,
    }

    headers = {
        "Content-Type": (
            "application/json"
        ),
        "Origin": BASE_URL,
        "Referer": SEARCH_URL,
        "X-CSRF-Token": csrf_token,
        "X-Page-View-Location": (
            SEARCH_URL
        ),
    }

    response = session.post(
        GRAPHQL_URL,
        headers=headers,
        json=payload,
        timeout=30,
    )

    print(
        "HTTP:",
        response.status_code,
    )

    if not response.ok:
        print(
            "Response:",
            response.text[:1000],
        )

    response.raise_for_status()

    result = response.json()

    if result.get("errors"):
        raise RuntimeError(
            json.dumps(
                result["errors"],
                ensure_ascii=False,
                indent=2,
            )
        )

    return result


def fetch_all_competitions(
    session,
    csrf_token,
):
    competitions = []

    after = ""
    page = 1

    while True:
        print(
            f"Tonamel取得中: "
            f"{page}ページ目"
        )

        result = fetch_page(
            session,
            csrf_token,
            after,
        )

        public_competitions = (
            result["data"][
                "publicCompetitions"
            ]
        )

        edges = (
            public_competitions["edges"]
        )

        for edge in edges:
            node = edge.get("node")

            if node:
                competitions.append(
                    node
                )

        print(
            f"  {len(edges)}件取得"
            f" / 合計"
            f"{len(competitions)}件"
        )

        page_info = (
            public_competitions[
                "pageInfo"
            ]
        )

        if not page_info[
            "hasNextPage"
        ]:
            break

        after = page_info[
            "endCursor"
        ]

        if not after:
            break

        page += 1

        time.sleep(0.5)

    return competitions


def unix_to_datetime(timestamp):
    if not timestamp:
        return None

    return datetime.fromtimestamp(
        int(timestamp),
        tz=JST,
    )


def get_main_tournament(
    competition
):
    tournaments = (
        competition.get(
            "tournaments"
        )
        or []
    )

    if not tournaments:
        return None

    return tournaments[0]


def get_entry_menu(
    competition
):
    menus = (
        competition.get(
            "entryMenus"
        )
        or []
    )

    participation_menus = [
        menu
        for menu in menus
        if menu.get(
            "forParticipation"
        )
    ]

    if participation_menus:
        return (
            participation_menus[0]
        )

    if menus:
        return menus[0]

    return None


def get_entry_fee(entry_menu):
    if not entry_menu:
        return None

    payment = entry_menu.get(
        "payment"
    )

    if not payment:
        return None

    price_info = payment.get(
        "price"
    )

    if not price_info:
        return None

    price = price_info.get(
        "price"
    )

    if price is None:
        return None

    currency = (
        price_info
        .get(
            "currency",
            {},
        )
        .get("type")
    )

    if currency == "JPY":
        return f"{price}円"

    return str(price)


def is_full(entry_menu):
    if not entry_menu:
        return False

    capacity = entry_menu.get(
        "participantChosenNum"
    )

    count_summary = (
        entry_menu.get(
            "countSummary"
        )
        or {}
    )

    entrants = (
        count_summary.get(
            "currentEntrantNum"
        )
    )

    if (
        capacity is None
        or entrants is None
    ):
        return False

    return entrants >= capacity


def is_cancelled(
    competition,
    tournament,
):
    competition_status = (
        competition.get(
            "status"
        )
        or ""
    ).upper()

    tournament_status = (
        (
            tournament.get(
                "status"
            )
            if tournament
            else ""
        )
        or ""
    ).upper()

    cancelled_statuses = {
        "CANCELLED",
        "CANCELED",
    }

    return (
        competition_status
        in cancelled_statuses
        or
        tournament_status
        in cancelled_statuses
    )


def normalize_competition(
    competition
):
    tournament = (
        get_main_tournament(
            competition
        )
    )

    if not tournament:
        return None

    start_at = unix_to_datetime(
        tournament.get(
            "displayStartAt"
        )
    )

    if not start_at:
        return None

    location = (
        tournament.get(
            "location"
        )
        or {}
    )

    address_data = (
        location.get(
            "address"
        )
        or {}
    )

    entry_menu = get_entry_menu(
        competition
    )

    capacity = None
    entrants = None

    if entry_menu:
        capacity = (
            entry_menu.get(
                "participantChosenNum"
            )
        )

        entrants = (
            entry_menu
            .get(
                "countSummary",
                {},
            )
            .get(
                "currentEntrantNum"
            )
        )

    organization = (
        competition.get(
            "organization"
        )
        or {}
    )

    competition_id = (
        competition["id"]
    )

    return {
        "id": (
            f"tonamel-"
            f"{competition_id}"
        ),
        "game": "pokemon",
        "source": "tonamel",
        "event_name": (
            competition.get(
                "title"
            )
            or ""
        ),
        "date": (
            start_at.strftime(
                "%Y-%m-%d"
            )
        ),
        "start_time": (
            start_at.strftime(
                "%H:%M"
            )
        ),
        "end_time": "",
        "shop_name": (
            location.get(
                "venueName"
            )
            or
            organization.get(
                "name"
            )
            or
            ""
        ),
        "prefecture": "大阪府",
        "address": (
            address_data.get(
                "input"
            )
            or ""
        ),
        "capacity": capacity,
        "entrant_count": (
            entrants
        ),
        "entry_fee": (
            get_entry_fee(
                entry_menu
            )
        ),
        "regulation": None,
        "distance": None,
        "full": is_full(
            entry_menu
        ),
        "cancelled": (
            is_cancelled(
                competition,
                tournament,
            )
        ),
        "source_url": (
            "https://tonamel.com/"
            f"competition/"
            f"{competition_id}"
        ),
    }


def normalize_competitions(
    competitions
):
    events = []

    for competition in competitions:
        event = (
            normalize_competition(
                competition
            )
        )

        if event:
            events.append(event)

    events.sort(
        key=lambda event: (
            event["date"],
            event["start_time"],
            event["event_name"],
        )
    )

    return events


def save_events(events):
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = {
        "source": "tonamel",
        "game": "pokemon",
        "updated_at": (
            datetime
            .now(JST)
            .isoformat()
        ),
        "events": events,
    }

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )


def main():
    print(
        "Tonamel "
        "ポケモン大会取得開始"
    )

    session, csrf_token = (
        create_session()
    )

    competitions = (
        fetch_all_competitions(
            session,
            csrf_token,
        )
    )

    print()
    print(
        "取得完了:",
        f"{len(competitions)}件",
    )

    events = (
        normalize_competitions(
            competitions
        )
    )

    print(
        "正規化完了:",
        f"{len(events)}件",
    )

    save_events(events)

    print(
        "保存先:",
        OUTPUT_PATH,
    )


if __name__ == "__main__":
    main()