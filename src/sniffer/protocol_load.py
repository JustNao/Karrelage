from pathlib import Path
import pickle
import os, sys

if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app
    # path into variable _MEIPASS'.
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

with (Path(__file__).parent / "protocol.pk").open("rb") as f:
    types = pickle.load(f)
    msg_from_id = pickle.load(f)
    types_from_id = pickle.load(f)
    primitives = pickle.load(f)
