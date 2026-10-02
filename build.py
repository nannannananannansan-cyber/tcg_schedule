import json
from datetime import datetime
from pathlib import Path


DATA_DIR = Path("data")

POKEMON_FILE = DATA_DIR / "pokemon.json"
LORCANA_FILE = DATA_DIR / "lorcana.json"
TONAMEL_POKEMON_FILE = DATA_DIR / "tonamel_pokemon.json"

OUTPUT_FILE = Path("docs/data/events.json")


def load_events(path):
    with path.open(
        "r",
        encoding="utf-8",
    ) as f:
        data = json.load(f)

    return data["events"]


def add_source(events, source):
    """
    sourceが未設定のイベントに情報ソースを設定する。
    """

    for event in events:
        if not event.get("source"):
            event["source"] = source

    return events


def main():
    pokemon_events = load_events(
        POKEMON_FILE
    )

    lorcana_events = load_events(
        LORCANA_FILE
    )

    tonamel_pokemon_events = load_events(
        TONAMEL_POKEMON_FILE
    )


    # 公式サイト由来
    pokemon_events = add_source(
        pokemon_events,
        "official",
    )

    lorcana_events = add_source(
        lorcana_events,
        "official",
    )

    # Tonamel側はtonamel.pyですでに
    # source=tonamel が設定されているが、
    # 念のため未設定の場合にも補完する
    tonamel_pokemon_events = add_source(
        tonamel_pokemon_events,
        "tonamel",
    )


    print(
        f"ポケモン公式: "
        f"{len(pokemon_events)}件"
    )

    print(
        f"ロルカナ公式: "
        f"{len(lorcana_events)}件"
    )

    print(
        f"ポケモン Tonamel: "
        f"{len(tonamel_pokemon_events)}件"
    )


    events = (
        pokemon_events
        + lorcana_events
        + tonamel_pokemon_events
    )


    events.sort(
        key=lambda event: (
            event["date"],
            event["start_time"] or "",
            event.get("event_name", ""),
        )
    )


    output = {
        "updated_at":
            datetime
            .now()
            .astimezone()
            .isoformat(),

        "event_count":
            len(events),

        "events":
            events,
    }


    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


    with OUTPUT_FILE.open(
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
        f"合計: "
        f"{len(events)}件"
    )

    print(
        f"保存先: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()