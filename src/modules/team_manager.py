import json
import re

import pythoncom
import win32com.client
from src.sniffer import protocol
from win32 import win32gui
import pyautogui as ag
import win32gui, win32api, win32con
import mouse
from src.entities.stats import idToStat
import numpy as np
from time import sleep
import random
import pygetwindow as gw
from colorama import Fore

DEBUG = False


def check(value):
    if value >= -10000 and value <= 10000:
        return value
    else:
        return int(np.int32(np.uint32(value)))


class Player:
    def __init__(self, id=0, name=None, window=None, level=0, breed=1, sex=0):
        self.id = id
        self.window = window
        self.name = name
        self.own = window is not None
        self.level = min(level, 200)
        self.auto_turn = False
        self.breed = breed
        self.sex = sex
        self.stats = {}
        self.current_health = 0
        self.total_health = 0
        self.cadrant = "90° horaire"
        self.shield = 0
        self.damage = 0
        self.healing = 0
        self.shielding = 0
        self.life_steal = 0

    def initialize(self, fighter):
        self.set_stats(fighter["stats"]["characteristics"]["characteristics"])
        self.level = min(fighter["level"], 200)
        self.breed = fighter["breed"]
        self.sex = int(fighter["sex"])

    def set_stats(self, characteristics):
        for characteristic in characteristics:
            id = characteristic["characteristicId"]
            if id not in (0, 11, 95, 97, 96):
                continue

            if "total" in characteristic:
                self.stats[id] = {
                    "current": check(characteristic["total"]),
                    "name": idToStat[id]["description"],
                    "order": idToStat[id]["order"],
                    "contextModif": 0,
                    "old": 0,
                }
            elif "base" in characteristic:
                self.stats[id] = {
                    "base": check(characteristic["base"]),
                    "additional": check(characteristic["additional"]),
                    "equipment": check(characteristic["objectsAndMountBonus"]),
                    "current": check(characteristic["base"])
                    + check(characteristic["additional"])
                    + check(characteristic["objectsAndMountBonus"]),
                    "name": idToStat[id]["description"],
                    "order": idToStat[id]["order"],
                    "contextModif": 0,
                    "old": 0,
                }

        # TODO: Need to look at why this is needed
        # Total health is (health from equipement + health from level + health from bonuses)
        temp_total_health = (
            self.stats[11]["current"]
            + self.stats[0]["current"]
            + self.stats[95]["current"]
        )
        if temp_total_health > 0:
            self.total_health = temp_total_health

        # Current health is (total health + health malus)
        self.current_health = self.total_health + self.stats[97]["current"]

    def update_stat(self, characteristics):
        for characteristic in characteristics:
            id = characteristic["characteristicId"]
            if id not in (0, 11, 95, 97, 96, 97):
                continue

            if id not in self.stats:
                self.stats[id] = {
                    "current": 0,
                    "old": 0,
                }

            if "total" in characteristic and characteristic["total"]:
                self.stats[id] |= {
                    "current": check(characteristic["total"]),
                    "name": idToStat[id]["description"],
                    "order": idToStat[id]["order"],
                    "old": 0 if id not in self.stats else self.stats[id]["current"],
                }
            elif "base" in characteristic:
                self.stats[id] |= {
                    "base": check(characteristic["base"]),
                    "additional": check(characteristic["additional"]),
                    "equipment": check(characteristic["objectsAndMountBonus"]),
                    "current": check(characteristic["base"])
                    + check(characteristic["additional"])
                    + check(characteristic["objectsAndMountBonus"]),
                    "name": idToStat[id]["description"],
                    "order": idToStat[id]["order"],
                    "old": 0 if id not in self.stats else self.stats[id]["current"],
                }

            if "used" in characteristic:
                self.stats[id]["current"] -= check(characteristic["used"])

            if "contextModif" in characteristic:
                if "contextModif" not in self.stats[id]:
                    delta = check(characteristic["contextModif"])
                else:
                    delta = (
                        check(characteristic["contextModif"])
                        - self.stats[id]["contextModif"]
                    )

                # Vitality buff
                if id == 11:
                    self.total_health += delta
                    self.current_health += delta

                self.stats[id]["current"] += delta
                self.stats[id]["contextModif"] = check(characteristic["contextModif"])

            # Updating shield value
            if id == 96:
                self.shield = self.stats[id]["current"]

            if id == 125:
                self.current_health += self.stats[id]["delta"]
                self.total_health += self.stats[id]["delta"]

            # Updating out of combat lost health
            if id == 97:
                self.current_health += self.stats[id]["current"] - self.stats[id]["old"]

            print(
                "Updated player's",
                self.name,
                "stat",
                self.stats[id]["name"],
                "to",
                self.stats[id]["current"],
            )

    def update_health(self, update):
        if "loss" in update:
            self.total_health -= update["permanentDamages"]
            self.current_health -= update["loss"]
            self.current_health = min(self.current_health, self.total_health)
        if "delta" in update:
            self.current_health += update["delta"]
        print("Updated player's", self.name, "health to", self.current_health)

        percent = self.current_health / self.total_health * 100
        if percent >= 90:
            self.cadrant = "90° horaire"
        elif percent >= 75:
            self.cadrant = "270° horaire - 90° contre horaire"
        elif percent >= 45:
            self.cadrant = "180°"
        elif percent >= 30:
            self.cadrant = "270° horaire - 90° contre horaire"
        else:
            self.cadrant = "90° horaire"

        self.health_string = "{:,}".format(self.current_health).replace(",", " ")

    def update_shield(self, update):
        if "shieldLoss" in update:
            self.shield -= update["shieldLoss"]

    def add_damage(self, damage):
        self.damage += damage
        print("Added", damage, "damage to player", self.name)

    def add_healing(self, healing):
        self.healing += healing

    def add_shielding(self, shielding):
        self.shielding += shielding

    def add_life_steal(self, life_steal):
        self.life_steal += life_steal

    def toggle_auto_turn(self):
        self.auto_turn = not self.auto_turn


