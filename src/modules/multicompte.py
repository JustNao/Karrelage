import random
import re
from sniffer import protocol
from colorama import Fore
from win32 import win32gui
import win32com.client as client
import pyautogui as ag
import json
import win32gui, win32api, win32con
from time import sleep
import mouse


class Perso:
    def __init__(self, id=0, mule=False, window=None):
        self.id = id
        self.mule = mule
        self.active = False
        self.window = window


class Multicompte:
    def __init__(self) -> None:
        self.characters = {}
        self.auto_turn = False
        windows = ag.getAllTitles()
        windows = [x for x in windows if re.search("- Dofus \d\.", x)]

        try:
            with open("config/multicompte.json") as file:
                importedChars = json.load(file)
        except FileNotFoundError:
            print("No character was manually put, and no file could be detected")
            return
        for char in importedChars:
            name = char["name"]
            print(f"Importing {Fore.BLUE}{name}{Fore.RESET}")
            window = [x for x in windows if re.search(char["name"], x)].pop()
            self.characters[char["name"]] = Perso(
                mule=char["mule"], window=win32gui.FindWindow(None, window)
            )

        mouse.on_middle_click(self.all_move)

    def packetRead(self, msg):
        name = protocol.msg_from_id[msg.id]["name"]

        if name == "GameFightUpdateTeamMessage":
            packet = protocol.readMsg(msg)
            if packet is None:
                return

            for member in packet["team"]["teamMembers"]:
                if "name" in member and member["name"] in self.characters:
                    self.characters[member["name"]].id = member["id"]
                    break

        elif name == "GameFightTurnStartMessage":
            packet = protocol.readMsg(msg)
            if packet is None:
                return

            if packet["id"] in [x.id for x in self.characters.values()]:
                character = self.get_character(packet["id"])
                if self.auto_turn and character.mule:
                    sleep(random.uniform(0.2, 0.8))
                    self.send_keystroke(character.window, 0x56)
                else:
                    shell = client.Dispatch("WScript.Shell")
                    shell.SendKeys("%")
                    win32gui.SetForegroundWindow(character.window)

    def send_keystroke(self, window, key=0x56):
        win32api.SendMessage(window, win32con.WM_KEYDOWN, key, 0)
        win32api.SendMessage(window, win32con.WM_KEYUP, key, 0)

    def get_character(self, id):
        for character in self.characters.values():
            if character.id == id:
                return character

    def toggle_auto_turn(self):
        self.auto_turn = not self.auto_turn
        if self.auto_turn:
            print(f"{Fore.GREEN}Auto turn is now enabled{Fore.RESET}")
            return "on"
        else:
            print(f"{Fore.RED}Auto turn is now disabled{Fore.RESET}")
            return "off"

    def all_move(self):
        x, y = mouse.get_position()
        lParam = win32api.MAKELONG(x, y)
        for character in self.characters.values():
            win32api.SendMessage(
                character.window, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam
            )
            win32api.SendMessage(
                character.window, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, lParam
            )
