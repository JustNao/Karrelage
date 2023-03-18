from .utils import load
from .i18n import i18n

textId = load("textId")
monsterJs = load("Monsters")


def monsterToName(id):
    try:
        nameId = [obj for obj in monsterJs if obj["id"] == id][0]["nameId"]
        name = i18n["texts"][str(nameId)]
        return name
    except KeyError:
        print("Couldn't identify", id)
        return ""
