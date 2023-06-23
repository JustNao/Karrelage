import os
import requests as rq


def check_for_update():
    wd = os.getcwd()
    protocol_path = os.path.join(wd, "src", "sniffer", "protocol.pk")

    with open("DOFUS_VERSION", "r") as f:
        current_saved_version = f.read().strip()

    cloud_version = rq.get(
        "https://b37a-2a01-cb00-dcf-1000-a6d1-91af-b3c4-87ba.ngrok-free.app/DOFUS_VERSION"
    )
    if not cloud_version.ok:
        print("Error while fetching version from server, auto-update disabled.")
        return

    cloud_version = cloud_version.content.decode("utf-8").strip()

    if cloud_version != current_saved_version:
        print("New version found, updating...")
        packets = rq.get(
            "https://b37a-2a01-cb00-dcf-1000-a6d1-91af-b3c4-87ba.ngrok-free.app/protocol.pk",
        )
        with open(protocol_path, "wb") as f:
            f.write(packets.content)
        with open("DOFUS_VERSION", "w") as f:
            f.write(cloud_version)
