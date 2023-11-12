import json
import time
import pyperclip
import pygetwindow
import pyautogui as ag
from seleniumwire import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from seleniumwire.utils import decode
from src.entities.id import get_monster_name, get_poi_name
from src.entities.maps import get_map_positions
from src.entities.utils import load
from src.utils.data import load_dat
from src.modules.base import DofusModule


class TreasureHunter(DofusModule):
    def __init__(self):
        # Running selenium webdriver in the background to simulate the user's clicks on the site
        options = Options()
        # options.add_argument('--headless')
        options.add_argument("log-level=1")
        self.driver = webdriver.Chrome(options=options)
        self.driver.get("https://dofusdb.fr/fr/tools/treasure-hunt")

        self.player_position = self.Position()
        self.hint_position = self.Hint()
        self.time_start = 0.0
        self.direction = "stay"
        self.check_positions = []
        self.phorreur = {"lookingFor": False, "npcId": 2673}
        self.autopilot = False
        self.autopilot_moving = False
        self.relevant_monsters = load("Archi")
        dofus_windows = pygetwindow.getWindowsWithTitle("- Dofus")
        if len(dofus_windows) > 0:
            self.dofus_window = dofus_windows[0]
        else:
            raise Exception("Dofus needs to be launched before starting the bot")
        self.setup_bot()

    class Hint:
        def __init__(self, posX=0, posY=0, x_d=666, y_d=666):
            self.x = posX
            self.y = posY
            self.x_distance = x_d
            self.y_distance = y_d

        def __str__(self):
            return "[" + str(self.x) + "," + str(self.y) + "]"

        def __eq__(self, obj):
            return (
                hasattr(obj, "x")
                and hasattr(obj, "y")
                and obj.x == self.x
                and obj.y == self.y
            )

    class Position:
        def __init__(self, posX=-25, posY=-36):
            self.x = posX
            self.y = posY

        def __str__(self):
            return "[" + str(self.x) + "," + str(self.y) + "]"

        def __eq__(self, obj):
            return (
                hasattr(obj, "x")
                and hasattr(obj, "y")
                and obj.x == self.x
                and obj.y == self.y
            )

    def is_hint_too_far(self):
        return self.hint_position.x_distance > 10 or self.hint_position.y_distance > 10

    # def exit(self):
    #     self.driver.quit()

    def move(self):
        # Déplacement du bot

        if self.direction == "stay":
            return

        if self.is_hint_too_far() and not self.phorreur["lookingFor"]:
            return

        # For first step, the hint will likely be away
        if (
            abs(self.player_position.x - self.hint_position.x) > 10
            or abs(self.player_position.y - self.hint_position.y) > 10
        ):
            return

        # If the autopilot is on, we don't move the bot
        if self.autopilot_moving:
            return

        if not self.phorreur["lookingFor"]:
            self.autopilot_moving = True
            x, y = self.hint_position.x, self.hint_position.y
            ag.hotkey("space")
            print("Autopilot : moving to", x, y)
            pyperclip.copy(f"/travel {x} {y}")
            ag.hotkey("ctrl", "v")
            ag.hotkey("enter")
            time.sleep(0.5)
            ag.hotkey("enter")
            time.sleep(0.5)
            ag.hotkey("esc")
            return

    def next_step(self):
        pass

    def setup_bot(self):
        screen_x, screen_y = ag.size()
        ui_positions = load_dat("Berilia_ui_positions")
        try:
            middle_banner = ui_positions["banner##pos##mainCtr##default"]
        except KeyError:
            raise Exception("Middle banner not found")
        self.move_positions = {
            "right": (screen_x - 50, screen_y // 2),
            "left": (50, screen_y // 2),
            "top": (screen_x // 2, 10),
            "bottom": (
                (middle_banner["x"] + 270.2) * 1.404,
                middle_banner["y"] * 1.404,
            ),  # TODO: check if this is the right ratio for all resolutions
        }

    def handle_CurrentMapMessage(self, packet):
        """Triggered when the player changes map"""
        self.player_position = self.Position(*get_map_positions(packet["mapId"]))
        self.step_update()

    def handle_TreasureHuntMessage(self, packet):
        """Triggered when the bot receives a new step"""
        self.reset()

        if len(packet["flags"]) == 0:
            # First step of the hunt
            self.check_positions.clear()
            self.check_positions.append(get_map_positions(packet["startMapId"]))
            if packet["checkPointCurrent"] == 0:
                self.time_start = time.time()
                self.player_position = self.Position(-25, -36)  # Malle aux trésors

        elif len(packet["flags"]) == packet["totalStepCount"]:
            # Last step of the current checkpoint
            self.next_step()
            return

        if packet["checkPointCurrent"] >= packet["checkPointTotal"] - 1:
            # Last step of the hunt
            end = time.time()
            print(f"This hunt took {int(end - self.time_start)} seconds to finish")
            return

        direction_int = packet["knownStepsList"][-1]["direction"]
        int_to_str = {
            0: "right",
            2: "bottom",
            4: "left",
            6: "top",
        }
        direction_str = int_to_str[direction_int]
        self.direction = direction_str

        if (
            packet["knownStepsList"][-1]["__type__"]
            == "TreasureHuntStepFollowDirectionToPOI"
        ):
            # Decor element to look for
            client_hint_name = get_poi_name(packet["knownStepsList"][-1]["poiLabelId"])
            self.get_hint(packet, client_hint_name)
            if self.hint_position.x_distance == 666:
                print("ERROR : no hint found !")
                self.direction = "stay"
            else:
                self.check_positions.append(
                    (self.hint_position.x, self.hint_position.y)
                )
                print("Hint found !")
                self.step_update()
                self.move()
        else:
            # Phorreur to look for
            self.phorreur["lookingFor"] = True
            self.phorreur["npcId"] = packet["knownStepsList"][-1]["npcId"]
            if (len(packet["flags"]) == 0) and (packet["checkPointCurrent"] == 0):
                # If the first step is a phorreur, we don't start looking for it immediately
                self.direction = "stay"
            self.move()

    def handle_MapComplementaryInformationsDataMessage(self, packet):
        """Triggered when the bot enters a new map"""
        for actor in packet["actors"]:
            if actor["__type__"] == "GameRolePlayTreasureHintInformations":
                if actor["npcId"] == self.phorreur["npcId"] and (
                    self.phorreur["lookingFor"] == True
                ):
                    self.phorreur["lookingFor"] = False
                    self.hint_position = self.Hint(
                        self.player_position.x, self.player_position.y, 0
                    )
                    self.direction = "stay"
                    self.next_step()
                    break
            elif actor["__type__"] == "GameRolePlayGroupMonsterInformations":
                main_monster = actor["staticInfos"]["mainCreatureLightInfos"][
                    "genericId"
                ]
                if get_monster_name(main_monster) in self.relevant_monsters:
                    print("Archimonstre found !")
                    self.direction = "stay"
                    self.autopilot_moving = False
                    # TODO: add a stop for the autopilot
                    break
        self.move()

    def step_update(self):
        """Updates the Hunter's state"""

        self.hint_position.x_distance = abs(
            self.player_position.x - self.hint_position.x
        )
        self.hint_position.y_distance = abs(
            self.player_position.y - self.hint_position.y
        )

        if self.hint_position.x_distance > self.hint_position.y_distance:
            if self.player_position.x < self.hint_position.x:
                direction = "right"
            else:
                direction = "left"
        else:
            if self.player_position.y < self.hint_position.y:
                direction = "bottom"
            else:
                direction = "top"
        self.direction = direction

        if self.player_position == self.hint_position:
            print("Hint found !")
            self.direction = "stay"
            self.autopilot_moving = False
            time.sleep(1)
            # TODO: add a button to click to go to the next step
            self.next_step()

    def reset(self):
        self.hint_position.x_distance = 666
        self.hint_position.y_distance = 666
        self.direction = "stay"
        self.phorreur["lookingFor"] = False
        self.autopilot_moving = False

    def get_DofusDB_pos(self, hintBody, poiToLookFor):
        hintBody["data"].sort(key=lambda x: x["distance"])
        for pos in hintBody["data"]:
            for poi in pos["pois"]:
                if poi["name"]["fr"] == poiToLookFor:
                    return pos["posX"], pos["posY"], pos["distance"]
        return 666, 666, 666

    def get_DofusDB_request(self, posX, posY, direction, poiToLookFor):
        driver_pos_x = self.driver.find_element(By.XPATH, "//input[@placeholder='X']")
        driver_pos_x.click()
        driver_pos_x.send_keys(Keys.CONTROL, "a")
        driver_pos_x.send_keys(posX)
        driver_pos_y = self.driver.find_element(By.XPATH, "//input[@placeholder='Y']")
        driver_pos_y.click()
        driver_pos_y.send_keys(Keys.CONTROL, "a")
        driver_pos_y.send_keys(posY)
        arrow = self.driver.find_element(
            By.XPATH, f"//i[contains(@class, 'fa-arrow-{direction}')]"
        )
        arrow.click()

        try:
            hintRequest = self.driver.wait_for_request(
                "https://api.dofusdb.fr/treasure-hunt"
            )
        except Exception:
            self.driver.refresh()
            print("Error with DofusDB request, retrying in 3 seconds...")
            time.sleep(3)
            return self.get_DofusDB_request(posX, posY, direction, poiToLookFor)

        response = hintRequest.response
        if not response:
            raise Exception("No response from DofusDB")
        body = decode(
            response.body, response.headers.get("Content-Encoding", "identity")
        )
        hintBody = json.loads(body.decode("utf-8"))
        del self.driver.requests
        return self.get_DofusDB_pos(hintBody, poiToLookFor)

    def get_hint(self, packet, clientHintName):
        direction_for_DofusDB = {
            "right": "right",
            "bottom": "down",
            "left": "left",
            "top": "up",
        }

        if len(packet["flags"]) == 0:
            lastCheckPoint = packet["startMapId"]
        else:
            lastCheckPoint = packet["flags"][-1]["mapId"]

        posX, posY = get_map_positions(lastCheckPoint)
        direction = direction_for_DofusDB[self.direction]

        newPosX, newPosY, distance = self.get_DofusDB_request(
            str(posX), str(posY), direction, clientHintName
        )
        self.hint_position = self.Hint(newPosX, newPosY, distance)
