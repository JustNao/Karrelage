import requests as rq
import keyboard as kb
import pyperclip
from .base import DofusModule
from time import sleep
import win32gui as w32


class Commander:
    def __init__(self):
        self.commands = {
            "enutrosor": lambda _: self.portals("enutrosor"),
            "srambad": lambda _: self.portals("srambad"),
            "xelorium": lambda _: self.portals("xelorium"),
            "ecaflipus": lambda _: self.portals("ecaflipus"),
        }

    def send_message(self, message):
        kb.press("space")
        sleep(2)
        pyperclip.copy(message)
        kb.press("ctrl+v")
        sleep(0.2)
        kb.press("enter")

    def portals(self, zone):
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
            print(pos_x, pos_y)
            self.send_message(f"Portail {zone} en [{pos_x},{pos_y}]")
        except KeyError:
            print("Pas de portail")
            self.send_message(f"Pas de portal {zone} trouvé")


class Biscuit(DofusModule):
    # Quality of Life assistant

    def __init__(self) -> None:
        self.reset()

    def reset(self):
        self.commander = Commander()

    def handle_ChatServerMessage(self, packet):
        """Triggered when a message is received in the chat (including the player's)"""

        if packet["channel"] not in [2, 4]:
            # Only handle guild (2) and group (4) chat
            return

        message = packet["content"]
        if message.startswith("$"):
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
                self.commander.commands[command_key](message)
