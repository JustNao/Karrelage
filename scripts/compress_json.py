from src.entities.utils import load, save
from glob import glob
import json
import os

for file in glob("src/entities/gameRessources/*.json"):
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
    base_name = os.path.basename(file)
    save(data, base_name)
