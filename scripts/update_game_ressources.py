import os
import json
import gzip
from PyDofus.d2o import D2OReader, InvalidD2OFile
from PyDofus.d2i import D2I, InvalidD2IFile

username = os.getlogin()
dofus_folder = f"C:/Users/{username}/AppData/Local/Ankama/Dofus"
d2o_files = [
    "Characteristics.d2o",
    "Effects.d2o",
    "Items.d2o",
    "MapPositions.d2o",
    "PointOfInterest.d2o",
    "Recipes.d2o",
]
for file in d2o_files:
    filepath = os.path.join(dofus_folder, "data", "common", file)
    if os.path.exists(filepath):
        print(f"Loading {file}")
        try:
            d2o_file = open(filepath, "rb")
            d2o_reader = D2OReader(d2o_file)
            d2o_data = d2o_reader.get_objects()
            d2o_file.close()
            output_file = file.replace("d2o", "json.gz")
            with gzip.open(
                f"src/entities/gameRessources/{output_file}", "wt", encoding="utf-8"
            ) as f:
                json.dump(d2o_data, f)
        except InvalidD2OFile:
            print(f"Invalid file {file}, skipping...")
            pass

# i18n_fr
filepath = os.path.join(dofus_folder, "data", "i18n", "i18n_fr.d2i")
if os.path.exists(filepath):
    print(f"Loading i18n")
    try:
        d2i_file = open(filepath, "rb")
        d2i_reader = D2I(d2i_file)
        d2i_data = d2i_reader.read()
        d2i_file.close()
        with gzip.open(
            f"src/entities/gameRessources/i18n_fr.json.gz", "wt", encoding="utf-8"
        ) as f:
            json.dump(d2i_data, f, ensure_ascii=False)
    except InvalidD2IFile:
        print(f"Error during i18n loading")
        pass
