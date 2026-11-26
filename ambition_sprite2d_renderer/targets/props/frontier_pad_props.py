"""The loading walks and service steps at Pad Three."""

from __future__ import annotations

from ._district_props import Piece, targets
from ._town_kit import box
from .frontier_props import HAZARD, HULL, HULL_ORANGE, PAL, STEEL, STEEL_DARK, STEEL_LIGHT, container, deck_edge


STREET = 640


def loading_deck(canvas, left, right, top):
    """Draw a steel deck with a light edge at the standing height."""
    canvas.put(canvas.mask(box(left, top, right, top + 14)), STEEL)
    canvas.put(canvas.mask(box(left, top + 9, right, top + 14)), STEEL_DARK)
    deck_edge(canvas, left, right, top, STEEL_LIGHT)
    for x in (left + 9, right - 9):
        canvas.put(canvas.mask(lambda pen: pen.ellipse(x, top + 7, 2)), HAZARD)


def loading_walk(canvas, _kit):
    """Draw the scale and the walks by the booth and container stack."""
    container(canvas, 552, 584, 632, STREET, (77, 109, 119), "scale", mark=False)
    loading_deck(canvas, 544, 640, 576)
    canvas.put(canvas.mask(box(580, 594, 605, 608)), STEEL_DARK)
    canvas.put(canvas.mask(box(583, 597, 602, 602)), HAZARD)
    for left, right, top in ((848, 976, 528), (1200, 1296, 512)):
        canvas.put(canvas.mask(lambda pen: pen.line(
            [(left + 4, top + 13), (left + 20, top + 37), (right - 16, top + 37), (right - 4, top + 13)], 5
        )), STEEL_DARK)
        canvas.put(canvas.mask(lambda pen: pen.line(
            [(left + 29, top), (left + 29, top - 24), (right - 18, top - 24), (right - 18, top)], 3
        )), HULL)
        loading_deck(canvas, left, right, top)


def service_steps(canvas, _kit):
    """Draw the steps below the cockpit and their supports on the apron."""
    canvas.put(canvas.mask(lambda pen: pen.line(
        [(1754, 518), (1810, 527), (1904, 600), (1944, STREET)], 7
    )), STEEL_DARK)
    canvas.put(canvas.mask(lambda pen: pen.line(
        [(1764, 486), (1836, 486), (1848, 522), (1935, 550), (1943, 576)], 4
    )), HULL_ORANGE)
    for left, right, top in ((1752, 1848, 512), (1840, 1952, 576)):
        loading_deck(canvas, left, right, top)


TARGETS = targets({
    "frontier_pad_loading_walk": Piece((530, 482, 1304, 642), loading_walk),
    "frontier_pad_service_steps": Piece((1736, 480, 1960, 642), service_steps),
}, PAL)
