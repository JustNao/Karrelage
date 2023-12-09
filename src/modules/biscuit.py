import pyperclip
import json
import os
import requests as rq
import keyboard as kb
import win32gui as w32
from datetime import datetime, timezone
from dateutil import parser, relativedelta

from .base import DofusModule
from utils.data import load_dat
from src.entities.utils import load, kamasToString
from src.entities.id import get_monster_name
from src.entities.media import play_sound
from src.entities.maps import get_map_positions
from src.utils.externals import Vulbis
from src.entities.item import get_recipe
from src.entities.i18n import id_to_name


class Commander:
    def __init__(self):
        self.commands = {
            "enutrosor": lambda _, channel: self.portals("enutrosor", channel),
            "srambad": lambda _, channel: self.portals("srambad", channel),
            "xelorium": lambda _, channel: self.portals("xelorium", channel),
            "ecaflipus": lambda _, channel: self.portals("ecaflipus", channel),
            "price": lambda packet, channel: self.price(packet, channel),
            "regen": lambda _, channel: self.regen(channel),
            "almanax": lambda _, channel: self.almanax(channel),
        }
        self.channels = {
            2: "/g",
            4: "/p",
        }
        local_prices = load_dat("itemAveragePrices")
        if not "Draconiros" in local_prices:
            print("Local prices for Draconiros not found, $price command will not work")
            self.local_prices = None
        else:
            self.local_prices = local_prices["Draconiros"]["items"]

    def send_message(self, message):
        pyperclip.copy(message)
        kb.press_and_release("ctrl+v")
        kb.press_and_release("enter")

    def portals(self, zone: str, channel: int):
        zone_id = {
            "ecaflipus": 0,
            "enutrosor": 1,
            "srambad": 2,
            "xelorium": 3,
        }

        request = rq.get(
            "https://api.dofus-portals.fr/internal/v1/servers/draconiros/portals"
        )
        portals = request.json()
        relevent_portal = portals[zone_id[zone]]
        try:
            pos_x, pos_y = (
                relevent_portal["position"]["x"],
                relevent_portal["position"]["y"],
            )
            try:
                time_str = relevent_portal["createdAt"]
            except KeyError:
                time_str = relevent_portal["updatedAt"]
            given_time = parser.isoparse(time_str)
            current_time = datetime.now(timezone.utc)
            time_diff = relativedelta.relativedelta(current_time, given_time)
            time_diff_str = (
                f"{time_diff.minutes} minutes"
                if time_diff.hours == 0
                else f"{time_diff.hours} heures et {time_diff.minutes} minutes"
            )
            remaining_uses = relevent_portal["remainingUses"]
            self.send_message(
                f"{self.channels[channel]} Portail {zone} dernièrement vu en [{pos_x},{pos_y}] il y'a {time_diff_str} (avec {remaining_uses} utilisations)"
            )
        except KeyError:
            pos_x, pos_y, time = Vulbis.get_portal_positions(zone)
            self.send_message(
                f"{self.channels[channel]} Portail {zone} dernièrement vu en [{pos_x},{pos_y}] il y'a {time}"
            )

    def get_craft_price(self, item_id: int):
        if not self.local_prices:
            return None

        recipe = get_recipe(item_id)
        if not recipe:
            return self.local_prices[str(item_id)]

        total_price = 0
        for ingredient_id, quantity in zip(
            recipe["ingredientIds"], recipe["quantities"]
        ):
            total_price += self.get_craft_price(ingredient_id) * quantity

        return total_price

    def price(self, packet, channel: int):
        gid = packet["objects"][0]["objectGID"]
        price = self.get_craft_price(gid)
        if not price:
            self.send_message(
                f"{self.channels[channel]} Prix de craft : inconnu. Un des items n'est pas dans la base de données"
            )
            return
        self.send_message(
            f"{self.channels[channel]} Prix de craft estimé : {kamasToString(price)} K"
        )

    def regen(self, channel):
        items = load("Items")
        if not self.local_prices:
            return None

        best_ratio = 666.0
        best_item = None
        best_ratio_craft = 666.0
        best_item_craft = None
        for item in items:
            if item["usable"]:
                if len(item["possibleEffects"]) == 1:
                    effect = item["possibleEffects"][0]
                    if effect["effectId"] == 110:
                        if not str(item["id"]) in self.local_prices:
                            continue
                        item_price = self.local_prices[str(item["id"])]
                        craft_price = self.get_craft_price(item["id"])
                        mean_regen = (
                            float(effect["diceNum"]) + float(effect["diceSide"]) / 2
                        )
                        if mean_regen < 50:
                            continue
                        ratio = float(item_price) / mean_regen
                        if ratio < best_ratio:
                            best_ratio = ratio
                            best_item = item
                        if craft_price:
                            ratio_craft = float(craft_price) / mean_regen
                            if ratio_craft < best_ratio_craft:
                                best_ratio_craft = ratio_craft
                                best_item_craft = item
        if not best_item:
            self.send_message(
                f"{self.channels[channel]} Erreur, aucun item trouvé avec l'effet de régénération de vie"
            )
            return
        item_name = id_to_name(best_item["nameId"])
        msg = f"{self.channels[channel]} Meilleur ratio prix/vie : {item_name} ({best_ratio:.1f} K/vie)"
        if best_item_craft and best_ratio_craft < best_ratio:
            msg += f". Un craft de {item_name} est plus rentable, avec {best_ratio_craft:.1f} K/vie"
        self.send_message(msg)

    def almanax(self, channel):
        data = {
            "action": "wpda_datatables",
            "wpnonce": "ddf53adf5f",
            "pubid": 8,
        }
        response = rq.post(
            "https://www.gamosaurus.com/wp-admin/admin-ajax.php", data=data
        )
        if response.status_code != 200:
            self.send_message(
                f"{self.channels[channel]} Erreur, impossible de récupérer les données de l'almanax"
            )
            return
        formatted_response = response.json()
        offrande, reward, bonus = formatted_response["data"][0]
        self.send_message(
            f"{self.channels[channel]} Offrande du jour : {offrande}. Récompense : {reward}K. Bonus : {bonus}"
        )


