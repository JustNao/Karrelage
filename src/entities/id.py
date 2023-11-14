from .utils import load
from .i18n import i18n

monsterJs = load("Monsters")
poiJs = load("PointOfInterest")
poi_dict = {}
for poi in poiJs:
    poi_dict[poi["id"]] = poi["nameId"]


def get_monster_name(id: int):
    """Returns the name of a monster from its id"""
    try:
        nameId = [obj for obj in monsterJs if obj["id"] == id][0]["nameId"]
        name = i18n["texts"][str(nameId)]
        return name
    except KeyError:
        print("Couldn't identify", id)
        return ""


def get_poi_name(id):
    """Returns the name of a point of interest from its id"""
    if id in poi_dict:
        return i18n["texts"][str(poi_dict[id])]
    raise ValueError("Unknown poi id", id)
