import subprocess
import os
from build_protocol import main as build_protocol


def update_packets():
    username = os.getlogin()
    wd = os.getcwd().replace("\\", "/")
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
    build_protocol()


if __name__ == "__main__":
    update_packets()
