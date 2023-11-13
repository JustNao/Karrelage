import pyautogui as ag


def on_screen_position(position: tuple[int, int]):
    """Converts a position from a 2560x1440 screen to the current screen."""
    screen_x, screen_y = ag.size()
    x, y = position
    x /= 2560
    y /= 1440
    return (int(x * screen_x), int(y * screen_y))
