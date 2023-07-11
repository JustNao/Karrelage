import re
import requests as rq
import undetected_chromedriver as uc


class Vulbis:
    base_url = "https://www.vulbis.com"
    portal_url = f"{base_url}/portal.php"

    @staticmethod
    def extract_position(input_str):
        """Extract the position in the brackets from the input string."""
        result = re.search(r"\[([-]?\d+),([-]?\d+)\]", input_str)
        if result is not None:
            position = (
                int(result.group(1)),
                int(result.group(2)),
            )  # converting to integers for use as coordinates
            return position
        else:
            return None

    @staticmethod
    def extract_preceding_content(input_str):
        """Extract the content just before the last <br> tag from the input string."""
        result = re.findall(r"(.*)(<br>)", input_str, re.DOTALL)
        if result:
            preceding_content = result[-1][0]
            clean_content = re.sub(r"<.*?>", "", preceding_content).strip()
            return " ".join(clean_content.split()[-2:])
        else:
            return None

    @staticmethod
    def get_portal_positions(zone) -> tuple[int, int, str]:
        zone_name_for_vulbis = {
            "ecaflipus": "Ecaflipus",
            "enutrosor": "Enutrosor",
            "srambad": "Srambad",
            "xelorium": "Xélorium",
        }
        payload = {"portal": zone_name_for_vulbis[zone], "server": "Draconiros"}
        response = rq.post(Vulbis.portal_url, payload)
        return *Vulbis.extract_position(
            response.text
        ), Vulbis.extract_preceding_content(response.text)

    @staticmethod
    def get_craft_price(gid: int):
        driver = uc.Chrome(headless=True)
        driver.get(
            f"https://www.vulbis.com/?server=Draconiros&gids={gid}&percent=0&craftableonly=false&select-type=-1&sellchoice=false&buyqty=1&sellqty=1&percentsell=0",
        )
        driver.implicitly_wait(10)
        try:
            craft_price_raw = driver.find_element(
                uc.By.XPATH, '//*[@id="scanTable"]/tbody/tr/td[10]/p[1]'
            ).text
        except uc.common.exceptions.NoSuchElementException:
            driver.quit()
            return None
        craft_price = craft_price_raw.replace("\u2006", "")
        driver.quit()
        return int(craft_price)
