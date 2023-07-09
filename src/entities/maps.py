from .utils import load

mapPositions = load("MapPositions")
mapToPositions_dict = {map["id"]: (map["posX"], map["posY"]) for map in mapPositions}
del mapPositions


def mapToPositions(map_id: float) -> tuple[int, int]:
    try:
        return mapToPositions_dict[map_id]
    except KeyError:
        print("Couldn't identify", map_id)
        return 0, 0
