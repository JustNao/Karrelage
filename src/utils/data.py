import pyamf
import os

appdata_folder = os.environ["APPDATA"]


def load_dat(filename: str):
    if not filename.endswith(".dat"):
        filename += ".dat"
    full_filepath = os.path.join(appdata_folder, "Dofus", filename)
    if not os.path.exists(full_filepath):
        raise FileNotFoundError(f"File {full_filepath} not found")
    with open(full_filepath, "rb") as f:
        data = f.read()
    decoder = pyamf.decode(data, encoding=pyamf.AMF3)
    content = decoder.readElement()
    return content
