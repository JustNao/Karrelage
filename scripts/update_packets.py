import subprocess
import os
import requests as rq
from build_protocol import main as build_protocol
from pathlib import Path
from dotenv import load_dotenv


def update_packets():
    load_dotenv()
    username = os.getlogin()
    wd = str(Path(__file__).absolute().parents[1]).replace("\\", "/")
    DofusInvoker = (
        f"C:\\Users\\{username}\\AppData\\Local\\Ankama\\Dofus\\DofusInvoker.swf"
    )
    selectclass = "com.ankamagames.dofus.BuildInfos,com.ankamagames.dofus.network.++,com.ankamagames.jerakine.network.++"
    config = "parallelSpeedUp=0"

    command = f'"C:\\Program Files (x86)\\FFDec\\ffdec.bat" -config "{config}" -selectclass "{selectclass}" -export script ./protocol "{DofusInvoker}"'
    print("Loading DofusInvoker.swf, this may take a while.")
    p = subprocess.run(command, text=True, stdout=subprocess.PIPE, cwd=wd, shell=True)
    for line in p.stdout.splitlines():
        if "OK" in line:
            print("DofusInvoker.swf loaded, building protocol..")
            break
    protocol_path = build_protocol()
    with open(f"C:/Users/{username}/AppData/Local/Ankama/Dofus/VERSION", "r") as f:
        current_official_version = f.read().strip()
    with open("DOFUS_VERSION", "w") as f:
            f.write(current_official_version)

    if os.environ.get("LOCAL_DOFUS_VERSION_ADDRESS") is not None:
        print("Updating protocol on server..")
        with open(protocol_path, "rb") as f:
            rq.post(
                os.environ.get("LOCAL_DOFUS_VERSION_ADDRESS") + "/protocol",
                files={"protocol.pk": f},
            )
        response = rq.post(
            os.environ.get("LOCAL_DOFUS_VERSION_ADDRESS") + "/version",
            json={"version": current_official_version},
        )
        if not response.ok:
            print("Error while updating version on server.")
            print(response.content.decode("utf-8"))


if __name__ == "__main__":
    update_packets()
