import playsound


def play_sound(sound: str):
    playsound.playsound(f"src/entities/sound/{sound}.mp3", False)
