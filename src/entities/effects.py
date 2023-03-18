from .utils import load
from .i18n import i18n

effectsJs = load("Effects")


def effects(id):
    for effect in effectsJs:
        if effect["id"] == id:
            return {
                "operator": effect["operator"],
                "reliquat": effect["effectPowerRate"],
            }
    return None


idToEffect = {}
for effect in effectsJs:
    try:
        idToEffect[effect["id"]] = {
            "operator": effect["operator"],
            "description": i18n["texts"][str(effect["descriptionId"])],
            "characteristic": effect["characteristic"],
        }
    except KeyError:
        pass
