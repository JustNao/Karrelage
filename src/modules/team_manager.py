from src.entities.stats import idToStat
from .base import DofusModule

from time import sleep
from win32 import win32gui
import json
import re
import win32com.client
import pythoncom
import pyautogui as ag
import win32api, win32con
import mouse
import numpy as np
import random


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

        # Total health is (health from equipement + health from level + health from bonuses)
        temp_total_health = (
            self.stats[11]["current"]
            + self.stats[0]["current"]
            + self.stats[95]["current"]
        )
        # TODO: Need to look at why this is needed
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

    def update_health(self, update):
        if "loss" in update:
            self.total_health -= update["permanentDamages"]
            self.current_health -= update["loss"]
            self.current_health = min(self.current_health, self.total_health)
        if "delta" in update:
            self.current_health += update["delta"]
        print("Updated player's", self.name, "health to", self.current_health)

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


class TeamManager(DofusModule):
    def __init__(self) -> None:
        self.characters = {}
        self.auto_turn = False
        windows = ag.getAllTitles()  # type: ignore
        self.windows = [x for x in windows if re.search("- Dofus \d\.", x)]  # type: ignore
        self.player_characters = [(window.split()[0]) for window in self.windows]
        self.team: list[Player] = []
        self.buffer_team = {}
        self.buffer = []
        self.fighting = False

        mouse.on_middle_click(self.all_move)

        try:
            with open("config/multicompte.json") as file:
                importedChars = json.load(file)
        except FileNotFoundError:
            print("No character was manually put, and no file could be detected")
            return
        for name in importedChars:
            if name not in self.player_characters:
                self.player_characters.append(name)

    def get_window(self, name):
        dofus_windows = [x for x in ag.getAllTitles() if re.search("- Dofus \d\.", x)]
        for window in dofus_windows:
            if name in window:
                return win32gui.FindWindow(
                    None,
                    window,
                )
        return None

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

    def get_player(self, id):
        for player in self.team:
            if player.id == id:
                return player
        return None

    def all_move(self):
        x, y = mouse.get_position()
        lParam = win32api.MAKELONG(x, y)
        for character in self.player_characters:
            window = self.get_window(character)
            win32api.SendMessage(
                window, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam  # type: ignore
            )
            win32api.SendMessage(
                window, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, lParam  # type: ignore
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

    def handle_GameFightStartingMessage(self, _):
        """Triggered when the fight starts."""

        if not self.fighting:
            self.team = []
            self.buffer_team = {}
            self.fighting = True

    def handle_GameFightEndMessage(self, _):
        """Triggered when the fight ends."""

        self.fighting = False

    def handle_GameFightTurnStartMessage(self, packet):
        """Triggered when the turn starts for any entity in the combat."""

        player_id = packet["id"]
        player = self.get_player(player_id)

        # If the player is not in the team or an invocation, abort
        if player is None or isinstance(player, Invocation):
            return

        if player.auto_turn:
            sleep(random.uniform(0.2, 0.8))
            self.send_keystroke(player.window, 0x56)
            return

        # If the player has a window registered, we bring it to the foreground
        # if player.window is not None:
        #     try:
        #         shell = win32com.client.Dispatch(
        #             "WScript.Shell", pythoncom.CoInitialize()
        #         )
        #         shell.SendKeys(
        #             "%"
        #         )  # Send alt to shell, required for SetForegroundWindow
        #         win32gui.SetForegroundWindow(player.window)
        #     except:
        #         pass

    def handle_GameFightShowFighterMessage(self, packet):
        """Triggered when an entity is added to the combat.

        Here we use a buffer team to store our players, because the next
        packet informing us in which team the entity is will not contain
        the player's stats.
        """

        fighter = packet["informations"]

        # If the fighter is a monster group, abort
        if "name" not in fighter:
            return

        # If the fighter is not in the team yet
        if fighter["contextualId"] not in [x.id for x in self.team]:
            window = None

            # If fighter is controlled by us, we get the window
            if any(fighter["name"] == x for x in self.player_characters):
                window = self.get_window(fighter["name"])

            new_player = Player(
                id=fighter["contextualId"],
                name=fighter["name"],
                window=window,
                level=fighter["level"],
                breed=fighter["breed"],
                sex=int(fighter["sex"]),
            )

            new_player.set_stats(fighter["stats"]["characteristics"]["characteristics"])
            self.buffer_team[
                fighter["contextualId"]
            ] = new_player  # Storing in buffer_team until we are sure it's our own team

        # The fighter is already in the team but has not been initialized yet
        else:
            team_player = self.get_player(fighter["contextualId"])
            if team_player is None:
                return

            team_player.initialize(fighter)

    def handle_GameFightUpdateTeamMessage(self, packet):
        """Triggered when the team is updated."""

        own_team = False
        if "teamMembers" not in packet["team"]:
            return

        for member in packet["team"]["teamMembers"]:
            # If it's a monster group, abort
            if "name" not in member and "masterId" not in member:
                return

            # If our own character is in the team, we continue
            if "name" in member and any(
                member["name"] == x for x in self.player_characters
            ):
                own_team = True
                break

        if not own_team:
            return

        # Moving invocations to the end of the list
        # so that we can register the master first
        for index, member in enumerate(packet["team"]["teamMembers"]):
            if "name" not in member:
                invocation = packet["team"]["teamMembers"].pop(index)
                packet["team"]["teamMembers"].append(invocation)

        for member in packet["team"]["teamMembers"]:
            # If not a player or already in team
            if self.get_player(member["id"]) is not None:
                continue

            # If the member is a companion (e.g. Lumino)
            # We count it as an invocation
            if "masterId" in member:
                # Need to check if the masteId is already registered, because sometimes
                # we get the invocation before the master (and then again after the master)
                if not self.get_player(member["masterId"]):
                    continue

                self.team.append(
                    Invocation(member["id"], self.get_player(member["masterId"]))
                )
                continue

            # New team member
            if self.get_player(member["id"]) is None:
                window = self.get_window(member["name"])

                if self.buffer_team.get(member["id"]) is not None:
                    # If the player is in the buffer, we use it
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

    def handle_RefreshCharacterStatsMessage(self, packet):
        """Triggered when the stats of an entity are updated."""

        fighter = self.get_player(packet["fighterId"])

        # If the fighter is not in the team or is an invocation, abort
        if fighter is None or isinstance(fighter, Invocation):
            return

        fighter.update_stat(packet["stats"]["characteristics"]["characteristics"])

    def handle_GameActionFightLifePointsLostMessage(self, packet):
        """Triggered when an entity loses health points."""

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

    def handle_GameActionFightLifeAndShieldPointsLostMessage(self, packet):
        """Triggered when an entity gets damaged while having a shield."""

        # If the target is in the team and not an invocation, update his health
        target_player = self.get_player(packet["targetId"])
        if target_player is not None and not isinstance(target_player, Invocation):
            target_player.update_health(packet)
            return

        # If the source is in the team, add the damage to his damage counter
        source_player = self.get_player(packet["sourceId"])
        if source_player is not None:
            source_player.add_damage(packet["loss"] + packet["shieldLoss"])

    def handle_GameActionFightLifePointsGainMessage(self, packet):
        """Triggered when an entity gains health points."""

        if packet["targetId"] == packet["sourceId"]:
            source_player = self.get_player(packet["sourceId"])
            # If the source is the target, it's life steal
            # TODO: Check how self heal and life steal differ
            if source_player is not None:
                if "delta" in packet:
                    source_player.add_life_steal(packet["delta"])

        # If the target is in the team and not an invocation, update his health
        target_player = self.get_player(packet["targetId"])
        if target_player is not None and not isinstance(target_player, Invocation):
            target_player.update_health(packet)
            return

        # If the source is in the team, add the healing to his healing counter
        source_player = self.get_player(packet["sourceId"])
        if source_player is not None:
            source_player.add_healing(packet["delta"])

    def handle_GameActionFightDispellableEffectMessage(self, packet):
        """Triggered when an entity gets a dispellable buff/debuff."""

        # Only shields
        # TODO: fix shielding
        if packet["actionId"] != 1040:
            return

        source_player = self.get_player(packet["sourceId"])
        if source_player is None:
            return

        source_player.add_shielding(packet["effect"]["delta"])

    def handle_GameActionFightMultipleSummonMessage(self, packet):
        """Triggered when an entity summons one or multiple entities."""

        # If the summoner is not in the team, abort
        source_player = self.get_player(packet["sourceId"])
        if source_player is None:
            return

        invoc = Invocation(
            id=packet["summons"][0]["summons"][0]["informations"]["contextualId"],
            summoner=source_player,
        )
        self.team.append(invoc)