class Biscuit(DofusModule):
    # Quality of Life assistant

    def __init__(self) -> None:
        self.reset()
        self.load_config()
        self.load_data()
        self.archimonstres = load("Archi")

    def reset(self):
        self.commander = Commander()
        self.config = {
            "commands": True,
            "archimonstres": True,
            "houses": True,
        }
        self.houses = []

    def load_config(self):
        with open("config/biscuit.json") as f:
            self.config = self.config | json.load(f)

    def load_data(self):
        if os.path.exists("config/abandonned_houses.txt"):
            with open("config/abandonned_houses.txt", "r") as f:
                positions = f.readlines()
                self.houses = [pos.strip() for pos in positions]

    def save_config(self):
        with open("config/biscuit.json", "w") as f:
            json.dump(self.config, f, indent=4)

    def update(self, data: str):
        key, value = data.split(":")

        # If the value is empty, its a toggle
        if value == "null":
            self.config[key] = not self.config[key]
        else:
            self.config[key] = bool(value)

        self.save_config()

    def save_abandonned_house(self, map_id):
        x, y = get_map_positions(map_id)
        position_string = f"[{x},{y}]"
        mode = "a" if len(self.houses) > 0 else "w"

        if position_string in self.houses:
            print("position already saved")
            return

        with open("config/abandonned_houses.txt", mode) as f:
            f.write(f"{position_string}\n")
            print(f"saved position {position_string}")
            self.houses.append(position_string)

    def handle_ChatServerMessage(self, packet):
        """Triggered when a message is received in the chat (including the player's)"""

        # Only handle guild (2) and group (4) chat
        if packet["channel"] not in [2, 4]:
            return

        message = packet["content"]
        if message.startswith("$") and self.config["commands"]:
            # If user is not in Dofus, don't handle the message
            window_title = w32.GetWindowText(w32.GetForegroundWindow())
            if "Dofus" not in window_title:
                return

            # If the message is not from the player, don't handle it
            player_name = window_title.split()[0]
            sender_name = packet["senderName"]
            if sender_name != player_name:
                return

            command_key = message.split(" ")[0][1:]
            if command_key in self.commander.commands:
                self.commander.commands[command_key](packet, packet["channel"])

    def handle_ChatServerWithObjectMessage(self, packet):
        """Triggered when a message with objects is received in the chat (including the player's)"""

        self.handle_ChatServerMessage(packet)

    def handle_MapComplementaryInformationsDataMessage(self, packet):
        """Triggered when the player changes map"""

        if self.config["archimonstres"]:
            actors = packet["actors"]
            for entity in actors:
                # Monster group
                if entity["__type__"] == "GameRolePlayGroupMonsterInformations":
                    monsters = []
                    monsters.append(
                        entity["staticInfos"]["mainCreatureLightInfos"]
                    )  # Main monster
                    monsters += entity["staticInfos"]["underlings"]  # Underlings
                    for monster in monsters:
                        monster_name = get_monster_name(monster["genericId"])
                        if monster_name in self.archimonstres:
                            play_sound("spotted")
                            return

        if self.config["houses"]:
            for house in packet["houses"]:
                if len(house["houseInstances"]) > 1:
                    break

                for house_instance in house["houseInstances"]:
                    is_abandonned = not house_instance["hasOwner"]
                    if is_abandonned:
                        print("Abandonned house found ...", end=" ")
                        play_sound("dingding")
                        self.save_abandonned_house(packet["mapId"])
                        return
