from math import ceil, floor
from .base import DofusModule
from src.entities.utils import load
from src.entities.item import item
from src.entities.effects import effects


class Item:
    def __init__(self, init_packet, reliquat=0) -> None:
        self.reliquat = reliquat
        self.effects = init_packet["object"]["effects"]
        self.GID = init_packet["object"]["objectGID"]
        self.UID = init_packet["object"]["objectUID"]

    def update_effects(self, new_effects):
        differences = {}
        for new_effect in new_effects:
            found_new_effect = False
            for old_effect in self.effects:
                if old_effect["actionId"] == new_effect["actionId"]:
                    found_new_effect = True
                    if isinstance(old_effect["value"], str):
                        # Skipping "modified by PLAYER"
                        break
                    differences[old_effect["actionId"]] = (
                        old_effect["value"] - new_effect["value"]
                    )

                    break
            if not found_new_effect:
                differences[new_effect["actionId"]] = -1 * new_effect["value"]

        # Handling stats that were removed
        new_effect_ids = [effect["actionId"] for effect in new_effects]
        for old_effect in self.effects:
            if old_effect["actionId"] not in new_effect_ids:
                differences[old_effect["actionId"]] = old_effect["value"]

        self.effects = new_effects
        return differences

    def update_reliquat(self, reliquat):
        self.reliquat += reliquat
        self.reliquat = min(self.reliquat, 99)


class Forgemager(DofusModule):
    def __init__(self) -> None:
        self.runes = load("runes")
        self.item = None
        self.current_rune = None

    def add_rune(self, packet):
        self.current_rune = {
            "actionId": packet["object"]["effects"][0]["actionId"],
            "value": packet["object"]["effects"][0]["value"],
            "GID": str(packet["object"]["objectGID"]),
        }

    def compute_reliquat(self, updates):
        reliquat = 0
        for key, value in updates.items():
            effect = effects(key)
            reliquat += value * effect["reliquat"]
        reliquat = round(reliquat, 2)
        return reliquat

    def get_item(self):
        if self.item is None:
            return None, None, None

        name = item(self.item.GID)["name"]
        if self.item.reliquat < 0:
            reliquat = ceil(self.item.reliquat)
        else:
            reliquat = floor(self.item.reliquat)
        level = item(self.item.GID)["level"]
        return name, reliquat, level

    def update(self, update_data):
        self.item.update_reliquat(int(update_data))

    def handle_ExchangeObjectAddedMessage(self, packet):
        """Triggered when an item is added to the workshop, both item
        and runes.
        """
        if str(packet["object"]["objectGID"]) in self.runes:
            self.add_rune(packet)
        else:
            self.item = Item(packet)

    def handle_ExchangeCraftResultMagicWithObjectDescMessage(self, packet):
        """Triggered when the item is updated."""
        if self.item is None:
            print("Please load the item first")
            return

        differences = self.item.update_effects(packet["objectInfo"]["effects"])
        reliquat = self.compute_reliquat(differences)
        if packet["magicPoolStatus"] != 1:
            if packet["craftResult"] == 1:
                # Used rune won't shop up in the updated effects
                # So we need to add it manually
                reliquat += -1 * self.runes[self.current_rune["GID"]]["poids"]
            self.item.update_reliquat(reliquat)
