"""Serious Bismuth: a business-attired variant of the crystal creature."""
from pathlib import Path
from .bismuth_elemental import SERIOUS, publish

TARGET_NAME = SERIOUS.target


def render(out_dir: str|Path,**opts):
    return publish(SERIOUS,out_dir,**opts)
