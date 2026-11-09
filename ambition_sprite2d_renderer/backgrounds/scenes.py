"""The parallax scenes: what is behind the play in each biome.

A scene has four layers, from the far one to the near one: `sky`,
`far_backplate`, `near_background` and `foreground_atmosphere`. The game
draws each one as a square panel larger than the view, and moves the near
ones more than the far ones when the camera moves.

What the view shows of a panel
------------------------------

A 16:9 view shows only the middle band of a square panel: about `v` 0.27 to
0.73 of the sky, and about 0.32 to 0.68 of the near layer when the camera is
at the middle of the room (0.18 to 0.82 over the full height of a room). A
thing above or below that band is seen only in a taller view. So a scene has
its horizon near `HORIZON`, its sun or moon above it in the band, and plain
ground below.

How a scene stays behind the play
---------------------------------

- A far thing has the colour of the air: each layer is mixed with the sky
  colour of the scene, the far one most.
- No layer has the lightest or the darkest values of the scene's play art in
  a large area, and no layer has small parts with hard contrast.
- The near layer is the darkest one, with a thin light on the edges that
  face the light of the scene.

The art is made here, with `artkit`, and published as PNG files. The game
draws no part of it.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
from PIL import Image

from . import arenas, art_dimension, art_quarters, eureka, evil, foregrounds, history_americas_pacific, history_atlantic, history_bengal, history_brazil, history_central_africa, history_east_asia_coast, history_eras, history_japan, history_oceania, history_origins, history_south_america, history_southeast_asia, interiors, math_town, military_tower, ninja_village, noodly, orbital, outdoors, pirate_port, room_look_sky
from . import history_budj_bim
from . import history_micronesia
from .artkit import Art
from .parts import LAYER_BLUR, LAYER_SIZE

# ---------------------------------------------------------------------------
# The table of scenes
# ---------------------------------------------------------------------------

Scene = Callable[[str, Art], np.ndarray]

SCENES: dict[str, Scene] = {
    "hub": arenas.hub,
    "lab": interiors.lab,
    "alarm": interiors.alarm,
    "undertown": interiors.undertown,
    "basement": interiors.foundry,
    "cave": interiors.cave,
    "cove": outdoors.cove,
    "water": outdoors.water,
    "forest": outdoors.forest,
    "primeval": outdoors.primeval,
    "starlight": outdoors.starlight,
    "stardune": outdoors.stardune,
    "starless": outdoors.starless,
    "void_castle": outdoors.void_castle,
    "void": outdoors.void,
    "skybridge": outdoors.skybridge,
    "open_sky": outdoors.open_sky,
    "boss": arenas.boss,
    "noodly": noodly.noodly,
    "math_town": math_town.math_town,
    "math_undercroft": math_town.undercroft,
    "math_interior": math_town.interior,
    "eclipse": arenas.eclipse,
    "evil_forest": evil.evil_forest,
    "castle_godwin": evil.castle_godwin,
    "castle_godwin_lab": evil.castle_godwin_lab,
    "castle_godwin_throne": evil.castle_godwin_throne,
    "military_tower": military_tower.military_tower,
    "pirate_port": pirate_port.pirate_port,
    "ninja_village": ninja_village.ninja_village,
    "orbital": orbital.orbital,
    "orbital_truss": orbital.orbital_truss,
    "eureka": eureka.eureka,
    "eureka_heights": eureka.eureka_heights,
    "art": art_dimension.art,
    "art_sketchbook": art_dimension.art_sketchbook,
    "art_inkfall": art_dimension.art_inkfall,
    "art_stacks": art_quarters.art_stacks,
    "art_resonance": art_quarters.art_resonance,
    "art_stage": art_quarters.art_stage,
    "art_forge": art_quarters.art_forge,
    # The History dimension: eight eras on one road, from the first farms
    # to the mills (`history_eras.py`).
    "history_crescent": history_eras.history_crescent,
    "history_nile": history_eras.history_nile,
    "history_classical": history_eras.history_classical,
    "history_silk": history_eras.history_silk,
    "history_steppe": history_eras.history_steppe,
    "history_monsoon": history_eras.history_monsoon,
    "history_sail": history_eras.history_sail,
    "history_industrial": history_eras.history_industrial,
    # The History dimension, second pass: the places of the first people and
    # the first farmers, one to each floor of the grid (`history_origins.py`).
    "history_savanna": history_origins.history_savanna,
    "history_green_sahara": history_origins.history_green_sahara,
    "history_ice_age": history_origins.history_ice_age,
    "history_megalith": history_origins.history_megalith,
    "history_northwoods": history_origins.history_northwoods,
    "history_indus": history_origins.history_indus,
    "history_yellow_river": history_origins.history_yellow_river,
    "history_maize": history_origins.history_maize,
    "history_sahul": history_origins.history_sahul,
    "history_highlands": history_origins.history_highlands,
    "history_painted_cave": history_origins.history_painted_cave,
    # The History dimension, third pass: the Americas and Oceania grow east
    # to the medieval column (`history_americas_pacific.py`).
    "history_olmec": history_americas_pacific.history_olmec,
    "history_maya": history_americas_pacific.history_maya,
    "history_caribbean": history_americas_pacific.history_caribbean,
    "history_lapita": history_americas_pacific.history_lapita,
    "history_open_ocean": history_americas_pacific.history_open_ocean,
    "history_rapa_nui": history_americas_pacific.history_rapa_nui,
    # The History dimension: the Atlantic world (`history_atlantic.py`).
    "history_benin": history_atlantic.history_benin,
    "history_saint_domingue": history_atlantic.history_saint_domingue,
    "history_gold_coast": history_atlantic.history_gold_coast,
    # The History dimension: South America (`history_south_america.py`).
    "history_andes": history_south_america.history_andes,
    "history_supe": history_south_america.history_supe,
    # The History dimension: Southeast Asia (`history_southeast_asia.py`).
    "history_wallacea": history_southeast_asia.history_wallacea,
    "history_austronesia": history_southeast_asia.history_austronesia,
    "history_red_river": history_southeast_asia.history_red_river,
    "history_strait": history_southeast_asia.history_strait,
    "history_borobudur": history_southeast_asia.history_borobudur,
    "history_angkor": history_southeast_asia.history_angkor,
    # The History dimension: the coasts of East Asia (`history_east_asia_coast.py`).
    "history_jomon": history_east_asia_coast.history_jomon,
    "history_taiwan": history_east_asia_coast.history_taiwan,
    "history_gyeongju": history_east_asia_coast.history_gyeongju,
    "history_hangzhou": history_east_asia_coast.history_hangzhou,
    "history_heian": history_east_asia_coast.history_heian,
    "history_hanyang": history_east_asia_coast.history_hanyang,
    # The History dimension: Bengal and the cotton (`history_bengal.py`).
    "history_dhaka_river": history_bengal.history_dhaka_river,
    "history_calcutta": history_bengal.history_calcutta,
    "history_dhaka_spring": history_bengal.history_dhaka_spring,
    # The History dimension: Brazil and Amazonia (`history_brazil.py`).
    "history_marajo": history_brazil.history_marajo,
    "history_palmares": history_brazil.history_palmares,
    "history_rio_1888": history_brazil.history_rio_1888,
    # The History dimension: Japan after Heian (`history_japan.py`).
    "history_kamakura": history_japan.history_kamakura,
    "history_meiji": history_japan.history_meiji,
    # The History dimension: Central Africa (`history_central_africa.py`).
    "history_ishango": history_central_africa.history_ishango,
    "history_mbanza_kongo": history_central_africa.history_mbanza_kongo,
    "history_matamba": history_central_africa.history_matamba,
    "history_congo_river_1900": history_central_africa.history_congo_river_1900,
    # The History dimension: Australia and Aotearoa (`history_oceania.py`).
    "history_willandra": history_oceania.history_willandra,
    "history_aotearoa": history_oceania.history_aotearoa,
    "history_tonga": history_oceania.history_tonga,
    "history_waitangi": history_oceania.history_waitangi,
    "history_sydney_cove": history_oceania.history_sydney_cove,
    # Budj Bim, in Gunditjmara country (`history_budj_bim.py`).
    "history_budj_bim": history_budj_bim.history_budj_bim,
    # The History dimension: Micronesia (`history_micronesia.py`).
    "history_marianas": history_micronesia.history_marianas,
    "history_marshalls": history_micronesia.history_marshalls,
    "history_nan_madol": history_micronesia.history_nan_madol,
    "history_yap": history_micronesia.history_yap,
    "history_nauru": history_micronesia.history_nauru,
    "history_bikini": history_micronesia.history_bikini,
}


#: The layer the game draws in front of the play. A scene can have none.
FOREGROUND = "foreground"


#: Each theme this package publishes: the scenes, and the two states of the
#: sky of the two-state room look, which has its own art.
THEMES: tuple[str, ...] = (*SCENES, *room_look_sky.THEME_KEYS)

LAYERS: tuple[str, ...] = (*LAYER_SIZE, FOREGROUND)


def render(theme_key: str, layer_key: str, size: int | None = None) -> Image.Image | None:
    """The published picture of one layer of one scene. `size` is for a test
    or a quick look: a scene is the same picture at each size. `None` for a
    foreground the scene does not have."""
    if layer_key == FOREGROUND:
        return foregrounds.render(theme_key, size)
    if theme_key in room_look_sky.THEME_KEYS:
        return room_look_sky.render_look_layer(theme_key, layer_key)
    art = Art(size or LAYER_SIZE[layer_key], theme_key, layer_key)
    layer = SCENES[theme_key](layer_key, art)
    return art.publish(layer, blur=LAYER_BLUR[layer_key], opaque=layer_key == "sky")


#: The panel of each layer as the game draws it: `(panel scale, factor along,
#: factor up and down)`
#: (`RUNTIME_PARALLAX_LAYERS` in `ambition_render`).
RUNTIME = {
    "sky": (1.20, 0.10, 0.10),
    "far_backplate": (1.34, 0.20, 0.20),
    "near_background": (1.52, 0.42, 0.42),
    "foreground_atmosphere": (1.72, 0.60, 0.60),
    FOREGROUND: (2.20, 1.00, 0.10),
}


def view(layers: dict[str, Image.Image], size: tuple[int, int] = (1280, 720), camera: tuple[float, float] = (0.0, 0.0)) -> Image.Image:
    """What the game shows of a scene in a view of `size`. `camera` is where
    the camera is in its room: -1 is the left or the top, 1 the right or the
    bottom. This is the arithmetic of `sync_parallax_transform_to_camera`."""
    w, h = size
    out = Image.new("RGBA", size, (0, 0, 0, 255))
    for key, (panel_scale, factor, factor_y) in RUNTIME.items():
        if layers.get(key) is None:
            continue
        panel = max(w, h) * panel_scale
        travel = ((panel - w) * 0.5, (panel - h) * 0.5)
        centre = (panel * 0.5 + camera[0] * travel[0] * factor, panel * 0.5 + camera[1] * travel[1] * factor_y)
        image = layers[key].resize((int(panel), int(panel)), Image.BILINEAR)
        box = (int(centre[0] - w * 0.5), int(centre[1] - h * 0.5))
        out.alpha_composite(image.crop((box[0], box[1], box[0] + w, box[1] + h)))
    return out


#: The side of the flat backdrop, in pixels: the one picture a tier that draws
#: no parallax shows behind the play, fixed to the view (`ParallaxLayerAsset::Flat`
#: in `ambition_sprite_sheet`). Small, as the tier is for low-power machines.
FLAT_SIDE = 512


def flat(layers: dict[str, Image.Image | None]) -> Image.Image:
    """The flat backdrop of a scene: what a square view shows of it with the
    camera at the middle of its room, without the foreground (it is in front of
    the play, and a flat backdrop is behind it). Drawn at twice its size and
    made smaller, so its edges are as smooth as the layers'."""
    behind = {key: image for key, image in layers.items() if key != FOREGROUND}
    big = view(behind, (FLAT_SIDE * 2, FLAT_SIDE * 2))
    return big.resize((FLAT_SIDE, FLAT_SIDE), Image.LANCZOS)
