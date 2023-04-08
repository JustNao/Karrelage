import re

from src.entities.effects import effects, idToEffect
from src.entities.item import items
from src.entities.utils import kamasToString
from .base import DofusModule
import keyboard
import json


class HDVFilter(DofusModule):
    # HDV Equipement Filter

    def __init__(self) -> None:
        self.item = None
        self.bids = []
        self.releventBids = []
        self.filter = {}
        self.position = 0
        keyboard.on_press_key("right", self.nextBid)
        keyboard.on_press_key("left", self.previousBid)

    def fullEffect(self, effectId):
        fullEffect = idToEffect[effectId]["description"]
        displayEffectRaw = re.split(r"[ {}~%#]", fullEffect)
        displayEffect = []
        for split in displayEffectRaw:
            if len(split) > 2 or split in ("PA", "PM"):
                displayEffect.append(split)
        if "%" in fullEffect:
            displayEffect.append("(%)")
        elif "Résistance" in fullEffect:
            displayEffect.append("(Fixe)")
        return " ".join(map(str, displayEffect))

    def reset(self):
        self.item = None
        self.bids = []
        self.releventBids = []
        self.filter = {}

    def nextBid(self, _):
        if len(self.releventBids) > 0:
            self.position = (self.position + 1) % len(self.releventBids)
            self.get_bid(self.position)

    def previousBid(self, _):
        if len(self.releventBids) > 0:
            self.position = (self.position - 1) % len(self.releventBids)
            self.get_bid(self.position)

    def get_bid(self, index):
        if len(self.releventBids) == 0:
            return [], 0

        bid = self.releventBids[index]

        effects = []
        price = kamasToString(bid["prices"][0])

        for effectId, effect in self.item["effects"].items():
            result = {}
            # Required because for PA and PM, the min and max are inverted
            result["min"] = min(effect["max"], effect["min"])
            result["max"] = max(effect["max"], effect["min"])

            result["name"] = effect["type"]
            result["exo"] = False

            found = False
            for bidEffect in bid["effects"]:
                if bidEffect["actionId"] == effectId:
                    found = True
                    result["operator"] = effect["operator"]
                    result["over"] = bidEffect["value"] - max(
                        effect["max"], effect["min"]
                    )
                    if effect["max"] < effect["min"]:
                        result["value"] = min([bidEffect["value"], effect["min"]])
                    else:
                        result["value"] = min([bidEffect["value"], effect["max"]])

                    break

            # If the effect is not found, it means it's 0
            if not found:
                result["operator"] = effect["operator"]
                result["over"] = 0
                result["value"] = 0

            effects.append(result)

        # EXO
        for bidEffect in bid["effects"]:
            found = False

            if bidEffect["actionId"] in (985, 988, 1151, 1176):
                # Item modifié par XX
                # Item fabriqué par XX
                # Apparence modifiée
                # Apparence modifiée²
                continue

            for effectId, effect in self.item["effects"].items():
                if bidEffect["actionId"] == effectId:
                    found = True
                    break
            if not found and "value" in bidEffect and bidEffect["value"] > 0:
                effects.append(
                    {
                        "name": self.fullEffect(bidEffect["actionId"]),
                        "value": bidEffect["value"],
                        "operator": "+",
                        "over": 0,
                        "exo": True,
                        "min": 0,
                        "max": 0,
                    }
                )

        return effects, price

    def filterBids(self, filt):
        self.releventBids = []
        self.filter = {}
        for effect in filt:
            if filt[effect] != "":
                self.filter[int(effect)] = filt[effect]
        characFilter = {}
        for effect, value in filt.items():
            if value != "" and value != "0" and int(effect) not in characFilter:
                characFilter[int(effect)] = {
                    "value": int(value),
                    "diff": 0,
                }

        for bid in self.bids:
            valid = True
            for effect in characFilter:
                if not valid:
                    break
                found = False
                for packetEffect in bid["effects"]:
                    if packetEffect["actionId"] == effect:
                        found = True
                        if packetEffect["value"] < (
                            characFilter[effect]["value"] - characFilter[effect]["diff"]
                        ):
                            valid = False
                            break
                if not found:
                    valid = False
            if valid:
                self.releventBids.append(bid)

        self.releventBids.sort(key=lambda x: x["prices"][0])

    def handle_ExchangeTypesItemsExchangerDescriptionForUserMessage(self, packet):
        """Triggered when the user clicks on an item in the HDV"""

        self.reset()
        self.item = items[packet["objectGID"]]
        for bid in packet["itemTypeDescriptions"]:
            self.bids.append(bid)
        print("Found", len(self.bids), "bids for", self.item["name"])

        self.item["effects"] = {}
        for effect in self.item["possibleEffects"]:
            operator = effects(effect["effectId"])["operator"]
            if operator != "null":
                self.item["effects"][effect["effectId"]] = {
                    "min": effect["diceNum"],
                    "max": effect["diceSide"],
                    "type": self.fullEffect(effect["effectId"]),
                    "operator": operator,
                }
