import json
import gzip


def load(file):
    with gzip.open(
        f"src/entities/gameRessources/{file}.json.gz", "rt", encoding="utf-8"
    ) as f:
        return json.load(f)


def kamasToString(price: int):
    return f"{price:,}"
