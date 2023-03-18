import json
import sys
import os
from .utils import load
from .i18n import i18n

statsJSON = load("Characteristics")

idToStat = {}
for stat in statsJSON:
    try:
        idToStat[stat["id"]] = {
            "description": i18n["texts"][str(stat["nameId"])],
            "order": stat["order"],
        }
    except KeyError:
        pass
