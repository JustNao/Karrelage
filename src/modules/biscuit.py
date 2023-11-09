import pyperclip
import json
import os
import requests as rq
import keyboard as kb
import win32gui as w32
from .base import DofusModule
from src.entities.utils import load, kamasToString
from src.entities.id import get_monster_name
from src.entities.media import play_sound
from src.entities.maps import get_map_positions
from src.utils.externals import Vulbis
from datetime import datetime, timezone
from dateutil import parser, relativedelta


class Commander:
    def __init__(self):
        self.commands = {
            "enutrosor": lambda _, channel: self.portals("enutrosor", channel),
            "srambad": lambda _, channel: self.portals("srambad", channel),
            "xelorium": lambda _, channel: self.portals("xelorium", channel),
            "ecaflipus": lambda _, channel: self.portals("ecaflipus", channel),
            "price": lambda packet, channel: self.price(packet, channel),
        }
        self.channels = {
            2: "/g",
            4: "/p",
        }

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

    def price(self, packet, channel: int):
        gid = packet["objects"][0]["objectGID"]
        price = Vulbis.get_craft_price(gid)
        if price is None:
            self.send_message(f"{self.channels[channel]} Prix de craft: inconnu")
            return
        self.send_message(
            f"{self.channels[channel]} Prix de craft: {kamasToString(price)} K"
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
            self.config[key] = value

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
                try:
                    self.commander.commands[command_key](packet, packet["channel"])
                except Exception as e:
                    print(f"Error while executing command {command_key}: {e}")

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
