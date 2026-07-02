"""Ambition 2D sprite renderer.

One package, two authoring surfaces: YAML-config generator targets
(``registry/character_generators.py`` + ``configs/*.yaml``) and module
targets auto-discovered under ``targets/<category>/``. See
``registry/discovery.py`` for the Target contract and README.md for the
walkthrough.
"""

__all__ = ["__version__"]
__version__ = "0.3.0"
