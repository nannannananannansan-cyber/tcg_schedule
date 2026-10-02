import json
from datetime import datetime
from pathlib import Path


DATA_DIR = Path("data")

POKEMON_FILE = DATA_DIR / "pokemon.json"
LORCANA_FILE = DATA_DIR / "lorcana.json"

OUTPUT_FILE = Path("docs/data/events.json")


def load_events(path):
    with path.open(
        "r",
        encoding="utf-8",
    ) as f:
        data = json.load(f)

    return data["events"]


def main():
    pokemon_events = load_events(
        POKEMON_FILE
    )

    lorcana_events = load_events(
        LORCANA_FILE
    )


    print(
        f"ポケモン: "
        f"{len(pokemon_events)}件"
    )

    print(
        f"ロルカナ: "
        f"{len(lorcana_events)}件"
    )


    events = (
        pokemon_events +
        lorcana_events
    )


    events.sort(
        key=lambda event: (
            event["date"],
            event["start_time"] or "",
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