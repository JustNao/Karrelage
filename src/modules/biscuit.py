import pyperclip
import json
import requests as rq
import keyboard as kb
import win32gui as w32
from .base import DofusModule
from src.entities.utils import load
from src.entities.id import monsterToName
from src.entities.media import play_sound
from time import sleep
from datetime import datetime, timezone
from dateutil import parser, relativedelta


class Commander:
    def __init__(self):
        self.commands = {
            "enutrosor": lambda _, channel: self.portals("enutrosor", channel),
            "srambad": lambda _, channel: self.portals("srambad", channel),
            "xelorium": lambda _, channel: self.portals("xelorium", channel),
            "ecaflipus": lambda _, channel: self.portals("ecaflipus", channel),
        }
        self.channels = {
            2: "/g",
            4: "/p",
        }

    def send_message(self, message):
        pyperclip.copy(message)
        kb.press_and_release("ctrl+v")
        kb.press_and_release("enter")

    def portals(self, zone, channel):
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
                f"{self.channels[channel]} Portail {zone} en [{pos_x},{pos_y}] il y'a {time_diff_str} ({remaining_uses} utilisations restantes)"
            )
        except KeyError:
            print("Pas de portail")
            self.send_message(f"{self.channels[channel]} Pas de portal {zone} trouvé")


class Biscuit(DofusModule):
    # Quality of Life assistant

    def __init__(self) -> None:
        self.reset()
        self.load_config()
        self.archimonstres = load("Archi")
        self.relevant_monster = None

    def reset(self):
        self.commander = Commander()
        self.config = {"commands": True, "archimonstres": True}

    def load_config(self):
        with open("config/biscuit.json") as f:
            self.config = self.config | json.load(f)

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
                self.commander.commands[command_key](message, packet["channel"])

    def handle_MapComplementaryInformationsDataMessage(self, packet):
        """Triggered when the player changes map"""

        actors = packet["actors"]
        for entity in actors:
            # Monster group
            if entity["__type__"] == "GameRolePlayGroupMonsterInformations":
                monsters = []
                print(entity["staticInfos"]["mainCreatureLightInfos"])
                monsters.append(
                    entity["staticInfos"]["mainCreatureLightInfos"]
                )  # Main monster
                monsters += entity["staticInfos"]["underlings"]  # Underlings
                for monster in monsters:
                    monster_name = monsterToName(monster["genericId"])
                    if (
                        monster_name in self.archimonstres
                        or monster_name == self.relevant_monster
                    ):
                        play_sound("spotted")
                        return