class Invocation:
    def __init__(self, id=0, summoner: Player = None):
        self.id = id
        self.summoner = summoner

    def add_damage(self, damage):
        self.summoner.add_damage(damage)

    def add_healing(self, healing):
        self.summoner.add_healing(healing)

    def add_shielding(self, shielding):
        self.summoner.add_shielding(shielding)

    def add_life_steal(self, life_steal):
        self.summoner.add_life_steal(life_steal)


class TeamManager:
    def __init__(self) -> None:
        self.characters = {}
        self.auto_turn = False
        windows = ag.getAllTitles()  # type: ignore
        self.windows = [x for x in windows if re.search("- Dofus \d\.", x)]  # type: ignore
        self.player_characters = [window.split()[0] for window in self.windows]
        self.team: list[Player] = []
        self.buffer_team = {}
        self.buffer = []
        self.fighting = False

        # Necessary to bring window to foreground
        self.shell = win32com.client.Dispatch("WScript.Shell", pythoncom.CoInitialize())
        self.shell.SendKeys("%")

        mouse.on_middle_click(self.all_move)

        try:
            with open("config/multicompte.json") as file:
                importedChars = json.load(file)
        except FileNotFoundError:
            print("No character was manually put, and no file could be detected")
            return
        for name in importedChars:
            print(f"Importing {Fore.BLUE}{name}{Fore.RESET}")
            windows = [x for x in self.windows if re.search(name, x)]
            if len(windows) > 0:
                window_name = windows[0]
                self.characters[name] = win32gui.FindWindow(
                    None,
                    window_name,
                )

    def save_packet(self, packet):
        self.buffer.append(packet)
        if len(self.buffer):
            with open("buffer.json", "r") as f:
                current = json.loads(f.read())
                current[self.buffer[0]["__type__"]].append(self.buffer[0])
            with open("buffer.json", "w") as f:
                f.write(json.dumps(current, indent=4))
                del self.buffer[0]

    def __hash__(self) -> int:
        team = self.get_team()
        return hash(json.dumps(team))

    def packetRead(self, msg):

        name = protocol.msg_from_id[msg.id]["name"]

        if name == "GameFightUpdateTeamMessage":
            packet = protocol.readMsg(msg)
            if packet is None:
                return
            if DEBUG:
                self.save_packet(packet)

            own_team = False
            for member in packet["team"]["teamMembers"]:
                # Monster group
                if "name" not in member:
                    return

                if any(member["name"] == x for x in self.player_characters):
                    own_team = True
                    break

            if not own_team:
                return

            for member in packet["team"]["teamMembers"]:
                window = None

                # If not a player or already in team
                if self.get_player(member["id"]) is not None:
                    continue

                # If the member is a companion (e.g. Lumino)
                # We count it as an invocation
                if "masterId" in member:
                    self.team.append(
                        Invocation(member["id"], self.get_player(member["masterId"]))
                    )
                    return

                # Get the correspond window if we are playing the character
                if any(member["name"] == x for x in self.player_characters):
                    window = win32gui.FindWindow(
                        None,
                        [x for x in self.windows if re.search(member["name"], x)].pop(),
                    )

                # New team member
                if self.get_player(member["id"]) is None:
                    if self.buffer_team.get(member["id"]) is not None:
                        player = self.buffer_team[member["id"]]
                        del self.buffer_team[member["id"]]
                    else:
                        if "breed" not in member:
                            player = Player(
                                id=member["id"],
                                name=member["name"],
                                window=window,
                                level=member["level"],
                            )
                        else:
                            player = Player(
                                id=member["id"],
                                name=member["name"],
                                window=window,
                                level=member["level"],
                                breed=member["breed"],
                                sex=int(member["sex"]),
                            )

                    self.team.append(player)

        # Turn start
        elif name == "GameFightTurnStartMessage":
            packet = protocol.readMsg(msg)
            if packet is None:
                return

            if DEBUG:
                self.save_packet(packet)

            player_id = packet["id"]
            player = self.get_player(player_id)

            if player is None or isinstance(player, Invocation):
                return
            # If the player is in the team and not an invocation

            if player.auto_turn:
                sleep(random.uniform(0.2, 0.8))
                self.send_keystroke(player.window, 0x56)

            # If the player has a window registered, we bring it to the foreground
            if player.window is not None:
                # doesn't work with multithreading
                win32gui.SetForegroundWindow(player.window)

        # Stats init
        elif name == "GameFightShowFighterMessage":
            packet = protocol.readMsg(msg)
            if packet is None:
                return

            if DEBUG:
                self.save_packet(packet)

            fighter = packet["informations"]

            # If the fighter is a monster group, abort
            if "name" not in fighter:
                return

            # If the fighter is not in the team yet
            if fighter["contextualId"] not in [x.id for x in self.team]:
                window = None
                if any(fighter["name"] == x for x in self.player_characters):
                    window = win32gui.FindWindow(
                        None,
                        [
                            x for x in self.windows if re.search(fighter["name"], x)
                        ].pop(),
                    )
                new_player = Player(
                    id=fighter["contextualId"],
                    name=fighter["name"],
                    window=window,
                    level=fighter["level"],
                    breed=fighter["breed"],
                    sex=int(fighter["sex"]),
                )
                new_player.set_stats(
                    fighter["stats"]["characteristics"]["characteristics"]
                )
                self.buffer_team[fighter["contextualId"]] = new_player
            # The fighter is already in the team but has not been initialized yet
            else:
                team_player = self.get_player(fighter["contextualId"])
                if team_player is None:
                    return

                team_player.initialize(fighter)

        # Stats update
        elif name == "RefreshCharacterStatsMessage":
            packet = protocol.readMsg(msg)
            if packet is None:
                return

            fighter = self.get_player(packet["fighterId"])
            # If the fighter is not in the team or is an invocation, abort
            if fighter is None or isinstance(fighter, Invocation):
                return

            if DEBUG:
                self.save_packet(packet)

            fighter.update_stat(packet["stats"]["characteristics"]["characteristics"])

        # Health update
        elif name == "GameActionFightLifePointsLostMessage":
            packet = protocol.readMsg(msg)
            if packet is None:
                return

            target_player = self.get_player(packet["targetId"])
            # If the target is in the team and not an invocation, update his health
            if target_player is not None and not isinstance(target_player, Invocation):
                target_player.update_health(packet)
                return

            source_player = self.get_player(packet["sourceId"])
            # If the source is in the team, add the damage to his damage counter
            if source_player is not None:
                if "loss" in packet:
                    source_player.add_damage(packet["loss"])
                elif "delta" in packet:
                    source_player.add_damage(packet["delta"])

        elif name == "GameActionFightLifeAndShieldPointsLostMessage":
            packet = protocol.readMsg(msg)
            if packet is None:
                return

            target_player = self.get_player(packet["targetId"])
            # If the target is in the team and not an invocation, update his health
            if target_player is not None and not isinstance(target_player, Invocation):
                target_player.update_health(packet)
                return

            source_player = self.get_player(packet["sourceId"])
            # If the source is in the team, add the damage to his damage counter
            if source_player is not None:
                source_player.add_damage(packet["loss"] + packet["shieldLoss"])

        elif name == "GameActionFightLifePointsGainMessage":
            packet = protocol.readMsg(msg)
            if packet is None:
                return

            if packet["targetId"] == packet["sourceId"]:
                source_player = self.get_player(packet["sourceId"])
                # If the source is the target, it's life steal
                # TODO: Check how self heal and life steal differ
                if source_player is not None:
                    if "delta" in packet:
                        source_player.add_life_steal(packet["delta"])

            target_player = self.get_player(packet["targetId"])
            # If the target is in the team and not an invocation, update his health
            if target_player is not None and not isinstance(target_player, Invocation):
                target_player.update_health(packet)
                if DEBUG:
                    self.save_packet(packet)

                return

            source_player = self.get_player(packet["sourceId"])
            # If the source is in the team, add the healing to his healing counter
            if source_player is not None:
                source_player.add_healing(packet["delta"])

        # Fight start
        elif name == "GameFightStartingMessage":
            if not self.fighting:
                self.team = []
                self.buffer_team = {}
                self.fighting = True

        elif name == "GameFightEndMessage":
            self.fighting = False
        # Add invocations to the team
        elif name == "GameActionFightMultipleSummonMessage":
            packet = protocol.readMsg(msg)
            if packet is None:
                return

            if DEBUG:
                self.save_packet(packet)

            source_player = self.get_player(packet["sourceId"])
            # If the summoner is not in the team, abort
            if source_player is None:
                return

            invoc = Invocation(
                id=packet["summons"][0]["summons"][0]["informations"]["contextualId"],
                summoner=source_player,
            )
            self.team.append(invoc)

        elif name == "GameActionFightDispellableEffectMessage":
            packet = protocol.readMsg(msg)
            if packet is None:
                return

            if DEBUG:
                self.save_packet(packet)

            # Only shields
            if packet["actionId"] != 1040:
                return

            source_player = self.get_player(packet["sourceId"])
            if source_player is None:
                return

            source_player.add_shielding(packet["effect"]["delta"])

        elif name == "ObjectAveragePricesMessage":
            self.save_packet(protocol.readMsg(msg))

    def get_player(self, id):
        for player in self.team:
            if player.id == id:
                return player
        return None

    def all_move(self):
        x, y = mouse.get_position()
        lParam = win32api.MAKELONG(x, y)
        for character_window in self.characters.values():
            win32api.SendMessage(
                character_window, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam  # type: ignore
            )
            win32api.SendMessage(
                character_window, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, lParam  # type: ignore
            )

    def get_team(self):
        displayable_team = []
        for entity in self.team:
            if isinstance(entity, Player):
                displayable_team.append(vars(entity))
        return displayable_team

    def update(self, id):
        player = self.get_player(int(id))
        player.toggle_auto_turn()

    def send_keystroke(self, window, key=0x56):
        win32api.SendMessage(window, win32con.WM_KEYDOWN, key, 0)
        win32api.SendMessage(window, win32con.WM_KEYUP, key, 0)
