import re
import requests as rq


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
