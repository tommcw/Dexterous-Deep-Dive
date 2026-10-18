"""Load full-hand background frames for the index-finger pose cycle."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

APP_DIR = Path(__file__).resolve().parent
HAND_WIDTH = 500
HAND_HEIGHT = 585  # native 749x877 aspect of background1–4

# Horizontal centres of each digit on background1.png (fraction of image width).
FINGER_X = {
    0: 0.147,  # little
    1: 0.286,  # ring
    2: 0.439,  # middle
    3: 0.602,  # index
    4: 0.856,  # thumb bend
}


def index_pose(angle: int) -> int:
    """Map index angle 0–1000 onto background1..4."""
    if angle >= 750:
        return 0
    if angle >= 500:
        return 1
    if angle >= 250:
        return 2
    return 3


def build_hand_frames(width: int = HAND_WIDTH, height: int = HAND_HEIGHT) -> list[Image.Image]:
    frames = []
    for n in (1, 2, 3, 4):
        path = APP_DIR / f"background{n}.png"
        if not path.is_file():
            raise FileNotFoundError(path)
        image = Image.open(path).convert("RGB")
        frames.append(image.resize((width, height), Image.LANCZOS))
    return frames
