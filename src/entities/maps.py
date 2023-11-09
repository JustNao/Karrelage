from .utils import load

mapPositions = load("MapPositions")
mapToPositions_dict = {map["id"]: (map["posX"], map["posY"]) for map in mapPositions}
del mapPositions


def get_map_positions(map_id: int) -> tuple[int, int]:
    """Returns the position of a map from its id"""
    try:
        return mapToPositions_dict[map_id]
    except KeyError:
        print("Couldn't identify", map_id)
        return 0, 0
