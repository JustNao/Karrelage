import json
import gzip


def load(file):
    with gzip.open(
        f"src/entities/gameRessources/{file}.json.gz", "rt", encoding="utf-8"
    ) as f:
        return json.load(f)


def save(data, file):
    with gzip.open(
        f"src/entities/gameRessources/{file}.gz", "wt", encoding="utf-8"
    ) as f:
        json.dump(data, f)


def kamasToString(price: int):
    return f"{price:,}"
