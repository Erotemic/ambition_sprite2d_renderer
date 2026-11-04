"""The terrain skin of each biome.

A room of the game is made of collision blocks: rectangles. A skin is the
art the game lays on them:

    fill     64 by 64 units, repeats each way: the inside of a block
    cap      64 by 20 units, repeats along a top edge that nothing covers.
             The surface a body stands on is `CAP_SURFACE` units below the
             top of the picture: what is above it (grass) stands over the
             edge.
    under    64 by 16 units, repeats along a bottom edge that nothing
             covers. The edge is `UNDER_EDGE` units below the top of the
             picture: what is below it hangs under the block.
    side     16 by 64 units, repeats down a left edge (the game mirrors it
             for a right edge): a shade that gives the block a round edge.
    oneway   64 by 16 units, repeats: a platform a body can jump up through.

A unit is a world unit of the game. Each picture has `PX_PER_UNIT` pixels to
the unit: the play camera shows a unit as two and a half pixels of a 1600 px
window.

Each picture repeats with no seam in the direction it is laid.

The fill is dark and has low contrast, and the cap has the one light line:
the top of the ground is what a player must see first.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

RGB = tuple[int, int, int]

PX_PER_UNIT = 2
SUPERSAMPLE = 4
#: Working pixels to the unit.
K = PX_PER_UNIT * SUPERSAMPLE

FILL = (64, 64)
CAP = (64, 20)
UNDER = (64, 16)
SIDE = (16, 64)
ONEWAY = (64, 16)

#: How far below the top of the cap picture the surface of the block is.
CAP_SURFACE = 4.0
#: How far below the top of the underside picture the bottom of the block is.
UNDER_EDGE = 4.0


@dataclass(frozen=True)
class Skin:
    key: str
    material: str
    base: RGB
    dark: RGB
    light: RGB
    accent: RGB
    cap: str
    cap_colour: RGB
    under: str
    oneway: str


SKINS: tuple[Skin, ...] = (
    # The lab is steel, not the teal of its air: the ground must not have the
    # colour of what is behind it.
    Skin("lab", "panel", (38, 54, 74), (14, 22, 36), (84, 112, 138), (120, 236, 220), "strip", (62, 84, 108), "pipes", "grate"),
    # The orbital station of the Science dimension: deck plates of painted
    # steel with a lit strip, a grate for a walkway; the same in its trusses.
    Skin("orbital", "panel", (58, 70, 90), (22, 28, 40), (120, 140, 162), (246, 176, 76), "strip", (92, 110, 132), "bolts", "grate"),
    Skin("orbital_truss", "panel", (52, 64, 86), (18, 24, 36), (112, 134, 158), (110, 220, 240), "strip", (86, 104, 128), "bolts", "grate"),
    # Eureka, the institute town of the Science dimension: red brick under a
    # coping of dressed sandstone, a slab of the same stone for a platform.
    Skin("eureka", "brick", (150, 78, 60), (62, 32, 26), (196, 122, 94), (232, 212, 168), "edge", (226, 208, 166), "lip", "slab"),
    # The space elevator's car and its stages: painted steel deck plates with
    # a lit strip, a grate for a walkway, red beacons.
    Skin("eureka_heights", "panel", (64, 76, 96), (22, 28, 40), (132, 150, 172), (255, 120, 92), "strip", (98, 116, 138), "bolts", "grate"),
    # The clean state of the two-state hub: pale marble with a line of gold.
    # The look of that room draws its own blocks, and this is what the room
    # has on a device that does not draw the look.
    # The lab with its power out: the same steel, darker, and the light of
    # its strip is the red of the alarm.
    Skin("alarm", "panel", (34, 37, 52), (9, 10, 18), (82, 88, 114), (255, 86, 68), "strip", (58, 60, 82), "pipes", "grate"),
    # The drains under the town: old brick, with moss where it is damp.
    Skin("undertown", "brick", (72, 66, 58), (22, 22, 22), (124, 112, 94), (96, 206, 172), "moss", (62, 112, 74), "pipes", "grate"),
    Skin("hub_clean", "block", (226, 220, 208), (150, 144, 138), (255, 252, 244), (226, 178, 86), "edge", (240, 234, 222), "lip", "slab"),
    # The corrupted state of the same hub: its stone rebuilt in dark voxels.
    # `two_state.py` draws both states; the fields here name its colours for
    # the parts that are the same in each biome (the ladder).
    Skin("hub_corrupt", "block", (20, 18, 52), (5, 5, 14), (100, 90, 190), (34, 224, 255), "edge", (199, 184, 255), "lip", "slab"),
    Skin("hub", "panel", (40, 40, 94), (15, 15, 46), (92, 94, 164), (255, 206, 140), "strip", (70, 70, 134), "lip", "grate"),
    Skin("basement", "brick", (88, 42, 32), (30, 13, 11), (146, 78, 54), (255, 150, 60), "plate", (58, 42, 40), "bolts", "grate"),
    # The vault of a boss: columns of black rock, with fire in some of the breaks.
    Skin("boss", "basalt", (70, 26, 38), (22, 7, 12), (132, 52, 64), (255, 112, 72), "plate", (40, 14, 20), "spikes", "grate"),
    Skin("cave", "rock", (48, 46, 90), (16, 15, 36), (94, 94, 152), (124, 222, 255), "moss", (46, 112, 112), "stalactites", "plank"),
    Skin("cove", "rock", (44, 78, 88), (12, 30, 40), (100, 150, 150), (255, 224, 170), "sand", (214, 190, 140), "weed", "plank"),
    # A town that sank: cut stone of many sizes, its corners worn, weed on it.
    Skin("water", "ruin", (30, 84, 104), (8, 34, 52), (82, 152, 162), (150, 240, 200), "moss", (36, 132, 108), "weed", "slab"),
    Skin("forest", "earth", (60, 46, 36), (24, 18, 14), (106, 86, 62), (236, 222, 120), "grass", (84, 140, 62), "roots", "plank"),
    # The land of the dinosaurs: red earth under deep green.
    Skin("primeval", "earth", (86, 56, 36), (34, 20, 12), (136, 98, 62), (255, 190, 90), "grass", (58, 146, 62), "roots", "plank"),
    # Mary-O's land: the ground blocks of an old platform game, in the pinks
    # of a magical girl, under mint icing.
    Skin("starlight", "candy", (236, 150, 186), (158, 86, 140), (255, 206, 222), (255, 240, 170), "frosting", (176, 232, 208), "lip", "slab"),
    # The desert of Mary-O's second world: the same ground blocks in the
    # colours of sandstone, under a lip of pale sand.
    Skin("stardune", "candy", (240, 186, 124), (172, 108, 78), (255, 226, 172), (255, 250, 214), "sand", (255, 236, 186), "lip", "slab"),
    # Under Mary-O's land: the brick of an old game's underground, in the
    # violet of the dark, with a line of magenta light on its edge.
    Skin("starless", "brick", (58, 46, 112), (17, 12, 40), (112, 96, 180), (255, 86, 170), "edge", (34, 26, 72), "spikes", "grate"),
    # Mary-O's castle: cut stone the colour of a plum, with a line of gold on
    # its edge. It is not red: the fire in the pits is. The void has no part in the ground: a body stands on what is whole.
    # The void, in Mary-O's land: a body with no light in it, and one thin
    # white line on each edge, as the void enemies have. No colour.
    Skin("void", "void", (8, 8, 9), (3, 3, 4), (244, 244, 244), (255, 255, 255), "rim", (246, 246, 246), "rim", "rim"),
    Skin("void_castle", "ruin", (104, 66, 116), (34, 18, 46), (170, 124, 176), (255, 206, 116), "edge", (138, 90, 146), "bolts", "slab"),
    # The Noodly Temple: noodles in a press, under marinara that runs down
    # the edge, with noodles that hang under each block.
    # The town of the Math dimension: pale limestone in courses, under a
    # curb with a blue line marked like a ruler.
    Skin("math_town", "block", (186, 172, 148), (118, 106, 90), (222, 210, 186), (78, 124, 186), "edge", (240, 234, 220), "lip", "slab"),
    # The gate hall under the Math town: the same limestone, in lamplight.
    # Inside the town's houses: a floor of terracotta tiles with a blue line.
    Skin("math_interior", "tile", (176, 108, 78), (110, 64, 46), (214, 150, 110), (78, 124, 186), "edge", (226, 200, 170), "lip", "slab"),
    Skin("math_undercroft", "block", (150, 134, 110), (74, 66, 58), (196, 178, 148), (214, 170, 84), "edge", (206, 194, 170), "lip", "slab"),
    Skin("noodly", "noodle", (160, 116, 58), (64, 34, 20), (226, 184, 106), (255, 222, 140), "sauce", (172, 44, 32), "noodles", "lasagne"),
    # The forest of the Evil dimension: black earth with dead grass on it,
    # and the red of the sky in its cracks.
    Skin("evil_forest", "earth", (46, 32, 32), (16, 10, 12), (86, 58, 52), (230, 70, 44), "grass", (74, 56, 40), "roots", "plank"),
    # The port of the pirate dimension: boards of weathered timber laid
    # flat, under the edge of a plank deck, with weed under a pier.
    Skin("pirate_port", "timber", (104, 76, 54), (42, 30, 22), (150, 114, 80), (214, 176, 108), "deck", (178, 140, 96), "weed", "plank"),
    # The village of the ninja dimension: packed earth with a kerb of round
    # stones, and a roof of grey tiles for a platform (a ridge to walk).
    Skin("ninja_village", "earth", (84, 68, 58), (34, 28, 26), (130, 110, 92), (206, 72, 52), "kerb", (138, 138, 132), "roots", "roof"),
    # Castle Godwin: the cold blue-grey blocks of a fortress, dark.
    Skin("castle_godwin", "block", (82, 92, 112), (28, 32, 44), (134, 146, 168), (200, 40, 32), "edge", (112, 122, 142), "bolts", "grate"),
    # The castle's lab: the same blocks, lit green by the vats.
    Skin("castle_godwin_lab", "block", (70, 88, 86), (22, 32, 30), (118, 150, 140), (120, 255, 150), "edge", (96, 120, 112), "bolts", "grate"),
    # The throne room: darker blocks, warmed by the red moon.
    Skin("castle_godwin_throne", "block", (78, 70, 84), (26, 22, 30), (130, 118, 134), (220, 50, 40), "edge", (108, 96, 112), "bolts", "slab"),
    # The tower of the Faction of Steel: riveted plates of gunmetal steel,
    # a deck edge with warning stripes of signal red, and a girder under it.
    Skin("military_tower", "deckplate", (74, 82, 88), (30, 34, 38), (124, 132, 136), (168, 56, 44), "hazard", (92, 98, 100), "girder", "grate"),
    # The islands in the sky are rock that broke off, not a wall that was laid.
    Skin("skybridge", "rock", (150, 164, 198), (86, 100, 142), (216, 224, 242), (255, 236, 150), "grass", (112, 178, 96), "roots", "slab"),
    Skin("open_sky", "rock", (176, 164, 150), (104, 92, 92), (232, 222, 204), (255, 240, 170), "grass", (126, 184, 92), "roots", "plank"),
    # The Art dimension (`backgrounds/art_dimension.py`). The surface: canvas
    # under a coat of paint in the three primaries that runs over the edge,
    # drops of paint under each block, and a palette for a platform.
    Skin("art", "canvas", (92, 72, 134), (38, 26, 66), (146, 120, 190), (255, 210, 50), "paint", (232, 54, 172), "drips", "palette"),
    # The Sketchbook Cliffs: the edges of the pages of a pad, under a line of
    # pencil, and a ruler for a platform.
    Skin("art_sketchbook", "paper", (190, 180, 160), (116, 108, 96), (232, 224, 204), (92, 94, 110), "pencil", (246, 241, 228), "lip", "ruler"),
    # The Inkfall Caverns: violet rock under living ink that runs down the
    # edge and glows, and drops of it under each block.
    Skin("art_inkfall", "rock", (58, 38, 102), (20, 12, 44), (110, 80, 170), (60, 220, 250), "ink", (246, 70, 200), "drips", "slab"),
    # The four quarters of the Art dimension (`backgrounds/art_quarters.py`).
    # The Story Stacks: books that lie in stacks, their spines to the view,
    # under the gilt edges of their pages; ribbons of bookmarks hang under
    # each block, and a shelf board is the platform.
    Skin("art_stacks", "books", (104, 62, 46), (40, 24, 20), (156, 104, 72), (222, 172, 70), "pages", (240, 226, 192), "ribbons", "shelf"),
    # The Resonant Reach: the black lacquer of a piano with keys of ivory in
    # it, under a rail of brass; a line of a stave is the platform.
    Skin("art_resonance", "keys", (34, 34, 52), (12, 12, 22), (88, 90, 120), (80, 230, 255), "brass", (214, 170, 80), "lip", "stave"),
    # The Amphitheatre: the black boards of a stage under an edge of gold
    # with footlights in it, a fringe of red velvet under each block, and a
    # catwalk for a platform.
    Skin("art_stage", "timber", (66, 40, 40), (24, 14, 18), (110, 70, 62), (236, 182, 70), "footlights", (236, 182, 70), "fringe", "catwalk"),
    # The Workshop Deeps: bricks fired in a kiln, a few of them glazed and
    # some scorched, under a plate of copper; a workbench is the platform.
    Skin("art_forge", "fired", (112, 54, 40), (40, 18, 14), (146, 80, 56), (255, 140, 50), "copper", (204, 116, 66), "bolts", "bench"),
    # The History dimension (`backgrounds/history_eras.py`), one era to each
    # skin. The Fertile Crescent: bricks of mud dried in the sun, with straw
    # in them and a few glazed in lapis, under a course of bricks on edge;
    # roots under each block, and a mat of bound reeds for a platform.
    Skin("history_crescent", "mudbrick", (150, 106, 70), (70, 48, 34), (196, 152, 106), (52, 84, 164), "bricks_on_edge", (198, 152, 102), "roots", "reed_mat"),
    # The Nile: dressed blocks of sandstone under a band of hieroglyphs
    # painted in lapis and red; a beam of palm log is the platform.
    Skin("history_nile", "block", (170, 134, 90), (88, 64, 42), (214, 182, 134), (40, 70, 160), "hieroglyphs", (222, 186, 130), "lip", "palm_log"),
    # The Classical Shore: slabs of marble with grey veins, under a band of
    # the key pattern (a meander) in terracotta; a marble lintel with its
    # dentils is the platform.
    Skin("history_classical", "marble", (172, 168, 160), (88, 88, 98), (222, 220, 214), (180, 82, 52), "meander", (234, 230, 222), "lip", "lintel"),
    # The Silk Road: dressed stone the colour of the dunes, under a course of
    # glazed tiles in turquoise and cobalt; a carved balcony rail of red
    # lacquer is the platform.
    Skin("history_silk", "block", (156, 102, 66), (74, 46, 32), (200, 150, 104), (40, 150, 140), "glazed", (48, 150, 160), "lip", "balcony"),
    # The Mongol Steppe: dark earth under a thick turf of grass; roots under
    # each block, and a pole wrapped in felt is the platform.
    Skin("history_steppe", "earth", (74, 58, 42), (30, 24, 18), (120, 100, 72), (64, 120, 200), "turf", (118, 150, 66), "roots", "felt"),
    # Timbuktu and the Monsoon Coast: mudbrick under plaster, with stones of
    # coral set in it, under a soft cap of white plaster; a beam of palm
    # wood with the ends of the toron under it is the platform.
    Skin("history_monsoon", "adobe", (150, 102, 62), (74, 48, 30), (214, 198, 170), (236, 186, 60), "plaster", (234, 218, 186), "lip", "toron"),
    # The Age of Sail: planks of a quay, wet and dark, under a beam bound
    # with rope; weed under each block, and the yard of a mast with its sail
    # furled is the platform.
    Skin("history_sail", "wet_planks", (92, 78, 62), (34, 30, 28), (142, 128, 104), (202, 160, 72), "rope_beam", (120, 94, 64), "weed", "yard"),
    # The Industrial Age: granite setts under an edge of riveted iron; the
    # flange of a girder under each block, and an iron lattice girder is the
    # platform.
    Skin("history_industrial", "cobbles", (96, 92, 92), (34, 32, 34), (142, 138, 134), (255, 200, 110), "iron", (80, 82, 90), "girder", "ironwork"),
    # The History dimension, second pass (`backgrounds/history_origins.py`),
    # one place to each skin. The Rift Valley: red earth that the sun baked
    # hard, in beds, under gold grass; a lashed log is the platform.
    Skin("history_savanna", "laterite", (144, 74, 44), (66, 32, 20), (196, 118, 72), (236, 196, 100), "grass", (206, 168, 80), "roots", "log"),
    # The Green Sahara: beds of soft sandstone under a thick green turf; a
    # mat of reeds is the platform.
    Skin("history_green_sahara", "laterite", (170, 132, 92), (82, 60, 42), (216, 182, 136), (176, 64, 44), "turf", (104, 156, 66), "roots", "reed_mat"),
    # The Ice Age: blue glacier ice under a cap of snow, with icicles under
    # each block; mammoth tusks lashed with hide are the platform.
    Skin("history_ice_age", "ice", (92, 140, 180), (34, 60, 98), (196, 226, 244), (236, 246, 255), "snow", (236, 242, 250), "icicles", "bone"),
    # The megalith builders: white chalk with rows of flints under the turf
    # of the downs; a lintel of sarsen stone is the platform.
    Skin("history_megalith", "chalk", (186, 182, 168), (90, 90, 86), (226, 224, 214), (52, 54, 62), "turf", (98, 146, 64), "roots", "sarsen"),
    # The north: grey granite under a cushion of moss; a plank of pine is
    # the platform.
    Skin("history_northwoods", "rock", (84, 92, 98), (30, 36, 40), (140, 150, 152), (206, 224, 176), "moss", (72, 106, 62), "roots", "plank"),
    # The Indus: fired bricks in English bond under a course of bricks on
    # edge; a plank is the platform.
    Skin("history_indus", "indus_brick", (170, 86, 56), (70, 34, 24), (214, 132, 90), (226, 196, 150), "bricks_on_edge", (196, 108, 72), "lip", "plank"),
    # The Yellow River: yellow loess with its upright joints under a crust of
    # the same silt; two poles of bamboo are the platform.
    Skin("history_yellow_river", "loess", (190, 150, 92), (98, 72, 44), (230, 200, 146), (150, 120, 80), "sand", (216, 182, 118), "roots", "bamboo"),
    # The first maize: a terrace wall of stones laid dry under the grass of
    # the field; a palm mat (a petate) is the platform.
    Skin("history_maize", "drystone", (112, 100, 88), (40, 36, 32), (170, 156, 138), (196, 186, 110), "grass", (128, 150, 62), "roots", "reed_mat"),
    # Sahul: deep red earth in beds under red sand with tufts of spinifex; a
    # lashed log is the platform.
    Skin("history_sahul", "laterite", (148, 62, 34), (66, 26, 16), (204, 110, 62), (240, 200, 140), "sand", (222, 134, 80), "roots", "log"),
    # The New Guinea highlands: wet clay of the swamp under moss; two poles
    # of bamboo are the platform.
    Skin("history_highlands", "wet_clay", (92, 76, 62), (34, 28, 24), (150, 132, 110), (196, 232, 206), "moss", (84, 138, 58), "roots", "bamboo"),
    # The painted cave: limestone under a crust of flowstone, with
    # stalactites under each block; a slab of the same rock is the platform.
    Skin("history_painted_cave", "rock", (122, 92, 70), (44, 30, 22), (188, 150, 116), (230, 170, 110), "flowstone", (214, 192, 160), "stalactites", "slab"),
    # The History dimension, third pass (`backgrounds/history_americas_pacific.py`).
    # The Olmec heartland: the coloured clays that the builders laid in
    # floors and mounds, in bands, under thick green grass; a column of
    # basalt laid along is the platform.
    Skin("history_olmec", "clay_layers", (128, 94, 66), (54, 38, 28), (176, 138, 98), (70, 150, 110), "grass", (96, 150, 62), "roots", "basalt_column"),
    # The Maya city: blocks of pale limestone under a frieze of red stucco
    # with bar-and-dot numbers in it (and the shell that is zero); a carved
    # beam of sapodilla wood is the platform.
    Skin("history_maya", "block", (168, 158, 136), (84, 78, 66), (208, 198, 176), (60, 140, 120), "maya_frieze", (176, 64, 46), "roots", "zapote"),
    # The Taino islands: pale beach rock of coral and shells under white
    # sand; a barbacoa (a frame of green sticks) is the platform.
    Skin("history_caribbean", "beachrock", (206, 196, 170), (120, 110, 92), (240, 234, 214), (40, 170, 180), "sand", (244, 234, 204), "lip", "barbacoa"),
    # The Lapita voyagers: the dark volcanic earth of a shore midden, with
    # sherds of stamped pots, shells and coral in it, under black sand; a
    # deck of poles on stilts is the platform.
    Skin("history_lapita", "midden", (84, 70, 62), (34, 28, 26), (140, 124, 110), (190, 100, 60), "sand", (96, 90, 86), "weed", "stilt_deck"),
    # The open ocean: the planks of a voyaging canoe sewn together with
    # cord of coconut fibre, wet, with the sea washing over the gunwale in
    # foam; weed under the hull, and a spar lashed with cord is the
    # platform. A room of this biome is mostly sea, and its blocks are hulls.
    Skin("history_open_ocean", "sewn_hull", (120, 86, 58), (44, 32, 26), (170, 132, 92), (220, 190, 130), "foam", (220, 234, 240), "weed", "spar"),
    # Rapa Nui: the yellow-brown tuff of Rano Raraku, with its dark grains
    # and the marks of the toki, under wind-blown turf; the fitted basalt
    # slabs of an ahu are the platform.
    Skin("history_rapa_nui", "tuff", (138, 120, 96), (58, 50, 42), (196, 178, 144), (214, 150, 60), "turf", (122, 148, 66), "roots", "ahu"),
    # The History dimension: the Atlantic world (`backgrounds/history_atlantic.py`).
    # Benin City: red laterite earth laid in courses with horizontal ridges,
    # as in the walls of the city and the palace, under a darker cap of
    # earth that was polished smooth; a squared beam of hardwood is the
    # platform.
    Skin("history_benin", "ridged_laterite", (164, 74, 46), (70, 30, 20), (212, 120, 78), (226, 176, 72), "polished_earth", (104, 42, 28), "roots", "hardwood_beam"),
    # Saint-Domingue: the red-brown earth of the north plain, baked hard in
    # beds, under a cap of grass with small yellow flowers; a rough plank,
    # sawn by hand and nailed on two cleats, is the platform.
    Skin("history_saint_domingue", "laterite", (150, 72, 44), (64, 28, 18), (198, 116, 72), (238, 196, 84), "grass", (112, 150, 58), "roots", "rough_plank"),
    # The fort on the Gold Coast: walls of stone under lime plaster washed
    # white, worn grey where the plaster has come off, under a smooth cap of
    # the same plaster; a heavy plank of timber, bolted, is the platform.
    Skin("history_gold_coast", "whitewash", (164, 162, 154), (78, 78, 78), (206, 204, 196), (120, 150, 140), "plaster", (238, 236, 228), "lip", "timber_plank"),
    # South America. The high Andes: grey-brown mountain rock, broken, under
    # a cap of tawny ichu grass in tussocks; a slab of flat stone on two
    # small stones is the platform.
    Skin("history_andes", "rock", (118, 108, 96), (44, 38, 34), (176, 166, 150), (214, 186, 120), "ichu", (198, 164, 98), "roots", "flagstone"),
    # Caral: walls of grey-tan stones laid in courses in clay, as the
    # builders of the pyramids laid them, with patches of the clay plaster
    # that once covered them; a cap of packed earth; a step of dressed stone
    # is the platform.
    Skin("history_supe", "caral_stone", (168, 152, 126), (74, 62, 48), (214, 202, 176), (204, 158, 84), "packed_earth", (164, 136, 102), "lip", "stone_step"),
    # Southeast Asia. Wallacea: pale grey limestone of the karst, cut by
    # the rain into flutes and pits, under a cap of dark green moss; a
    # shelf of the same limestone is the platform, and stalactites hang
    # under it.
    Skin("history_wallacea", "karst", (192, 190, 180), (74, 76, 72), (234, 232, 222), (118, 152, 82), "moss", (56, 94, 50), "stalactites", "limestone_shelf"),
    # The Austronesian islands: dark volcanic earth with bits of red scoria
    # and grey pumice in it, under a cap of grass with red flowers; two
    # poles of bamboo are the platform.
    Skin("history_austronesia", "volcanic_earth", (84, 66, 56), (30, 22, 20), (140, 112, 94), (226, 92, 70), "grass", (98, 152, 62), "roots", "bamboo"),
    # The Red River: grey-brown clay that the floods laid down in thin
    # layers, with rust along old root holes, under the mud of a paddy
    # with young rice in a film of water; a walkway of split bamboo on
    # cross poles is the platform.
    Skin("history_red_river", "river_clay", (150, 120, 90), (62, 46, 34), (200, 174, 134), (190, 96, 52), "young_rice", (112, 172, 72), "roots", "split_bamboo"),
    # The Strait: a wharf of dark wet timber on piles over the mud of the
    # Musi; the end of a deck of planks is its top, weed hangs under it,
    # and a walkway of planks on cross beams is the platform.
    Skin("history_strait", "wharf", (88, 66, 48), (34, 26, 20), (140, 112, 82), (196, 150, 80), "deck", (112, 84, 58), "weed", "plank_walk"),
    # Borobudur: grey andesite in courses, under a carved moulding of
    # the same stone with a band of lotus petals; a step of andesite is the
    # platform.
    Skin("history_borobudur", "andesite", (128, 128, 124), (56, 56, 58), (180, 178, 170), (108, 140, 86), "moulding", (150, 148, 140), "lip", "andesite_step"),
    # Angkor: blocks of red laterite full of pits, under a coping of
    # grey-pink sandstone; a lintel of the same sandstone is the platform.
    Skin("history_angkor", "laterite_blocks", (150, 76, 52), (66, 32, 22), (196, 120, 86), (200, 172, 160), "sandstone_coping", (184, 160, 154), "lip", "sandstone_lintel"),
    # Jomon: the dark earth of a chestnut forest of north Japan, full of
    # roots and small stones, under a cap of moss with fallen leaves of
    # autumn on it; a split log is the platform.
    Skin("history_jomon", "forest_earth", (78, 58, 40), (34, 24, 18), (128, 98, 68), (196, 96, 40), "leaf_litter", (92, 112, 52), "roots", "split_log"),
    # Taiwan: grey-green schist of the Central Range in thin layers that
    # slant, with veins of quartz, under a cap of grass; a slab of dark
    # slate is the platform.
    Skin("history_taiwan", "schist", (106, 118, 104), (40, 46, 42), (162, 172, 152), (232, 214, 130), "grass", (96, 150, 64), "roots", "slate_slab"),
    # Gyeongju: large dressed blocks of speckled granite, as Silla built
    # its kerbs and its observatory, under a cap of short turf; a step of
    # the same granite is the platform.
    Skin("history_gyeongju", "granite_blocks", (172, 164, 152), (72, 66, 62), (216, 210, 198), (104, 128, 70), "turf", (106, 148, 66), "lip", "granite_step"),
    # Hangzhou: slabs of grey bluestone, as the Song paved the causeways
    # of West Lake, under a cap of moss with willow catkins on it; a
    # wooden walk with a balustrade is the platform.
    Skin("history_hangzhou", "bluestone_paving", (112, 118, 120), (42, 46, 50), (166, 172, 172), (132, 168, 84), "moss_catkin", (96, 134, 64), "lip", "balustrade_walk"),
    # Heian-kyo: white gravel raked in parallel lines over dark earth, as
    # in the courtyard of a mansion, under a cap of moss with red maple
    # leaves on it; the edge of a veranda of cypress is the platform.
    Skin("history_heian", "raked_gravel", (160, 156, 144), (48, 38, 32), (212, 208, 196), (196, 62, 40), "moss_maple", (88, 120, 56), "lip", "engawa"),
    # Hanyang: long blocks of pale granite dressed with fine tool marks, as
    # in the terraces of Gyeongbokgung, under a cap of grass trimmed short;
    # a step of the terrace is the platform.
    Skin("history_hanyang", "palace_granite", (160, 160, 154), (62, 62, 62), (212, 212, 204), (60, 132, 104), "trimmed_grass", (92, 140, 60), "lip", "terrace_step"),
    # Dhaka on the Buriganga: dark silt of the river laid in thin layers,
    # under a cap of lush wet grass; a walk of bamboo poles on crossed
    # bamboo legs is the platform.
    Skin("history_dhaka_river", "river_silt", (86, 74, 60), (36, 30, 24), (140, 124, 98), (226, 214, 180), "delta_grass", (92, 134, 58), "roots", "bamboo_walk"),
    # Calcutta: courses of red laterite blocks with bands of thin brick
    # between them, under a cap of grass; a stone step of a river ghat is
    # the platform.
    Skin("history_calcutta", "laterite_brick", (146, 74, 50), (60, 28, 20), (204, 124, 84), (232, 186, 70), "grass", (98, 138, 60), "roots", "ghat_step"),
    # Dhaka in spring: red brick paving laid in a basket weave, under a cap
    # of trimmed grass; a step of pale stone on a brick riser, as at Curzon
    # Hall, is the platform.
    Skin("history_dhaka_spring", "brick_paving", (166, 72, 52), (66, 30, 24), (214, 124, 92), (236, 150, 40), "trimmed_grass", (98, 146, 62), "lip", "hall_step"),
    # Great slabs, each with one sign cut in it that gives a little light.
    Skin("eclipse", "monolith", (30, 34, 86), (10, 12, 36), (72, 78, 152), (92, 232, 200), "edge", (44, 50, 112), "lip", "slab"),
)


def _mix(a, b, t: float) -> RGB:
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))  # type: ignore[return-value]


def _seed(*parts: object) -> int:
    import hashlib

    return int.from_bytes(hashlib.blake2b(":".join(map(str, parts)).encode(), digest_size=8).digest(), "little")


class Tile:
    """A picture of `w` by `h` units in work. `wrap_x` and `wrap_y` say in
    which directions a shape that goes off one edge comes in at the other."""

    def __init__(self, size: tuple[int, int], wrap_x: bool, wrap_y: bool, *seed: object) -> None:
        self.w, self.h = size
        self.wrap_x, self.wrap_y = wrap_x, wrap_y
        self.W, self.H = self.w * K, self.h * K
        self.rng = random.Random(_seed(*seed))
        self.np_rng = np.random.default_rng(_seed(*seed) % (2**63))
        self.rgb = np.zeros((self.H, self.W, 3), dtype=np.float32)
        self.alpha = np.zeros((self.H, self.W), dtype=np.float32)
        ys, xs = np.mgrid[0 : self.H, 0 : self.W]
        #: The place of each pixel, in units.
        self.x = (xs + 0.5) / K
        self.y = (ys + 0.5) / K

    # -- masks --------------------------------------------------------------

    def mask(self, draw: Callable[[ImageDraw.ImageDraw, float, float], None], blur: float = 0.0) -> np.ndarray:
        """The mask that `draw(pen, dx, dy)` makes. It is called one time for
        each copy a wrap needs, with the offset of that copy in pixels."""
        image = Image.new("L", (self.W, self.H), 0)
        pen = ImageDraw.Draw(image)
        for dx in (-self.W, 0, self.W) if self.wrap_x else (0,):
            for dy in (-self.H, 0, self.H) if self.wrap_y else (0,):
                draw(pen, dx, dy)
        if blur > 0.0:
            image = self._blur(image, blur)
        return np.asarray(image, dtype=np.float32) / 255.0

    def _blur(self, image: Image.Image, units: float) -> Image.Image:
        """Blur that wraps in the directions the tile wraps in."""
        pad_x = self.W if self.wrap_x else 0
        pad_y = self.H if self.wrap_y else 0
        if pad_x or pad_y:
            wide = Image.new("L", (self.W + 2 * pad_x, self.H + 2 * pad_y))
            for ix in range(-1 if pad_x else 0, 2 if pad_x else 1):
                for iy in range(-1 if pad_y else 0, 2 if pad_y else 1):
                    wide.paste(image, (pad_x + ix * self.W, pad_y + iy * self.H))
            wide = wide.filter(ImageFilter.GaussianBlur(units * K))
            return wide.crop((pad_x, pad_y, pad_x + self.W, pad_y + self.H))
        return image.filter(ImageFilter.GaussianBlur(units * K))

    def noise(self, cells_x: int, cells_y: int, octaves: int = 3) -> np.ndarray:
        """Noise 0..1 that repeats with the tile."""
        total = np.zeros((self.H, self.W), dtype=np.float32)
        amplitude, norm = 1.0, 0.0
        for octave in range(octaves):
            cx, cy = cells_x * 2**octave, cells_y * 2**octave
            grid = self.np_rng.random((cy, cx), dtype=np.float32)
            fx, fy = self.x / self.w * cx, self.y / self.h * cy
            x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
            tx, ty = fx - x0, fy - y0
            tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
            a = grid[y0 % cy, x0 % cx]
            b = grid[y0 % cy, (x0 + 1) % cx]
            c = grid[(y0 + 1) % cy, x0 % cx]
            d = grid[(y0 + 1) % cy, (x0 + 1) % cx]
            total += ((a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty) * amplitude
            norm += amplitude
            amplitude *= 0.5
        return total / norm

    def profile(self, cells: int, octaves: int = 3) -> np.ndarray:
        """Noise 0..1 along x only, that repeats: one value for each column."""
        total = np.zeros(self.W, dtype=np.float32)
        amplitude, norm = 1.0, 0.0
        xs = (np.arange(self.W) + 0.5) / self.W
        for octave in range(octaves):
            c = cells * 2**octave
            grid = self.np_rng.random(c, dtype=np.float32)
            f = xs * c
            i = np.floor(f).astype(int)
            t = f - i
            t = t * t * (3 - 2 * t)
            total += (grid[i % c] * (1 - t) + grid[(i + 1) % c] * t) * amplitude
            norm += amplitude
            amplitude *= 0.5
        return total / norm

    # -- paint --------------------------------------------------------------

    def put(self, mask: np.ndarray, colour, alpha: float = 1.0) -> None:
        cover = np.clip(mask * alpha, 0.0, 1.0)
        out = cover + self.alpha * (1.0 - cover)
        weight = np.where(out > 1e-6, cover / np.maximum(out, 1e-6), 0.0)[:, :, None]
        self.rgb = self.rgb * (1.0 - weight) + np.asarray(colour, dtype=np.float32) * weight
        self.alpha = out

    def tone(self, amount: np.ndarray) -> None:
        """Make the colour lighter (amount over 0) or darker (under 0)."""
        self.rgb = np.clip(self.rgb * (1.0 + amount[:, :, None]), 0.0, 255.0)

    def publish(self, supersample: int = SUPERSAMPLE) -> Image.Image:
        """The picture to publish. It is made `supersample` times smaller
        than the work: a smaller number gives more pixels to the unit."""
        pre = np.dstack([self.rgb * self.alpha[:, :, None], self.alpha])
        s = supersample
        small = pre.reshape(self.H // s, s, self.W // s, s, 4).mean(axis=(1, 3))
        a = small[:, :, 3:4]
        # An empty pixel has the mean colour of the picture, so a sampler that
        # mixes it in adds no dark line.
        full = a[:, :, 0] > 0.5
        mean = (small[:, :, :3][full] / a[full]).mean(axis=0) if full.any() else np.zeros(3)
        colour = np.where(a > 4e-3, small[:, :, :3] / np.maximum(a, 1e-4), mean)
        out = np.dstack([np.clip(colour, 0, 255), np.clip(a * 255.0, 0, 255)])
        return Image.fromarray(np.rint(out).astype(np.uint8), "RGBA")


def _box(pen: ImageDraw.ImageDraw, dx: float, dy: float, x0: float, y0: float, x1: float, y1: float, value: int = 255) -> None:
    pen.rectangle([x0 * K + dx, y0 * K + dy, x1 * K + dx - 1, y1 * K + dy - 1], fill=value)


def _dot(pen: ImageDraw.ImageDraw, dx: float, dy: float, x: float, y: float, r: float, value: int = 255, ry: float | None = None) -> None:
    ry = r if ry is None else ry
    pen.ellipse([(x - r) * K + dx, (y - ry) * K + dy, (x + r) * K + dx, (y + ry) * K + dy], fill=value)


def _poly(pen: ImageDraw.ImageDraw, dx: float, dy: float, pts, value: int = 255) -> None:
    pen.polygon([(x * K + dx, y * K + dy) for x, y in pts], fill=value)


def _line(pen: ImageDraw.ImageDraw, dx: float, dy: float, pts, width: float, value: int = 255) -> None:
    pen.line([(x * K + dx, y * K + dy) for x, y in pts], fill=value, width=max(1, int(round(width * K))), joint="curve")


# ---------------------------------------------------------------------------
# Fills
# ---------------------------------------------------------------------------


def _courses(tile: Tile, skin: Skin, row_h: float, unit_w: float, joint: float, bevel: float) -> None:
    """Laid units in rows, each row half a unit along from the one above:
    bricks or cut blocks."""
    rows = int(round(tile.h / row_h))
    count = int(round(tile.w / unit_w))
    tile.put(np.ones_like(tile.alpha), skin.dark)
    for row in range(rows):
        for i in range(count):
            x0 = i * unit_w + (unit_w * 0.5 if row % 2 else 0.0)
            y0 = row * row_h
            tone = tile.rng.uniform(-0.16, 0.14)
            colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.6)
            body = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + joint, y0 + joint, x0 + unit_w - joint, y0 + row_h - joint))
            tile.put(body, colour)
            top = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + joint, y0 + joint, x0 + unit_w - joint, y0 + joint + bevel))
            left = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + joint, y0 + joint, x0 + joint + bevel, y0 + row_h - joint))
            tile.put(np.maximum(top, left), skin.light, 0.30)
            low = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + joint, y0 + row_h - joint - bevel, x0 + unit_w - joint, y0 + row_h - joint))
            tile.put(low, skin.dark, 0.35)


def breakable_brick(skin: Skin) -> Image.Image:
    """Draw loose masonry in the room palette, with open joints and cracks."""
    tile = Tile((32, 32), True, True, skin.key, "breakable_brick")
    tile.put(np.ones_like(tile.alpha), skin.dark)
    for row, y in enumerate((1, 17)):
        for x in ((1, 17) if row == 0 else (-7, 9, 25)):
            left, right = max(1, x), min(30, x + 13)
            body = tile.mask(lambda p, dx, dy: _box(p, dx, dy, left, y, right + 1, y + 13))
            tile.put(body, _mix(skin.base, skin.light, 0.28))
            top = tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(left, y), (right, y)], 1.0))
            tile.put(top, skin.light)
            edge = tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(right, y + 1), (right, y + 12)], 1.0))
            tile.put(edge, _mix(skin.base, skin.dark, 0.45))
    for points in ([(22, 3), (20, 7), (22, 10)], [(13, 20), (15, 24), (13, 28)]):
        crack = tile.mask(lambda p, dx, dy: _line(p, dx, dy, points, 1.0))
        tile.put(crack, skin.dark)
    return tile.publish()


def fill(skin: Skin) -> Image.Image:
    tile = Tile(FILL, True, True, skin.key, "fill")
    rng = tile.rng
    if skin.material == "panel":
        tile.put(np.ones_like(tile.alpha), skin.dark)
        for px in range(2):
            for py in range(2):
                x0, y0 = px * 32.0, py * 32.0
                tone = rng.uniform(-0.10, 0.10)
                colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 2.0)
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.6, y0 + 0.6, x0 + 31.4, y0 + 31.4)), colour)
                edge = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 0.6, y0 + 0.6, x0 + 31.4, y0 + 1.2), _box(p, dx, dy, x0 + 0.6, y0 + 0.6, x0 + 1.2, y0 + 31.4)))
                tile.put(edge, skin.light, 0.38)
                low = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 0.6, y0 + 30.8, x0 + 31.4, y0 + 31.4), _box(p, dx, dy, x0 + 30.8, y0 + 0.6, x0 + 31.4, y0 + 31.4)))
                tile.put(low, skin.dark, 0.5)
                rivets = tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x0 + cx, y0 + cy, 0.75) for cx in (3.2, 28.8) for cy in (3.2, 28.8)])
                tile.put(rivets, skin.light, 0.55)
                kind = px + py * 2
                if kind == 0:
                    slats = tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x0 + 8, y0 + 9 + k * 3.2, x0 + 24, y0 + 10.4 + k * 3.2) for k in range(5)])
                    tile.put(slats, skin.dark, 0.5)
                elif kind == 1:
                    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 7, y0 + 15.3, x0 + 25, y0 + 16.7)), skin.dark, 0.5)
                    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 21, y0 + 15.5, x0 + 24, y0 + 16.5)), skin.accent, 0.6)
                elif kind == 2:
                    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x0 + 6, y0 + 24), (x0 + 16, y0 + 24), (x0 + 22, y0 + 18), (x0 + 22, y0 + 7)], 0.8)), skin.dark, 0.4)
        tile.tone((tile.noise(4, 4, 3) - 0.5) * 0.14)
    elif skin.material == "brick":
        _courses(tile, skin, 8.0, 16.0, 0.45, 0.45)
        tile.tone((tile.noise(3, 3, 4) - 0.55) * 0.34)
    elif skin.material == "candy":
        # Square blocks with round corners, each with a light top left and a
        # dark low right: the ground of an old platform game. One in five
        # has a star pressed in it.
        tile.put(np.ones_like(tile.alpha), skin.dark)
        for bx in range(4):
            for by in range(4):
                x0, y0 = bx * 16.0, by * 16.0
                tone = rng.uniform(-0.10, 0.10)
                colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.4)

                def block(p, dx, dy, grow=0.0):
                    p.rounded_rectangle(((x0 + 0.6 - grow) * K + dx, (y0 + 0.6 - grow) * K + dy, (x0 + 15.4 + grow) * K + dx, (y0 + 15.4 + grow) * K + dy),
                                        radius=2.6 * K, fill=255)

                body = tile.mask(block)
                tile.put(body, colour)
                lit = body * np.clip(1.0 - tile.mask(lambda p, dx, dy: p.rounded_rectangle(((x0 + 1.9) * K + dx, (y0 + 1.9) * K + dy, (x0 + 16.6) * K + dx, (y0 + 16.6) * K + dy), radius=2.6 * K, fill=255)), 0.0, 1.0)
                tile.put(lit, skin.light, 0.75)
                low = body * np.clip(1.0 - tile.mask(lambda p, dx, dy: p.rounded_rectangle(((x0 - 0.6) * K + dx, (y0 - 0.6) * K + dy, (x0 + 14.1) * K + dx, (y0 + 14.1) * K + dy), radius=2.6 * K, fill=255)), 0.0, 1.0)
                tile.put(low, skin.dark, 0.55)
                if (bx, by) in ((0, 1), (2, 3), (3, 0)):
                    cx, cy = x0 + 8.0, y0 + 8.2
                    star = [(cx + (3.6 if k % 2 == 0 else 1.6) * math.cos(math.radians(-90 + k * 36)), cy + (3.6 if k % 2 == 0 else 1.6) * math.sin(math.radians(-90 + k * 36))) for k in range(10)]
                    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x + 0.5, y + 0.5) for x, y in star])), skin.dark, 0.45)
                    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, star)), skin.accent, 0.85)
                else:
                    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x0 + cx, y0 + cy, 0.7) for cx, cy in ((4.2, 4.2), (11.8, 11.8))]), skin.dark, 0.30)
        tile.tone((tile.noise(3, 3, 3) - 0.5) * 0.08)
    elif skin.material == "tile":
        # Glazed square tiles in grout, light and dark by turns, and a small
        # diamond of the accent where four of them meet: a floor indoors.
        tile.put(np.ones_like(tile.alpha), skin.dark)
        for bx in range(4):
            for by in range(4):
                x0, y0 = bx * 16.0, by * 16.0
                colour = skin.base if (bx + by) % 2 == 0 else _mix(skin.base, skin.light, 0.45)
                colour = _mix(colour, skin.dark, rng.uniform(0.0, 0.10))
                body = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.6, y0 + 0.6, x0 + 15.4, y0 + 15.4))
                tile.put(body, colour)
                glaze = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.6, y0 + 0.6, x0 + 15.4, y0 + 1.6))
                tile.put(glaze, skin.light, 0.40)
                if (bx + by) % 2 == 0:
                    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x0, y0 - 2.2), (x0 + 2.2, y0), (x0, y0 + 2.2), (x0 - 2.2, y0)])), skin.accent, 0.9)
        tile.tone((tile.noise(3, 3, 3) - 0.5) * 0.10)
    elif skin.material == "block":
        _courses(tile, skin, 16.0, 32.0, 0.5, 0.7)
        cracks = tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, y), (x + a, y + 3), (x + a - 1.5, y + 7)], 0.3) for x, y, a in [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(-3, 3)) for _ in range(6)]])
        tile.put(cracks, skin.dark, 0.55)
        tile.tone((tile.noise(3, 3, 4) - 0.5) * 0.22)
    elif skin.material == "basalt":
        # Columns of rock that stand side by side, each with a round face.
        # Each column is broken across at its own heights: the top of each
        # piece is a light facet, and the fire is in a few of the breaks.
        tile.put(np.ones_like(tile.alpha), skin.dark)
        widths = [14.0, 9.0, 16.0, 11.0, 14.0]
        x0 = 0.0
        hot = []
        for width in widths:
            breaks = sorted(rng.uniform(0.0, 64.0) for _ in range(2))
            if breaks[1] - breaks[0] < 14.0:
                breaks[1] = breaks[0] + 14.0 + rng.uniform(0.0, 20.0)
            tone = rng.uniform(-0.18, 0.14)
            colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.5)
            for k, top in enumerate(breaks):
                low = breaks[(k + 1) % len(breaks)] + (64.0 if k + 1 == len(breaks) else 0.0)
                slant = rng.uniform(1.2, 2.6) * rng.choice([-1.0, 1.0])
                peak = rng.uniform(0.3, 0.7)
                # The top is two slopes that meet at a point: a broken end.
                shape = [(x0 + 0.6, top + 2.4 + slant), (x0 + width * peak, top + 0.6), (x0 + width - 0.6, top + 2.4 - slant), (x0 + width - 0.6, low - 0.5), (x0 + 0.6, low - 0.5)]
                body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, shape))
                tile.put(body, colour)
                # Round: light on the left third, shade to the right.
                across = ((tile.x - x0) % 64.0) / width
                tile.put(body * np.clip(1.0 - np.abs(across - 0.26) / 0.22, 0.0, 1.0), skin.light, 0.22)
                tile.put(body * np.clip((across - 0.55) / 0.45, 0.0, 1.0), skin.dark, 0.55)
                facet = [shape[0], shape[1], shape[2], (shape[2][0], shape[2][1] + 2.2), (shape[1][0], shape[1][1] + 3.4), (shape[0][0], shape[0][1] + 2.2)]
                tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, facet)), skin.light, 0.34)
                if rng.random() < 0.3:
                    hot.append([(shape[0][0], shape[0][1] - 0.5), (shape[1][0], shape[1][1] - 0.5), (shape[2][0], shape[2][1] - 0.5)])
            x0 += width
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 1.2) for pts in hot], blur=1.4), skin.accent, 0.42)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.4) for pts in hot]), _mix(skin.accent, (255, 230, 190), 0.35), 0.80)
        tile.tone((tile.noise(5, 5, 4) - 0.5) * 0.30)
    elif skin.material == "monolith":
        # Two rows of great slabs. Each slab has one sign cut in it.
        tile.put(np.ones_like(tile.alpha), skin.dark)
        signs, dust = [], []
        for row in range(2):
            for i in range(2):
                x0, y0 = i * 32.0 + (16.0 if row else 0.0), row * 32.0
                tone = rng.uniform(-0.12, 0.10)
                colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.6)
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.5, y0 + 0.5, x0 + 31.5, y0 + 31.5)), colour)
                tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 0.5, y0 + 0.5, x0 + 31.5, y0 + 1.3), _box(p, dx, dy, x0 + 0.5, y0 + 0.5, x0 + 1.3, y0 + 31.5))), skin.light, 0.32)
                tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 0.5, y0 + 30.7, x0 + 31.5, y0 + 31.5), _box(p, dx, dy, x0 + 30.7, y0 + 0.5, x0 + 31.5, y0 + 31.5))), skin.dark, 0.5)
                # A panel that is cut a little into the face of the slab.
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 5.0, y0 + 5.0, x0 + 27.0, y0 + 27.0)), skin.dark, 0.22)
                tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 5.0, y0 + 26.4, x0 + 27.0, y0 + 27.0), _box(p, dx, dy, x0 + 26.4, y0 + 5.0, x0 + 27.0, y0 + 27.0))), skin.light, 0.22)
                signs.append((x0 + 16.0, y0 + 16.0, row * 2 + i))
        def sign(p, dx, dy, cx, cy, kind, width):
            if kind == 0:
                _dot(p, dx, dy, cx, cy, 5.2)
                _dot(p, dx, dy, cx, cy, 5.2 - width, value=0)
                _dot(p, dx, dy, cx, cy, 1.0)
            elif kind == 1:
                _line(p, dx, dy, [(cx - 5.0, cy + 3.5), (cx, cy - 4.5), (cx + 5.0, cy + 3.5)], width)
                _line(p, dx, dy, [(cx - 2.6, cy + 5.2), (cx + 2.6, cy + 5.2)], width)
            elif kind == 2:
                _line(p, dx, dy, [(cx - 5.2, cy), (cx + 5.2, cy)], width)
                _line(p, dx, dy, [(cx, cy - 5.2), (cx, cy + 5.2)], width)
                _dot(p, dx, dy, cx + 3.6, cy - 3.6, 0.8)
            else:
                # A moon in front of a sun: the sign of this place.
                _dot(p, dx, dy, cx, cy, 5.0)
                _dot(p, dx, dy, cx + 2.2, cy - 1.2, 4.3, value=0)
                _dot(p, dx, dy, cx + 2.6, cy - 1.4, 0.9)
        tile.put(tile.mask(lambda p, dx, dy: [sign(p, dx, dy, cx, cy, kind, 1.3) for cx, cy, kind in signs], blur=1.2), skin.accent, 0.22)
        tile.put(tile.mask(lambda p, dx, dy: [sign(p, dx, dy, cx, cy, kind, 0.7) for cx, cy, kind in signs]), _mix(skin.accent, skin.base, 0.35), 0.62)
        dust = [(rng.uniform(0, 64), rng.uniform(0, 64)) for _ in range(26)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.28) for x, y in dust]), skin.light, 0.5)
        tile.tone((tile.noise(3, 3, 4) - 0.5) * 0.20)
    elif skin.material == "ruin":
        # Cut stone of many sizes in rows of many heights. The corners are
        # worn round, and weed is in the damp of the joints.
        tile.put(np.ones_like(tile.alpha), skin.dark)
        y0 = 0.0
        stones = []
        for row_h in (13.0, 19.0, 11.0, 21.0):
            x0 = rng.uniform(0.0, 12.0)
            end = x0 + 64.0
            while x0 < end - 1.0:
                width = min(rng.choice([10.0, 14.0, 18.0, 24.0]), end - x0)
                if end - (x0 + width) < 7.0:
                    width = end - x0
                stones.append((x0, y0, width, row_h, rng.uniform(-0.2, 0.16), rng.uniform(1.2, 2.4)))
                x0 += width
            y0 += row_h
        for x0, sy, width, row_h, tone, worn in stones:
            colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.5)
            # A box with a blur, cut at half: its corners come out round.
            soft = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.7, sy + 0.7, x0 + width - 0.7, sy + row_h - 0.7), blur=worn * 0.5)
            body = np.clip((soft - 0.5) * 6.0 + 0.5, 0.0, 1.0)
            tile.put(body, colour)
            tile.put(body * np.clip(1.0 - (tile.y - sy) % 64.0 / 2.6, 0.0, 1.0) * ((tile.y - sy) % 64.0 < row_h), skin.light, 0.24)
            tile.put(body * np.clip(((tile.y - sy) % 64.0 - (row_h - 3.0)) / 3.0, 0.0, 1.0) * ((tile.y - sy) % 64.0 < row_h), skin.dark, 0.30)
        growth = np.clip((tile.noise(4, 4, 3) - 0.56) * 7.0, 0.0, 1.0) * (1.0 - tile.alpha * 0.0)
        joints = 1.0 - np.clip(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x0 + 1.6, sy + 1.6, x0 + width - 1.6, sy + row_h - 1.6) for x0, sy, width, row_h, _t, _w in stones], blur=1.0), 0.0, 1.0)
        tile.put(growth * (0.35 + 0.65 * joints), skin.cap_colour, 0.55)
        shells = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.5, 0.95)) for _ in range(12)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y + 0.25, r) for x, y, r in shells]), skin.dark, 0.6)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r * 0.8) for x, y, r in shells]), _mix(skin.light, (236, 232, 214), 0.5), 0.85)
        tile.tone((tile.noise(3, 3, 4) - 0.5) * 0.22)
    elif skin.material == "noodle":
        # Noodles in a press: rows of strands that go along, each with a slow
        # wave. A wave has a whole number of turns in the tile, and the rows
        # fill its height, so the picture repeats each way.
        tile.put(np.ones_like(tile.alpha), skin.dark)
        rows = 16
        pitch = FILL[1] / rows
        for row in range(rows):
            turns = rng.choice([1, 2, 2, 3])
            phase = rng.uniform(0.0, math.tau)
            swing = rng.uniform(0.35, 1.0)
            y0 = (row + 0.5) * pitch
            tone = rng.uniform(-0.20, 0.12)
            colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.5)
            pts = [(x, y0 + swing * math.sin(phase + turns * math.tau * x / FILL[0])) for x in np.linspace(-4.0, FILL[0] + 4.0, 73)]
            tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, pts, pitch * 0.80)), colour)
            tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x, y - pitch * 0.22) for x, y in pts], pitch * 0.16)), skin.light, 0.34)
            tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x, y + pitch * 0.30) for x, y in pts], pitch * 0.18)), skin.dark, 0.40)
        # Noodles that lie over the rows: a short strand that goes from one
        # row up to the row over it, with a round end.
        for _ in range(7):
            x0, row = rng.uniform(0, 64), rng.randrange(rows)
            span, lift = rng.uniform(12.0, 22.0), rng.choice([-1.0, 1.0]) * pitch * rng.choice([1.0, 2.0])
            y0 = (row + 0.5) * pitch
            over = [(x0 + span * t, y0 + lift * (t * t * (3.0 - 2.0 * t))) for t in np.linspace(0.0, 1.0, 17)]
            colour = _mix(skin.base, skin.light, rng.uniform(0.25, 0.6))
            for oy in (-FILL[1], 0.0, FILL[1]):
                pts = [(x, y + oy) for x, y in over]
                tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x, y + pitch * 0.34) for x, y in pts], pitch * 0.80)), skin.dark, 0.5)
                tile.put(tile.mask(lambda p, dx, dy: (_line(p, dx, dy, pts, pitch * 0.80), _dot(p, dx, dy, *pts[0], pitch * 0.40), _dot(p, dx, dy, *pts[-1], pitch * 0.40))), colour)
                tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x, y - pitch * 0.22) for x, y in pts], pitch * 0.16)), skin.light, 0.45)
        # A noodle end here and there, where a strand is cut: a round face.
        ends = [(rng.uniform(0, 64), (rng.randrange(rows) + 0.5) * pitch) for _ in range(7)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, pitch * 0.42) for x, y in ends]), _mix(skin.base, skin.light, 0.5))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, pitch * 0.16) for x, y in ends]), skin.dark, 0.55)
        tile.tone((tile.noise(3, 3, 3) - 0.5) * 0.20)
    elif skin.material == "canvas":
        # Canvas on a stretcher: a fine weave, and under-painting in broad
        # strokes of the primaries, dull, so the cap is what shows.
        tile.put(np.ones_like(tile.alpha), skin.base)
        weave = np.sin(tile.x * math.pi * 2.0) * np.sin(tile.y * math.pi * 2.0)
        tile.tone(weave * 0.07)
        for colour in ((232, 54, 172), (40, 200, 236), (255, 210, 50)):
            strokes = []
            for _ in range(2):
                x, y0 = rng.uniform(0, 64), rng.uniform(0, 64)
                length, rise = rng.uniform(18.0, 34.0), rng.uniform(-6.0, 6.0)
                strokes.append(([(x + length * t, y0 + rise * t + math.sin(t * 6.0) * 1.2) for t in np.linspace(0.0, 1.0, 13)], rng.uniform(3.0, 6.0)))
            mask = tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, w) for pts, w in strokes], blur=0.6)
            tile.put(mask, _mix(skin.base, colour, 0.30), 0.55)
            # The bristles of the brush leave lines along the stroke.
            tile.tone(mask * (tile.noise(16, 64, 2) - 0.5) * 0.18)
        tile.tone((tile.noise(4, 4, 3) - 0.5) * 0.12)
    elif skin.material == "paper":
        # The edges of pages in a stack: a thin line for each page, of a few
        # tones, some pages out further than others.
        tile.put(np.ones_like(tile.alpha), skin.base)
        pitch = 2.0
        rows = int(FILL[1] / pitch)
        for row in range(rows):
            y0 = row * pitch
            tone = rng.uniform(-0.10, 0.10)
            colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 2.0)
            tile.put(((tile.y >= y0) & (tile.y < y0 + pitch - 0.35)).astype(np.float32), colour)
            tile.put(((tile.y >= y0 + pitch - 0.35) & (tile.y < y0 + pitch)).astype(np.float32), skin.dark, 0.45)
        # A page that is creased: a short dark line across a few pages.
        creases = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(3.0, 7.0)) for _ in range(4)]
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, y), (x + 1.2, y + h)], 0.30) for x, y, h in creases]), skin.dark, 0.5)
        tile.tone((tile.noise(3, 6, 3) - 0.5) * 0.10)
    elif skin.material == "books":
        # Books that lie flat in stacks, their spines to the view: a row of
        # spines of each height, each spine of its own binding, with bands of
        # gold near its ends and a title in the middle.
        tile.put(np.ones_like(tile.alpha), skin.dark)
        bindings = (skin.base, (110, 36, 44), (48, 80, 62), (44, 54, 92), (130, 92, 52))
        y0 = 0.0
        titles, bands = [], []
        while y0 < FILL[1] - 0.5:
            h = min(rng.choice([4.0, 5.0, 6.0, 7.0]), FILL[1] - y0)
            if FILL[1] - (y0 + h) < 3.0:
                h = FILL[1] - y0
            x0 = rng.uniform(0.0, 20.0)
            end = x0 + 64.0
            while x0 < end - 1.0:
                length = min(rng.choice([18.0, 24.0, 30.0, 40.0]), end - x0)
                if end - (x0 + length) < 10.0:
                    length = end - x0
                tone = rng.uniform(-0.10, 0.08)
                colour = _mix(rng.choice(bindings), skin.dark, 0.42 + max(0.0, -tone))
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.5, y0 + 0.35, x0 + length - 0.5, y0 + h - 0.35)), colour)
                # A spine is round: a light line on its top, shade on its foot.
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.5, y0 + 0.35, x0 + length - 0.5, y0 + 1.0)), skin.light, 0.22)
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.5, y0 + h - 1.1, x0 + length - 0.5, y0 + h - 0.35)), skin.dark, 0.45)
                bands += [(x0 + 2.2, y0, h), (x0 + length - 3.0, y0, h)]
                if length > 22.0:
                    titles.append((x0 + length * 0.5, y0 + h * 0.5, min(8.0, length * 0.3)))
                x0 += length
            y0 += h
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x, y + 0.6, x + 0.7, y + h - 0.6) for x, y, h in bands]), skin.accent, 0.32)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - w * 0.5, y - 0.35, x + w * 0.5, y + 0.35) for x, y, w in titles]), skin.accent, 0.28)
        tile.tone((tile.noise(4, 8, 3) - 0.5) * 0.14)
    elif skin.material == "keys":
        # The black lacquer of a piano, with a keyboard set in it: keys of
        # ivory, gone dim in the dark, and the black keys over them. A line
        # of light on the lacquer, as on a polished case.
        tile.put(np.ones_like(tile.alpha), skin.base)
        ivory = _mix((236, 228, 206), skin.dark, 0.62)
        for row in range(2):
            y0 = row * 32.0
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, y0 + 2.0, 64.0, y0 + 18.0)), skin.dark)
            for k in range(8):
                x0 = k * 8.0 + (4.0 if row else 0.0)
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.35, y0 + 2.4, x0 + 7.65, y0 + 17.6)), _mix(ivory, skin.dark, rng.uniform(0.0, 0.12)))
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.35, y0 + 16.4, x0 + 7.65, y0 + 17.6)), skin.dark, 0.35)
            for k in range(8):
                if (k + (1 if row else 0)) % 7 in (2, 6):
                    continue
                x0 = k * 8.0 + 5.4 + (4.0 if row else 0.0)
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, y0 + 2.4, x0 + 5.2, y0 + 12.0)), skin.dark)
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.8, y0 + 2.4, x0 + 1.6, y0 + 11.0)), skin.light, 0.30)
            # The lacquer under the keys: a long soft shine.
            tile.put(np.clip(1.0 - np.abs(tile.y - (y0 + 25.0)) / 2.0, 0.0, 1.0) * (0.55 + 0.45 * np.sin(tile.x * math.pi / 32.0 + row)) ** 2, skin.light, 0.35)
        tile.tone((tile.noise(4, 4, 3) - 0.5) * 0.10)
    elif skin.material == "fired":
        # Bricks fired in a kiln: each of its own tone, its end scorched
        # dark where the fire was, a few glazed, and heat in a few joints.
        _courses(tile, skin, 8.0, 16.0, 0.6, 0.5)
        for row in range(8):
            for i in range(4):
                x0 = i * 16.0 + (8.0 if row % 2 else 0.0)
                y0 = row * 8.0
                kind = rng.random()
                if kind < 0.35:
                    burn = np.clip(1.0 - ((tile.x - x0) % 64.0) / 7.0, 0.0, 1.0) * (((tile.x - x0) % 64.0) < 16.0) * (tile.y >= y0) * (tile.y < y0 + 8.0)
                    tile.put(burn, skin.dark, 0.55)
                elif kind < 0.45:
                    glaze = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 1.0, y0 + 1.0, x0 + 15.0, y0 + 7.0))
                    tile.put(glaze, (52, 84, 92), 0.30)
                    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 2.0, y0 + 1.4, x0 + 9.0, y0 + 2.0)), (200, 226, 226), 0.18)
        seams = [(rng.randrange(8) * 8.0, rng.uniform(0, 64), rng.uniform(5.0, 12.0)) for _ in range(3)]
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x, y - 0.3, x + w, y + 0.3) for y, x, w in seams], blur=0.6), skin.accent, 0.45)
        tile.tone((tile.noise(3, 3, 4) - 0.55) * 0.28)
    elif skin.material == "timber":
        # Boards laid flat, eight to the tile, each board a few lengths. Each
        # board has its own tone, a grain along it and a nail at each end.
        tile.put(np.ones_like(tile.alpha), skin.dark)
        board = 8.0
        nails = []
        for row in range(int(FILL[1] / board)):
            y0 = row * board
            x0 = rng.uniform(0.0, 20.0)
            end = x0 + 64.0
            while x0 < end - 1.0:
                length = min(rng.choice([20.0, 26.0, 32.0, 40.0]), end - x0)
                if end - (x0 + length) < 10.0:
                    length = end - x0
                tone = rng.uniform(-0.22, 0.14)
                colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.4)
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.4, y0 + 0.5, x0 + length - 0.4, y0 + board - 0.5)), colour)
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.4, y0 + 0.5, x0 + length - 0.4, y0 + 1.3)), skin.light, 0.22)
                nails += [(x0 + 1.6, y0 + board * 0.5), (x0 + length - 1.6, y0 + board * 0.5)]
                x0 += length
        grain = np.sin(tile.y * 2.6 + (tile.noise(4, 16, 2) - 0.5) * 9.0)
        tile.tone(grain * 0.05 + (tile.noise(4, 8, 3) - 0.5) * 0.18)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.45) for x, y in nails]), skin.dark, 0.85)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.15, y - 0.15, 0.2) for x, y in nails]), skin.accent, 0.5)
    elif skin.material == "deckplate":
        # Square plates of steel, four to the tile, each with a row of rivets
        # along each edge. The paint is a little worn: low contrast, so the
        # repeat does not show.
        tile.put(np.ones_like(tile.alpha), skin.dark)
        rivets = []
        for px in range(2):
            for py in range(2):
                x0, y0 = px * 32.0, py * 32.0
                tone = rng.uniform(-0.08, 0.08)
                colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.6)
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.4, y0 + 0.4, x0 + 31.6, y0 + 31.6)), colour)
                tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 0.4, y0 + 0.4, x0 + 31.6, y0 + 1.0), _box(p, dx, dy, x0 + 0.4, y0 + 0.4, x0 + 1.0, y0 + 31.6))), skin.light, 0.30)
                tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 0.4, y0 + 31.0, x0 + 31.6, y0 + 31.6), _box(p, dx, dy, x0 + 31.0, y0 + 0.4, x0 + 31.6, y0 + 31.6))), skin.dark, 0.45)
                for k in range(8):
                    t = 2.0 + k * 4.0
                    rivets += [(x0 + t, y0 + 2.2), (x0 + t, y0 + 29.8)]
                    if 0 < k < 7:
                        rivets += [(x0 + 2.2, y0 + t), (x0 + 29.8, y0 + t)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x + 0.2, y + 0.2, 0.62) for x, y in rivets]), skin.dark, 0.55)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.1, y - 0.1, 0.5) for x, y in rivets]), skin.light, 0.40)
        # Worn paint: a few faint scuffs.
        scuffs = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(2.0, 5.0)) for _ in range(6)]
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, y), (x + w, y + w * 0.15)], 0.35) for x, y, w in scuffs]), skin.light, 0.18)
        tile.tone((tile.noise(4, 4, 4) - 0.5) * 0.14)
    elif skin.material == "rock":
        # Broken stone: each pixel is in the cell of its nearest point, and
        # the cracks are where the two nearest points are as near.
        points = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(-0.2, 0.2)) for _ in range(16)]
        d1 = np.full(tile.alpha.shape, 1e9, dtype=np.float32)
        d2 = np.full(tile.alpha.shape, 1e9, dtype=np.float32)
        tone = np.zeros_like(d1)
        lit = np.zeros_like(d1)
        for px, py, t in points:
            ddx = (tile.x - px + 32.0) % 64.0 - 32.0
            ddy = (tile.y - py + 32.0) % 64.0 - 32.0
            d = np.sqrt(ddx * ddx + (ddy * 1.25) ** 2)
            closer = d < d1
            d2 = np.where(closer, d1, np.minimum(d2, d))
            tone = np.where(closer, t, tone)
            lit = np.where(closer, -(ddx + ddy) * 0.012, lit)
            d1 = np.where(closer, d, d1)
        tile.put(np.ones_like(tile.alpha), skin.base)
        tile.tone(tone + lit)
        crack = np.clip(1.0 - (d2 - d1) / 1.3, 0.0, 1.0)
        tile.put(crack, skin.dark, 0.85)
        tile.put(np.clip(1.0 - np.abs((d2 - d1) - 1.9) / 0.7, 0, 1) * (lit > 0), skin.light, 0.25)
        tile.tone((tile.noise(5, 5, 3) - 0.5) * 0.20)
    elif skin.material == "void":
        # Black, with a few faint cracks in it and a few points of light it
        # ate. Low contrast: the white edge of the block is what shows it.
        tile.put(np.ones_like(tile.alpha), skin.base)
        cracks = []
        for _ in range(3):
            x, y = rng.uniform(0, 64), rng.uniform(0, 64)
            pts = [(x, y)]
            for _ in range(rng.randint(3, 5)):
                x, y = x + rng.uniform(-4.5, 4.5), y + rng.uniform(2.0, 5.5)
                pts.append((x, y))
            cracks.append(pts)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.32) for pts in cracks]), (26, 26, 28), 0.9)
        specks = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.25, 0.45)) for _ in range(3)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r) for x, y, r in specks]), skin.light, 0.55)
    elif skin.material == "mudbrick":
        # Bricks of mud dried in the sun, in a thick bed of mud: each brick of
        # its own tone, its edges soft, straw in it, and a few of them glazed
        # in lapis, as on the gates of Babylon.
        tile.put(np.ones_like(tile.alpha), _mix(skin.dark, skin.base, 0.35))
        glazed = {(rng.randrange(8), rng.randrange(4))}
        for row in range(8):
            for i in range(4):
                x0 = i * 16.0 + (8.0 if row % 2 else 0.0)
                y0 = row * 8.0
                tone = rng.uniform(-0.18, 0.12)
                colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.5)
                if (row, i) in glazed:
                    colour = _mix(skin.accent, skin.base, 0.45)
                soft = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.9, y0 + 0.9, x0 + 15.1, y0 + 7.1), blur=0.6)
                body = np.clip((soft - 0.5) * 5.0 + 0.5, 0.0, 1.0)
                tile.put(body, colour)
                tile.put(body * np.clip(1.0 - ((tile.y - y0) % 64.0) / 1.8, 0.0, 1.0), skin.light, 0.22)
        straw = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0, math.pi)) for _ in range(46)]
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, y), (x + 1.6 * math.cos(a), y + 1.6 * math.sin(a))], 0.22) for x, y, a in straw]), _mix(skin.light, (240, 214, 140), 0.5), 0.55)
        tile.tone((tile.noise(4, 4, 4) - 0.5) * 0.26)
    elif skin.material == "marble":
        # Slabs of marble in courses, the joints thin, with grey veins that
        # wander through each slab.
        _courses(tile, skin, 16.0, 32.0, 0.35, 0.6)
        n = tile.noise(3, 3, 4)
        veins = np.clip(1.0 - np.abs(n - 0.5) / 0.018, 0.0, 1.0)
        tile.put(veins, skin.dark, 0.20)
        n2 = tile.noise(5, 2, 3)
        tile.put(np.clip(1.0 - np.abs(n2 - 0.45) / 0.012, 0.0, 1.0), skin.dark, 0.12)
        tile.tone((tile.noise(3, 3, 3) - 0.5) * 0.10)
    elif skin.material == "adobe":
        # Mudbrick under a coat of plaster that is worn, with stones of
        # coral set in it here and there: pale, round, full of small holes.
        tile.put(np.ones_like(tile.alpha), skin.base)
        tile.tone((tile.noise(5, 5, 4) - 0.5) * 0.30)
        worn = np.clip((tile.noise(4, 4, 3) - 0.58) * 6.0, 0.0, 1.0)
        bricks = (((tile.y % 8.0) < 0.6) | (((tile.x + (tile.y // 8.0 % 2.0) * 8.0) % 16.0) < 0.6)).astype(np.float32)
        tile.put(worn, _mix(skin.base, skin.dark, 0.25), 0.6)
        tile.put(worn * bricks, skin.dark, 0.55)
        stones = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(1.8, 3.6)) for _ in range(8)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x + 0.3, y + 0.4, r, ry=r * 0.75) for x, y, r in stones], blur=0.3), skin.dark, 0.45)
        coral = tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r, ry=r * 0.72) for x, y, r in stones], blur=0.2)
        tile.put(coral, _mix(skin.light, skin.base, 0.45))
        pores = [(x + rng.uniform(-r, r) * 0.7, y + rng.uniform(-r, r) * 0.5) for x, y, r in stones for _ in range(7)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.3) for x, y in pores]) * coral, skin.dark, 0.45)
    elif skin.material == "wet_planks":
        # Planks of a quay, dark with the sea: each plank of its own tone, a
        # wet shine along its top, nails gone to rust, and green weed low
        # down where the tide comes.
        tile.put(np.ones_like(tile.alpha), skin.dark)
        nails = []
        for row in range(8):
            y0 = row * 8.0
            x0 = rng.uniform(0.0, 20.0)
            end = x0 + 64.0
            while x0 < end - 1.0:
                length = min(rng.choice([22.0, 28.0, 36.0]), end - x0)
                if end - (x0 + length) < 12.0:
                    length = end - x0
                tone = rng.uniform(-0.22, 0.10)
                colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.4)
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.35, y0 + 0.45, x0 + length - 0.35, y0 + 7.55)), colour)
                nails += [(x0 + 1.8, y0 + 4.0), (x0 + length - 1.8, y0 + 4.0)]
                x0 += length
        sheen = np.clip(1.0 - np.abs((tile.y % 8.0) - 1.4) / 0.8, 0.0, 1.0) * np.clip((tile.noise(6, 8, 2) - 0.45) * 4.0, 0.0, 1.0)
        tile.put(sheen, skin.light, 0.40)
        grain = np.sin(tile.y * 2.4 + (tile.noise(4, 16, 2) - 0.5) * 8.0)
        tile.tone(grain * 0.04 + (tile.noise(4, 8, 3) - 0.5) * 0.16)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.5) for x, y in nails]), (120, 64, 40), 0.85)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 0.3, y + 0.4, x + 0.3, y + 2.6) for x, y in nails]), (120, 64, 40), 0.30)
        tile.put(np.clip((tile.noise(6, 3, 3) - 0.55) * 5.0, 0.0, 1.0) * np.clip((tile.y % 8.0) / 8.0, 0.0, 1.0), (52, 90, 70), 0.22)
    elif skin.material == "cobbles":
        # Setts of granite in rows, each a block with round corners, of its
        # own grey, a light top and soot in the joints.
        tile.put(np.ones_like(tile.alpha), skin.dark)
        for row in range(8):
            y0 = row * 8.0
            x0 = rng.uniform(0.0, 6.0)
            end = x0 + 64.0
            while x0 < end - 1.0:
                w = min(rng.choice([8.0, 9.0, 10.0, 11.0]), end - x0)
                if end - (x0 + w) < 6.0:
                    w = end - x0
                tone = rng.uniform(-0.20, 0.16)
                colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.5)
                soft = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.7, y0 + 0.7, x0 + w - 0.7, y0 + 7.3), blur=0.8)
                body = np.clip((soft - 0.5) * 5.0 + 0.5, 0.0, 1.0)
                tile.put(body, colour)
                tile.put(body * np.clip(1.0 - ((tile.y - y0) % 64.0 - 0.7) / 2.0, 0.0, 1.0), skin.light, 0.30)
                tile.put(body * np.clip(((tile.y - y0) % 64.0 - 5.0) / 2.3, 0.0, 1.0), skin.dark, 0.35)
                x0 += w
        tile.tone((tile.noise(8, 8, 3) - 0.5) * 0.18)
    elif skin.material == "laterite":
        # Earth that the sun baked hard: wavy beds of each tone, a thin dark
        # seam between some beds, small pebbles, and nodules of iron rust.
        tile.put(np.ones_like(tile.alpha), skin.base)
        wave = tile.y + 1.4 * np.sin(tile.x * math.pi / 16.0 + 0.7) + (tile.noise(4, 2, 3) - 0.5) * 4.0
        bed = 64.0 / 7.0
        tile.tone(np.sin(wave * 2.0 * math.pi / bed) * 0.09 + (tile.noise(6, 6, 3) - 0.5) * 0.22)
        seam = np.clip(1.0 - np.abs((wave / bed) % 1.0 - 0.5) / 0.035, 0.0, 1.0) * (tile.noise(3, 3, 2) > 0.45)
        tile.put(seam, skin.dark, 0.45)
        pebbles = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.5, 1.3)) for _ in range(22)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y + 0.3, r, ry=r * 0.7) for x, y, r in pebbles]), skin.dark, 0.55)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r * 0.85, ry=r * 0.6) for x, y, r in pebbles]), _mix(skin.light, (220, 210, 190), 0.3), 0.8)
        nodules = [(rng.uniform(0, 64), rng.uniform(0, 64)) for _ in range(30)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.45) for x, y in nodules]), _mix(skin.dark, (120, 40, 20), 0.4), 0.7)
    elif skin.material == "ice":
        # Old ice of a glacier in blocks: each block a deeper blue low down,
        # light cracks between the blocks, long streaks of light, and bubbles
        # of air caught in it.
        points = [(rng.uniform(0, 64), rng.uniform(0, 64)) for _ in range(9)]
        d1 = np.full(tile.alpha.shape, 1e9, dtype=np.float32)
        d2 = np.full(tile.alpha.shape, 1e9, dtype=np.float32)
        depth = np.zeros_like(d1)
        for px, py in points:
            ddx = (tile.x - px + 32.0) % 64.0 - 32.0
            ddy = (tile.y - py + 32.0) % 64.0 - 32.0
            d = np.sqrt(ddx * ddx + ddy * ddy)
            closer = d < d1
            d2 = np.where(closer, d1, np.minimum(d2, d))
            depth = np.where(closer, ddy, depth)
            d1 = np.where(closer, d, d1)
        tile.put(np.ones_like(tile.alpha), skin.base)
        tile.tone(np.clip(depth / 14.0, -1.0, 1.0) * -0.16 + (tile.noise(4, 4, 3) - 0.5) * 0.16)
        tile.put(np.clip((tile.noise(8, 2, 2) - 0.6) * 4.0, 0.0, 1.0), skin.light, 0.16)
        tile.put(np.clip(1.0 - (d2 - d1) / 0.9, 0.0, 1.0), skin.light, 0.65)
        tile.put(np.clip(1.0 - np.abs((d2 - d1) - 1.7) / 0.8, 0.0, 1.0), skin.dark, 0.25)
        bubbles = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.25, 0.6)) for _ in range(26)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r) for x, y, r in bubbles]), skin.accent, 0.45)
    elif skin.material == "chalk":
        # Chalk: soft white rock in beds, with rows of flints in it. Each
        # flint is a dark lump with a white rind.
        tile.put(np.ones_like(tile.alpha), skin.base)
        tile.tone((tile.noise(5, 5, 4) - 0.5) * 0.16)
        beds = np.clip(1.0 - np.abs((tile.y + (tile.noise(3, 1, 2) - 0.5) * 3.0) % 16.0 - 0.6) / 0.35, 0.0, 1.0)
        tile.put(beds, skin.dark, 0.22)
        flints = []
        for y0 in (7.0, 39.0):
            x = rng.uniform(0.0, 6.0)
            while x < 58.0:
                flints.append((x, y0 + rng.uniform(-1.5, 1.5), rng.uniform(2.2, 3.8), rng.uniform(1.3, 2.2)))
                x += rng.uniform(10.0, 16.0)
        lumps = [(x + rx * 0.5, y + ry * 0.3, rx * 0.6, ry * 0.8) for x, y, rx, ry in flints]
        shapes = flints + lumps
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, rx + 0.5, ry=ry + 0.5) for x, y, rx, ry in shapes], blur=0.2), skin.light)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, rx, ry=ry) for x, y, rx, ry in shapes]), skin.accent)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - rx * 0.3, y - ry * 0.35, rx * 0.35, ry=ry * 0.25) for x, y, rx, ry in flints]), (120, 124, 136), 0.5)
        cracks = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(-2, 2)) for _ in range(5)]
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, y), (x + a, y + 3), (x + a - 1.0, y + 6)], 0.25) for x, y, a in cracks]), skin.dark, 0.35)
    elif skin.material == "indus_brick":
        # Fired bricks of the Indus cities, all of one shape (four long, two
        # wide, one high), in English bond: a course of stretchers, then a
        # course of headers. Each brick has its own tone, and a few are dark
        # from the kiln.
        tile.put(np.ones_like(tile.alpha), _mix(skin.dark, skin.accent, 0.25))
        for row in range(16):
            y0 = row * 4.0
            length = 16.0 if row % 2 == 0 else 8.0
            shift = 8.0 if row % 4 == 2 else (4.0 if row % 4 == 1 else 0.0)
            for i in range(int(64 / length)):
                x0 = i * length + shift
                tone = rng.uniform(-0.16, 0.12)
                colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.6)
                if rng.random() < 0.06:
                    colour = _mix(skin.base, skin.dark, 0.45)
                body = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.35, y0 + 0.35, x0 + length - 0.35, y0 + 3.65))
                tile.put(body, colour)
                tile.put(body * (((tile.y - y0) % 64.0) < 1.0), skin.light, 0.22)
        tile.tone((tile.noise(4, 4, 3) - 0.5) * 0.18)
    elif skin.material == "loess":
        # Loess: fine yellow silt that the wind laid down. It cracks in long
        # upright joints. Old soils show as faint red-brown bands, and small
        # snail shells are in it.
        tile.put(np.ones_like(tile.alpha), skin.base)
        tile.tone((tile.noise(8, 8, 3) - 0.5) * 0.14)
        soil = np.clip(1.0 - np.abs((tile.y + (tile.noise(4, 1, 2) - 0.5) * 4.0) % 32.0 - 20.0) / 3.0, 0.0, 1.0)
        tile.put(soil, _mix(skin.dark, (150, 70, 40), 0.35), 0.28)
        joints = []
        for _ in range(7):
            x = rng.uniform(0, 64)
            wobble = [rng.uniform(-0.7, 0.7) for _ in range(10)]
            joints.append([(x + wobble[k % 10], k * 6.4) for k in range(11)])
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.35) for pts in joints]), skin.dark, 0.55)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x + 0.5, y) for x, y in pts], 0.3) for pts in joints]), skin.light, 0.30)
        shells = [(rng.uniform(0, 64), rng.uniform(0, 64)) for _ in range(10)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.7) for x, y in shells]), skin.light, 0.7)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x + 0.15, y + 0.1, 0.28) for x, y in shells]), skin.dark, 0.6)
    elif skin.material == "drystone":
        # A wall of stones laid dry, with no mortar, as the terraces of the
        # highlands: each stone of its own shape and tone, fitted close,
        # round at its edges, dark in the gaps, and lichen on a few.
        points = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(-0.22, 0.18)) for _ in range(14)]
        d1 = np.full(tile.alpha.shape, 1e9, dtype=np.float32)
        d2 = np.full(tile.alpha.shape, 1e9, dtype=np.float32)
        tone = np.zeros_like(d1)
        lit = np.zeros_like(d1)
        for px, py, t in points:
            ddx = (tile.x - px + 32.0) % 64.0 - 32.0
            ddy = (tile.y - py + 32.0) % 64.0 - 32.0
            d = np.sqrt(ddx * ddx + (ddy * 1.5) ** 2)
            closer = d < d1
            d2 = np.where(closer, d1, np.minimum(d2, d))
            tone = np.where(closer, t, tone)
            lit = np.where(closer, -(ddx * 0.5 + ddy) * 0.016, lit)
            d1 = np.where(closer, d, d1)
        tile.put(np.ones_like(tile.alpha), skin.base)
        tile.tone(tone + np.clip(lit, -0.25, 0.25) + (tile.noise(8, 8, 3) - 0.5) * 0.16)
        tile.put(np.clip(1.0 - (d2 - d1 - 0.4) / 1.2, 0.0, 1.0), skin.dark, 0.95)
        tile.put(np.clip(1.0 - np.abs((d2 - d1) - 2.2) / 0.8, 0.0, 1.0) * (lit > 0), skin.light, 0.30)
        lichen = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.4, 1.0)) for _ in range(14)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r) for x, y, r in lichen]) * ((d2 - d1) > 1.5), skin.accent, 0.45)
    elif skin.material == "wet_clay":
        # Wet clay of a swamp: dark and smooth, with a shine where it is
        # wettest, fibres of roots in it, and a few small stones.
        tile.put(np.ones_like(tile.alpha), skin.base)
        tile.tone((tile.noise(4, 4, 4) - 0.5) * 0.30)
        wet = np.clip((tile.noise(6, 3, 3) - 0.60) * 6.0, 0.0, 1.0)
        tile.put(wet, _mix(skin.base, skin.dark, 0.45), 0.5)
        sheen = wet * np.clip(1.0 - np.abs(tile.noise(12, 4, 2) - 0.5) / 0.06, 0.0, 1.0)
        tile.put(sheen, skin.light, 0.35)
        fibres = []
        for _ in range(12):
            x, y = rng.uniform(0, 64), rng.uniform(0, 64)
            pts = [(x, y)]
            for _ in range(4):
                x, y = x + rng.uniform(1.0, 3.0), y + rng.uniform(-1.4, 1.4)
                pts.append((x, y))
            fibres.append(pts)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.28) for pts in fibres]), _mix(skin.light, (170, 140, 90), 0.4), 0.45)
        stones = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.6, 1.4)) for _ in range(10)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r, ry=r * 0.7) for x, y, r in stones]), _mix(skin.light, (120, 120, 116), 0.4), 0.7)
    elif skin.material == "clay_layers":
        # The floors of coloured clay that the builders of the Gulf coast
        # laid one on another: bands of brown, red, yellow and olive clay,
        # each band a little wavy, a dark line between them, and grit in
        # them.
        tile.put(np.ones_like(tile.alpha), skin.base)
        red, yellow, olive = _mix(skin.base, (164, 66, 44), 0.32), _mix(skin.base, (200, 164, 84), 0.32), _mix(skin.base, (90, 106, 88), 0.36)
        bands = ((9.0, skin.base), (6.0, red), (8.0, yellow), (5.0, olive), (10.0, skin.base), (7.0, red), (6.0, olive), (13.0, yellow))
        # Each line between two bands waves a little; the line at the top of
        # the tile is straight, so the tile repeats down.
        lines = [0.0]
        for height, _ in bands:
            lines.append(lines[-1] + height)
        waves = [np.zeros_like(tile.x) if j in (0, len(bands)) else 0.8 * np.sin(tile.x * 2.0 * math.pi / 64.0 * (1 + j % 3) + j) for j in range(len(lines))]
        for k, (_, colour) in enumerate(bands):
            top, low = lines[k] + waves[k], lines[k + 1] + waves[k + 1]
            band = ((tile.y >= top) & (tile.y < low)).astype(np.float32)
            tile.put(band, colour)
            tile.put(band * np.clip(1.0 - (tile.y - top) / 1.2, 0.0, 1.0), skin.light, 0.20)
            tile.put(np.clip(1.0 - np.abs(tile.y - top) / 0.35, 0.0, 1.0), skin.dark, 0.55)
        tile.tone((tile.noise(8, 4, 3) - 0.5) * 0.18)
        grit = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.3, 0.8)) for _ in range(40)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r, ry=r * 0.7) for x, y, r in grit]), skin.dark, 0.45)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.15, y - 0.15, r * 0.5) for x, y, r in grit[::3]]), skin.light, 0.5)
    elif skin.material == "beachrock":
        # Beach rock: sand, shells and bits of coral that the sea set hard.
        # Pale, with small pits, round holes the sea wore, the white curves
        # of shells, and a few heads of brain coral.
        tile.put(np.ones_like(tile.alpha), skin.base)
        tile.tone((tile.noise(6, 6, 4) - 0.5) * 0.20)
        beds = np.clip(1.0 - np.abs((tile.y + (tile.noise(3, 1, 2) - 0.5) * 4.0) % 21.33 - 0.6) / 0.5, 0.0, 1.0)
        tile.put(beds, skin.dark, 0.18)
        holes = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(1.0, 2.6)) for _ in range(9)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r, ry=r * 0.75) for x, y, r in holes]), skin.dark, 0.55)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x + r * 0.25, y + r * 0.2, r * 0.7, ry=r * 0.5) for x, y, r in holes]), _mix(skin.dark, (0, 0, 0), 0.3), 0.45)
        pits = [(rng.uniform(0, 64), rng.uniform(0, 64)) for _ in range(70)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.35) for x, y in pits]), skin.dark, 0.5)
        shells = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.8, 1.8), rng.uniform(0, 360)) for _ in range(14)]
        tile.put(tile.mask(lambda p, dx, dy: [p.arc([(x - r) * K + dx, (y - r) * K + dy, (x + r) * K + dx, (y + r) * K + dy], a, a + 160, fill=255, width=max(1, int(0.4 * K))) for x, y, r, a in shells]), skin.light, 0.85)
        corals = [(rng.uniform(4, 60), rng.uniform(4, 60), rng.uniform(2.0, 3.2)) for _ in range(3)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r) for x, y, r in corals]), _mix(skin.base, skin.light, 0.5), 0.8)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x - r * 0.7, y + r * 0.2 * math.sin(k)), (x - r * 0.2, y - r * 0.3), (x + r * 0.3, y + r * 0.2), (x + r * 0.7, y - r * 0.1)], 0.25) for k, (x, y, r) in enumerate(corals)]), skin.dark, 0.45)
    elif skin.material == "midden":
        # The earth of a shore where people lived a long time: dark
        # volcanic soil, with sherds of red pots stamped with rows of fine
        # teeth, white shells, bits of coral and flecks of charcoal.
        tile.put(np.ones_like(tile.alpha), skin.base)
        tile.tone((tile.noise(6, 6, 4) - 0.5) * 0.30)
        sherds = []
        for _ in range(7):
            x, y, r, a = rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(2.0, 3.4), rng.uniform(0, math.pi)
            corners = [(x + math.cos(a + k * 2.0 + rng.uniform(-0.3, 0.3)) * r, y + math.sin(a + k * 2.0 + rng.uniform(-0.3, 0.3)) * r * 0.7) for k in range(3)] + [(x + math.cos(a + 5.4) * r * 0.8, y + math.sin(a + 5.4) * r * 0.6)]
            sherds.append((x, y, r, corners))
        tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(cx, cy + 0.4) for cx, cy in pts]) for _, _, _, pts in sherds]), skin.dark, 0.6)
        tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, pts) for _, _, _, pts in sherds]), _mix(skin.accent, skin.base, 0.35))
        teeth = [(x + j * 0.55 - r * 0.5, y + row * 0.9 - 0.4) for x, y, r, _ in sherds for row in (0, 1) for j in range(int(r * 1.6))]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.16) for x, y in teeth]) * tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, pts) for _, _, _, pts in sherds]), _mix(skin.light, (250, 240, 220), 0.5), 0.75)
        shells = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.6, 1.3)) for _ in range(16)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r, ry=r * 0.6) for x, y, r in shells]), _mix(skin.light, (240, 236, 224), 0.6), 0.85)
        flecks = [(rng.uniform(0, 64), rng.uniform(0, 64)) for _ in range(40)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.4) for x, y in flecks]), skin.dark, 0.7)
    elif skin.material == "sewn_hull":
        # The planks of a hull, each sewn to the next with cord of coconut
        # fibre through pairs of holes, the seams filled with gum; the wood
        # is wet and has its grain along it.
        rows = 6
        h = 64.0 / rows
        tile.put(np.ones_like(tile.alpha), skin.dark)
        for row in range(rows):
            y0 = row * h
            tone = rng.uniform(-0.14, 0.12)
            colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.6)
            plank = ((tile.y >= y0 + 0.5) & (tile.y < y0 + h - 0.3)).astype(np.float32)
            tile.put(plank, colour)
            tile.put(plank * np.clip(1.0 - (tile.y - y0 - 0.5) / 1.6, 0.0, 1.0), skin.light, 0.25)
            tile.put(plank * np.clip((tile.y - (y0 + h - 2.4)) / 2.1, 0.0, 1.0), skin.dark, 0.35)
        grain = np.clip(1.0 - np.abs(((tile.y + (tile.noise(4, 8, 2) - 0.5) * 3.0) % 1.4) - 0.7) / 0.12, 0.0, 1.0)
        tile.put(grain, skin.dark, 0.18)
        # The gum in the seams, and the stitches over them in pairs of holes.
        for row in range(rows):
            seam = row * h
            tile.put(np.clip(1.0 - np.abs(tile.y - seam) / 0.45, 0.0, 1.0), skin.accent, 0.35)
            for k in range(8):
                x = k * 8.0 + (4.0 if row % 2 else 0.0)
                tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x + side, seam + off, 0.45) for side in (-1.0, 1.0) for off in (-1.6, 1.6)]), skin.dark, 0.9)
                tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x - 1.0, seam - 1.6), (x + 1.0, seam + 1.6)], 0.4), _line(p, dx, dy, [(x + 1.0, seam - 1.6), (x - 1.0, seam + 1.6)], 0.4)]), _mix(skin.accent, (240, 220, 170), 0.3), 0.85)
        sheen = np.clip((tile.noise(6, 3, 2) - 0.55) * 4.0, 0.0, 1.0)
        tile.put(sheen, (220, 236, 240), 0.10)
    elif skin.material == "tuff":
        # Lapilli tuff, the soft rock of the crater that the moai were cut
        # from: grey-brown, full of small dark and pale grains, with the
        # marks of the stone adzes in rows, and spots of orange lichen.
        tile.put(np.ones_like(tile.alpha), skin.base)
        tile.tone((tile.noise(5, 5, 4) - 0.5) * 0.24)
        grains = []
        for _ in range(110):
            x, y, r = rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.5, 1.9)
            turn = rng.uniform(0.0, 6.28)
            grains.append([(x + math.cos(a + turn) * r * rng.uniform(0.6, 1.0), y + math.sin(a + turn) * r * rng.uniform(0.6, 1.0)) for a in (0.3, 1.9, 3.3, 4.6)])
        tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, pts) for pts in grains[:80]]), _mix(skin.dark, (40, 36, 34), 0.3), 0.70)
        tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, pts) for pts in grains[80:]]), skin.light, 0.65)
        marks = []
        for _ in range(4):
            x, y = rng.uniform(0, 64), rng.uniform(0, 64)
            marks.extend([(x + k * 1.3, y, x + k * 1.3 + 0.9, y + 3.2) for k in range(5)])
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x0, y0), (x1, y1)], 0.3) for x0, y0, x1, y1 in marks]), skin.dark, 0.35)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x0 + 0.4, y0), (x1 + 0.4, y1)], 0.25) for x0, y0, x1, y1 in marks]), skin.light, 0.30)
        lichen = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.5, 1.4)) for _ in range(10)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r, ry=r * 0.8) for x, y, r in lichen]), skin.accent, 0.55)
    elif skin.material == "whitewash":
        # A wall of rough stones in lime mortar, under a coat of lime plaster
        # washed white. The salt air has taken the plaster off in patches:
        # there the grey stones and the mortar show, and the edge of the
        # plaster round each patch is a little raised and lit. Rain has left
        # grey streaks down the wall, and fine cracks run through the coat.
        points = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(-0.20, 0.16)) for _ in range(16)]
        d1 = np.full(tile.alpha.shape, 1e9, dtype=np.float32)
        d2 = np.full(tile.alpha.shape, 1e9, dtype=np.float32)
        tone = np.zeros_like(d1)
        for px, py, t in points:
            ddx = (tile.x - px + 32.0) % 64.0 - 32.0
            ddy = (tile.y - py + 32.0) % 64.0 - 32.0
            d = np.sqrt(ddx * ddx + (ddy * 1.4) ** 2)
            closer = d < d1
            d2 = np.where(closer, d1, np.minimum(d2, d))
            tone = np.where(closer, t, tone)
            d1 = np.where(closer, d, d1)
        stone = _mix(skin.base, skin.dark, 0.38)
        worn = np.clip((tile.noise(3, 3, 3) - 0.56) * 7.0, 0.0, 1.0)
        # The stones and the mortar under the plaster.
        tile.put(np.ones_like(tile.alpha), stone)
        tile.tone(tone + (tile.noise(8, 8, 2) - 0.5) * 0.12)
        tile.put(np.clip(1.0 - (d2 - d1 - 0.3) / 1.0, 0.0, 1.0), _mix(skin.base, skin.dark, 0.15), 0.85)
        # The plaster over them, where it is still on.
        coat = 1.0 - worn
        tile.put(coat, skin.base)
        tile.tone((tile.noise(5, 5, 3) - 0.5) * 0.10 * coat)
        rim = np.clip(1.0 - np.abs(worn - 0.08) / 0.10, 0.0, 1.0)
        tile.put(rim * (tile.noise(16, 16, 1) > 0.3), skin.light, 0.55)
        tile.put(np.clip(worn * 4.0, 0.0, 1.0) * np.clip(1.0 - worn * 1.4, 0.0, 1.0), skin.dark, 0.30)
        # The grey streaks of the rain, down the wall.
        streaks = np.clip((tile.noise(14, 1, 2) - 0.58) * 4.0, 0.0, 1.0) * np.clip(tile.noise(2, 3, 2) * 1.6 - 0.4, 0.0, 1.0)
        tile.put(streaks * coat, skin.dark, 0.18)
        cracks = []
        for _ in range(4):
            x, yy = rng.uniform(0, 64), rng.uniform(0, 64)
            pts = [(x, yy)]
            for _ in range(4):
                x, yy = x + rng.uniform(-1.8, 1.8), yy + rng.uniform(1.0, 2.6)
                pts.append((x, yy))
            cracks.append(pts)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.18) for pts in cracks]) * coat, skin.dark, 0.40)
    elif skin.material == "caral_stone":
        # A wall of a platform of Caral: angular stones from the hills, some
        # big and some small, laid in courses in a mortar of clay. Small
        # stones fill the wide joints. A coat of clay plaster still covers
        # the wall in patches, and on a few of them the old red paint shows.
        mortar = _mix(skin.base, skin.dark, 0.60)
        tile.put(np.ones_like(tile.alpha), mortar)
        tile.tone((tile.noise(6, 6, 2) - 0.5) * 0.12)
        y0 = 0.0
        for row_h in (12.0, 7.0, 13.0, 8.0, 12.0, 12.0):
            x = rng.uniform(0.0, 8.0)
            end = x + 64.0
            while x < end - 3.0:
                w = min(rng.uniform(5.0, 15.0) * (row_h / 10.0), end - x)
                gap = rng.uniform(0.7, 1.3)
                tone = rng.uniform(-0.24, 0.20)
                colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.6)
                # An angular stone: each corner is broken off by its own
                # amount, and its sides are not quite straight.
                ya, yb = y0 + gap * 0.5 + rng.uniform(0.0, 1.2), y0 + row_h - gap * 0.5 - rng.uniform(0.0, 1.2)
                xa, xb = x + gap * 0.5, x + w - gap * 0.5
                k = [rng.uniform(0.2, 2.6) for _ in range(4)]
                pts = [(xa + k[0], ya), (xb - k[1], ya + rng.uniform(-0.4, 0.6)), (xb, ya + k[1] * 0.7), (xb + rng.uniform(-0.6, 0.4), yb - k[2]), (xb - k[2] * 0.8, yb),
                       (xa + k[3], yb + rng.uniform(-0.6, 0.2)), (xa, yb - k[3] * 0.7), (xa + rng.uniform(-0.4, 0.6), ya + k[0] * 0.8)]
                tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, pts)), colour)
                tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [pts[0], pts[1], (pts[1][0] - 0.6, pts[1][1] + 1.0), (pts[0][0] + 0.6, pts[0][1] + 1.0)])), skin.light, 0.40)
                tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [pts[5], pts[4], (pts[4][0] - 0.4, pts[4][1] - 1.0), (pts[5][0] + 0.4, pts[5][1] - 1.0)])), skin.dark, 0.40)
                x += w
            # The small stones that fill the joint under the course.
            chinks = [(rng.uniform(0, 64), y0 + row_h + rng.uniform(-0.3, 0.3), rng.uniform(0.5, 1.0)) for _ in range(5)]
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, cx, cy, r, ry=r * 0.7) for cx, cy, r in chinks]), _mix(skin.base, skin.dark, 0.15))
            y0 += row_h
        tile.tone((tile.noise(10, 10, 2) - 0.5) * 0.14)
        # The plaster that is left: smooth, pale, with a raised edge.
        coat = np.clip((tile.noise(3, 3, 3) - 0.62) * 10.0, 0.0, 1.0)
        tile.put(coat, _mix(skin.light, (236, 226, 204), 0.3), 0.95)
        tile.tone((tile.noise(12, 12, 2) - 0.5) * 0.08 * coat)
        tile.put(np.clip(1.0 - np.abs(coat - 0.10) / 0.10, 0.0, 1.0), skin.dark, 0.40)
        paint = coat * np.clip((tile.noise(2, 2, 2) - 0.55) * 6.0, 0.0, 1.0)
        tile.put(paint, skin.accent, 0.45)
    elif skin.material == "karst":
        # Limestone of the karst. The rain dissolves it, so its face has
        # rows of upright flutes (each a groove with a lit edge and a dark
        # edge), round pits, and dark streaks where the water runs down.
        # Thin beds cross it. The flutes are in patches, not on all of it.
        tile.put(np.ones_like(tile.alpha), skin.base)
        tile.tone((tile.noise(4, 4, 4) - 0.5) * 0.18)
        beds = np.clip(1.0 - np.abs((tile.y + (tile.noise(4, 1, 2) - 0.5) * 4.0) % 21.333 - 0.8) / 0.45, 0.0, 1.0)
        tile.put(beds, skin.dark, 0.20)
        phase = tile.x * 2.0 * math.pi / 5.333 + (tile.noise(3, 2, 2) - 0.5) * 5.0
        patch = np.clip((tile.noise(3, 3, 2) - 0.42) * 5.0, 0.0, 1.0)
        tile.put(patch * np.clip(-np.cos(phase) - 0.55, 0.0, 1.0) * 2.2, skin.dark, 0.38)
        tile.put(patch * np.clip(np.sin(phase) - 0.65, 0.0, 1.0) * 2.8, skin.light, 0.55)
        streaks = np.clip((tile.noise(14, 2, 2) - 0.60) * 5.0, 0.0, 1.0) * np.clip(tile.noise(2, 4, 2) * 1.6 - 0.4, 0.0, 1.0)
        tile.put(streaks, _mix(skin.dark, skin.base, 0.35), 0.45)
        pits = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.4, 1.0)) for _ in range(10)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y + r * 0.35, r * 0.9, ry=r * 1.3) for x, y, r in pits]), skin.light, 0.6)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r * 0.75, ry=r * 1.2) for x, y, r in pits]), skin.dark, 0.55)
        cracks = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(-1.5, 1.5)) for _ in range(4)]
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, y), (x + a, y + 4.0), (x + a * 0.5, y + 8.0)], 0.25) for x, y, a in cracks]), skin.dark, 0.5)
    elif skin.material == "volcanic_earth":
        # Dark earth of a volcanic island: it is rich and black-brown, in
        # soft clods. Bits of red scoria and grey pumice are in it, and fine
        # pale roots run through it.
        tile.put(np.ones_like(tile.alpha), skin.base)
        tile.tone((tile.noise(5, 5, 4) - 0.5) * 0.34)
        clods = np.clip((tile.noise(9, 9, 2) - 0.55) * 4.0, 0.0, 1.0)
        tile.put(clods, skin.light, 0.22)
        tile.put(np.clip((0.40 - tile.noise(9, 9, 2)) * 4.0, 0.0, 1.0), skin.dark, 0.40)
        for colour, count, size in ((_mix(skin.accent, (120, 50, 36), 0.55), 14, (0.6, 1.5)), ((150, 146, 138), 12, (0.5, 1.3))):
            bits = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(*size)) for _ in range(count)]
            pts = [[(x + r * math.cos(a) * rng.uniform(0.7, 1.1), y + r * 0.8 * math.sin(a) * rng.uniform(0.7, 1.1)) for a in np.linspace(0.0, 2.0 * math.pi, 7)[:-1]] for x, y, r in bits]
            tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, q) for q in pts]), colour, 0.9)
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - r * 0.3, y - r * 0.3, r * 0.35) for x, y, r in bits]), (255, 240, 220), 0.25)
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x + r * 0.2, y + r * 0.1, r * 0.25) for x, y, r in bits]), skin.dark, 0.5)
        roots = []
        for _ in range(8):
            x, y = rng.uniform(0, 64), rng.uniform(0, 64)
            pts = [(x, y)]
            for _ in range(5):
                x, y = x + rng.uniform(-1.6, 1.6), y + rng.uniform(1.0, 2.6)
                pts.append((x, y))
            roots.append(pts)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.22) for pts in roots]), _mix(skin.light, (200, 170, 120), 0.3), 0.5)
    elif skin.material == "river_clay":
        # Clay that the floods of the river laid down, one thin layer each
        # year: fine grey-brown bands, some paler with silt. Old root holes
        # go down through it, and rust stains the clay round each one, as
        # in the soil of a rice paddy.
        tile.put(np.ones_like(tile.alpha), skin.base)
        wave = (tile.noise(4, 1, 2) - 0.5) * 3.0
        fine = np.sin((tile.y + wave) * 2.0 * math.pi / 2.0)
        coarse = np.sin((tile.y + wave * 1.4) * 2.0 * math.pi / 8.0 + 0.6)
        tile.put(np.clip(coarse - 0.35, 0.0, 1.0) * 1.4, skin.light, 0.35)
        tile.put(np.clip(-coarse - 0.55, 0.0, 1.0) * 2.0, skin.dark, 0.30)
        tile.put(np.clip(fine - 0.7, 0.0, 1.0) * 3.0, skin.light, 0.18)
        tile.tone((tile.noise(6, 6, 3) - 0.5) * 0.16)
        holes = []
        for _ in range(7):
            x, y = rng.uniform(0, 64), rng.uniform(0, 64)
            pts = [(x, y)]
            for _ in range(5):
                x, y = x + rng.uniform(-1.0, 1.0), y + rng.uniform(1.4, 2.8)
                pts.append((x, y))
            holes.append(pts)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 2.6) for pts in holes], blur=1.2), skin.accent, 0.70)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.35) for pts in holes]), skin.dark, 0.65)
        grit = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.25, 0.55)) for _ in range(30)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r, ry=r * 0.7) for x, y, r in grit]), skin.dark, 0.45)
        shells = [(rng.uniform(0, 64), rng.uniform(0, 64)) for _ in range(3)]
        tile.put(tile.mask(lambda p, dx, dy: [p.pieslice([(x - 0.9) * K + dx, (y - 0.9) * K + dy, (x + 0.9) * K + dx, (y + 0.9) * K + dy], 180, 360, fill=255) for x, y in shells]), (226, 218, 198), 0.7)
    elif skin.material == "wharf":
        # A wharf over the mud of a river: planks of dark wet timber laid
        # on their edges in rows, each plank of its own tone, held by pegs
        # of wood. The mud shows in the gaps between them and is smeared on
        # their lower parts. A round pile stands in front each thirty-two
        # units, bound to the planks with rattan.
        tile.put(np.ones_like(tile.alpha), _mix(skin.dark, (70, 58, 44), 0.4))
        pegs = []
        for row in range(8):
            y0 = row * 8.0
            x0 = rng.uniform(0.0, 20.0)
            end = x0 + 64.0
            while x0 < end - 1.0:
                length = min(rng.choice([18.0, 24.0, 30.0]), end - x0)
                if end - (x0 + length) < 10.0:
                    length = end - x0
                tone = rng.uniform(-0.24, 0.10)
                colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.4)
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.5, y0 + 0.7, x0 + length - 0.5, y0 + 7.3)), colour)
                pegs += [(x0 + 2.2, y0 + 4.0), (x0 + length - 2.2, y0 + 4.0)]
                x0 += length
        grain = np.sin(tile.y * 2.6 + (tile.noise(4, 16, 2) - 0.5) * 9.0)
        tile.tone(grain * 0.05 + (tile.noise(4, 8, 3) - 0.5) * 0.16)
        sheen = np.clip(1.0 - np.abs((tile.y % 8.0) - 1.5) / 0.7, 0.0, 1.0) * np.clip((tile.noise(6, 8, 2) - 0.40) * 4.0, 0.0, 1.0)
        tile.put(sheen, skin.light, 0.45)
        tile.put(np.clip(((tile.y % 8.0) - 5.6) / 1.7, 0.0, 1.0) * (tile.y % 8.0 < 7.3), skin.dark, 0.35)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.55) for x, y in pegs]), skin.light, 0.75)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x + 0.15, y + 0.15, 0.30) for x, y in pegs]), skin.dark, 0.6)
        mud = np.clip((tile.noise(5, 6, 3) - 0.50) * 4.0, 0.0, 1.0) * np.clip(((tile.y % 8.0) - 3.0) / 4.0, 0.0, 1.0)
        tile.put(mud, (96, 82, 64), 0.40)
        for x in (10.0, 42.0):
            pile = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x - 2.6, 0.0, x + 2.6, 64.0))
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x + 2.6, 0.0, x + 4.2, 64.0), blur=0.6), (0, 0, 0), 0.40)
            tile.put(pile, _mix(skin.base, skin.dark, 0.25))
            tile.put(pile * np.clip(1.0 - np.abs(tile.x - (x - 1.2)) / 0.9, 0.0, 1.0), skin.light, 0.45)
            tile.put(pile * np.clip((tile.x - x - 0.8) / 1.8, 0.0, 1.0), skin.dark, 0.55)
            tile.put(pile * np.clip((tile.noise(2, 12, 2) - 0.5) * 3.0, 0.0, 1.0), (96, 82, 64), 0.35)
            for y in (6.0, 38.0):
                band = tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x - 2.9, y + k * 1.0), (x + 2.9, y + k * 1.0 + 0.7)], 0.5) for k in range(3)])
                tile.put(band, (150, 112, 66))
                tile.put(band * (tile.x > x + 1.0), skin.dark, 0.45)
    elif skin.material == "andesite":
        # Andesite, the grey stone of the volcanoes of Java, cut in blocks
        # and laid in courses, each block half along from the one under it,
        # with no mortar. Each block has its own grey, small round holes of
        # gas in it, and patches of pale lichen. Moss grows in a few joints.
        tile.put(np.ones_like(tile.alpha), skin.dark)
        for row in range(8):
            y0 = row * 8.0
            x0 = rng.uniform(0.0, 8.0)
            end = x0 + 64.0
            while x0 < end - 1.0:
                w = min(rng.choice([10.0, 12.0, 14.0, 16.0]), end - x0)
                if end - (x0 + w) < 8.0:
                    w = end - x0
                tone = rng.uniform(-0.16, 0.14)
                colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.5)
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.35, y0 + 0.35, x0 + w - 0.35, y0 + 7.65)), colour)
                tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 0.35, y0 + 0.35, x0 + w - 0.35, y0 + 1.1), _box(p, dx, dy, x0 + 0.35, y0 + 0.35, x0 + 1.0, y0 + 7.65))), skin.light, 0.35)
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.35, y0 + 6.9, x0 + w - 0.35, y0 + 7.65)), skin.dark, 0.40)
                x0 += w
        tile.tone((tile.noise(8, 8, 3) - 0.5) * 0.16)
        holes = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.25, 0.55)) for _ in range(40)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y + r * 0.4, r * 1.1) for x, y, r in holes]), skin.light, 0.45)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r) for x, y, r in holes]), skin.dark, 0.75)
        lichen = np.clip((tile.noise(12, 12, 2) - 0.72) * 6.0, 0.0, 1.0)
        tile.put(lichen, _mix(skin.light, (210, 216, 180), 0.5), 0.30)
        spots = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.4, 0.9)) for _ in range(6)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r, ry=r * 0.8) for x, y, r in spots]), (200, 150, 80), 0.55)
        joints = np.clip(1.0 - np.abs((tile.y % 8.0) - 8.0 * (tile.y % 8.0 > 4.0)) / 0.6, 0.0, 1.0)
        tile.put(joints * np.clip((tile.noise(6, 8, 2) - 0.60) * 5.0, 0.0, 1.0), skin.accent, 0.80)
    elif skin.material == "laterite_blocks":
        # Laterite, the red stone of Angkor: soft when it is dug, it goes
        # hard in the air, and it is full of holes and pits. The blocks are
        # large, set tight in courses with no mortar, each of its own red.
        # The holes are dark inside, with a lit lower lip.
        tile.put(np.ones_like(tile.alpha), skin.dark)
        rows = 6
        row_h = 64.0 / rows
        for row in range(rows):
            y0 = row * row_h
            x0 = rng.uniform(0.0, 12.0)
            end = x0 + 64.0
            while x0 < end - 1.0:
                w = min(rng.choice([14.0, 18.0, 21.0, 24.0]), end - x0)
                if end - (x0 + w) < 10.0:
                    w = end - x0
                tone = rng.uniform(-0.18, 0.12)
                colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.5)
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.3, y0 + 0.3, x0 + w - 0.3, y0 + row_h - 0.3)), colour)
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.3, y0 + 0.3, x0 + w - 0.3, y0 + 1.0)), skin.light, 0.30)
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.3, y0 + row_h - 1.0, x0 + w - 0.3, y0 + row_h - 0.3)), skin.dark, 0.35)
                x0 += w
        tile.tone((tile.noise(6, 6, 3) - 0.5) * 0.22)
        pits = tile.noise(32, 32, 2)
        hole = np.clip((pits - 0.68) * 8.0, 0.0, 1.0)
        lip = np.clip((np.roll(pits, -int(0.5 * K), axis=0) - 0.68) * 8.0, 0.0, 1.0) * (1.0 - hole)
        tile.put(lip, skin.light, 0.45)
        tile.put(hole, _mix(skin.dark, (30, 14, 10), 0.4), 0.85)
        small = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.3, 0.7)) for _ in range(36)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r, ry=r * 0.8) for x, y, r in small]), skin.dark, 0.7)
        tile.put(np.clip((tile.noise(3, 10, 2) - 0.6) * 4.0, 0.0, 1.0) * np.clip(tile.noise(2, 2, 2) * 1.4 - 0.3, 0.0, 1.0), (60, 50, 44), 0.25)
    elif skin.material == "forest_earth":
        # The earth of a forest floor: dark humus in soft clods, roots that
        # wind through it, small stones of grey and brown, and bits of old
        # leaves. It is not laid in courses: it is the ground itself.
        tile.put(np.ones_like(tile.alpha), skin.base)
        tile.tone((tile.noise(6, 6, 3) - 0.5) * 0.30)
        tile.put(np.clip((tile.noise(10, 10, 2) - 0.55) * 4.0, 0.0, 1.0), skin.dark, 0.45)
        tile.put(np.clip((tile.noise(14, 14, 2) - 0.62) * 5.0, 0.0, 1.0), skin.light, 0.20)
        roots = []
        for _ in range(7):
            x, yy = rng.uniform(0, 64), rng.uniform(0, 64)
            heading = rng.uniform(-0.5, 0.9)
            pts = [(x, yy)]
            for _ in range(6):
                heading += rng.uniform(-0.5, 0.5)
                x, yy = x + math.cos(heading) * 3.0, yy + math.sin(heading) * 2.0
                pts.append((x, yy))
            roots.append((pts, rng.uniform(0.35, 0.75)))
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(px, py + 0.35) for px, py in pts], w) for pts, w in roots]), skin.dark, 0.55)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, w) for pts, w in roots]), _mix(skin.light, (160, 128, 86), 0.4), 0.80)
        stones = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(1.0, 2.4), rng.uniform(-0.2, 0.2)) for _ in range(10)]
        for x, yy, r, t in stones:
            grey = _mix((112, 104, 94), (150, 140, 124) if t > 0 else (70, 64, 58), abs(t) * 2.0)
            tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x, yy + 0.4, r * 1.05, ry=r * 0.75)), skin.dark, 0.6)
            tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x, yy, r, ry=r * 0.7)), grey)
            tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x - r * 0.25, yy - r * 0.3, r * 0.5, ry=r * 0.25)), (200, 190, 170), 0.45)
        bits = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0, math.pi)) for _ in range(16)]
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x - math.cos(a) * 0.8, yy - math.sin(a) * 0.4), (x + math.cos(a) * 0.8, yy + math.sin(a) * 0.4)], 0.45) for x, yy, a in bits]), _mix(skin.accent, skin.base, 0.45), 0.55)
        grit = [(rng.uniform(0, 64), rng.uniform(0, 64)) for _ in range(40)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 0.3) for x, yy in grit]), skin.light, 0.35)
    elif skin.material == "schist":
        # Schist: rock made in thin layers under heat and weight. Here its
        # layers slant down to the right. Each layer has its own grey-green,
        # and the rock breaks across the layers in short joints, so it
        # stands in thin steps. Veins of white quartz run along a few
        # layers, and flakes of mica glint.
        lean = 0.25
        # A slope of one in four over 64 units is 16 units, so a layer
        # height of 4 repeats in x and in y: 16 layers fill the tile.
        warp = (tile.noise(4, 4, 2) - 0.5) * 2.4
        f = tile.y - tile.x * lean + warp
        layer = np.floor(f / 4.0).astype(int) % 16
        tones = np.array([rng.uniform(-0.20, 0.16) for _ in range(16)], dtype=np.float32)
        tile.put(np.ones_like(tile.alpha), skin.base)
        tile.tone(tones[layer] + (tile.noise(8, 8, 3) - 0.5) * 0.14)
        tile.put(np.clip((tile.noise(6, 6, 2) - 0.60) * 5.0, 0.0, 1.0), (96, 124, 96), 0.30)
        inside = f % 4.0
        tile.put(np.clip(1.0 - inside / 0.55, 0.0, 1.0), skin.dark, 0.80)
        tile.put(np.clip(1.0 - np.abs(inside - 0.75) / 0.3, 0.0, 1.0), skin.light, 0.35)
        tile.put(np.clip(1.0 - np.abs(inside - 2.2) / 0.18, 0.0, 1.0), skin.dark, 0.15)
        # Joints across the layers: each one a short crack from the top of
        # a layer to its bottom, at a slant across it.
        joints = []
        for k in range(16):
            for _ in range(rng.randint(1, 3)):
                x = rng.uniform(0, 64)
                top = k * 4.0 + x * lean
                joints.append([(x, top), (x + rng.uniform(-0.8, -0.2), top + 4.0 * rng.choice([1, 1, 2]))])
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.45) for pts in joints]), skin.dark, 0.80)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x + 0.5, y) for x, y in pts], 0.35) for pts in joints]), skin.light, 0.30)
        vein_layers = rng.sample(range(16), 3)
        vein = np.isin(layer, vein_layers) * np.clip(1.0 - np.abs(inside - 2.6) / 0.28, 0.0, 1.0) * np.clip((tile.noise(5, 5, 2) - 0.40) * 5.0, 0.0, 1.0)
        tile.put(vein, (228, 226, 210), 0.80)
        mica = [(rng.uniform(0, 64), rng.uniform(0, 64)) for _ in range(18)]
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x - 0.6, yy - 0.15), (x + 0.6, yy + 0.15)], 0.25) for x, yy in mica]), (236, 238, 226), 0.65)
    elif skin.material == "granite_blocks":
        # Granite of Silla, cut in large square blocks and laid in courses
        # with fine joints, as in the kerbs of the royal tombs and in
        # Cheomseongdae. Granite is speckled: black grains of mica and pale
        # grains of feldspar in grey. The faces are dressed flat, with a
        # lit upper and left edge.
        tile.put(np.ones_like(tile.alpha), skin.dark)
        rows = 4
        row_h = 64.0 / rows
        for row in range(rows):
            y0 = row * row_h
            x0 = rng.uniform(0.0, 14.0)
            end = x0 + 64.0
            while x0 < end - 1.0:
                w = min(rng.choice([18.0, 22.0, 26.0, 30.0]), end - x0)
                if end - (x0 + w) < 12.0:
                    w = end - x0
                tone = rng.uniform(-0.10, 0.10)
                colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.5)
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.3, y0 + 0.3, x0 + w - 0.3, y0 + row_h - 0.3)), colour)
                tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 0.3, y0 + 0.3, x0 + w - 0.3, y0 + 1.1), _box(p, dx, dy, x0 + 0.3, y0 + 0.3, x0 + 1.0, y0 + row_h - 0.3))), skin.light, 0.40)
                tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 0.3, y0 + row_h - 1.0, x0 + w - 0.3, y0 + row_h - 0.3), _box(p, dx, dy, x0 + w - 1.0, y0 + 0.3, x0 + w - 0.3, y0 + row_h - 0.3))), skin.dark, 0.35)
                x0 += w
        tile.tone((tile.noise(6, 6, 3) - 0.5) * 0.10)
        dark_grains = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.22, 0.42)) for _ in range(130)]
        pale_grains = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.25, 0.5)) for _ in range(60)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r) for x, yy, r in pale_grains]), (236, 226, 214), 0.45)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r) for x, yy, r in dark_grains]), (44, 40, 40), 0.55)
        tile.put(np.clip((tile.noise(3, 10, 2) - 0.62) * 4.0, 0.0, 1.0), (84, 92, 70), 0.22)
    elif skin.material == "bluestone_paving":
        # Slabs of grey bluestone, as the Song paved the streets and the
        # causeways of Hangzhou. The slabs are long and of each length,
        # laid in rows of each height with fine joints, and each slab has
        # its own grey. Feet wore the faces smooth, water left soft stains,
        # and moss grows in some of the joints.
        tile.put(np.ones_like(tile.alpha), skin.dark)
        joints = []
        y0 = 0.0
        for h in (10.0, 12.0, 9.0, 11.0, 12.0, 10.0):
            x0 = rng.uniform(0.0, 20.0)
            end = x0 + 64.0
            while x0 < end - 1.0:
                w = min(rng.choice([12.0, 16.0, 20.0, 26.0]), end - x0)
                if end - (x0 + w) < 8.0:
                    w = end - x0
                tone = rng.uniform(-0.12, 0.10)
                colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.6)
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.35, y0 + 0.35, x0 + w - 0.35, y0 + h - 0.35)), colour)
                tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 0.35, y0 + 0.35, x0 + w - 0.35, y0 + 1.0), _box(p, dx, dy, x0 + 0.35, y0 + 0.35, x0 + 0.9, y0 + h - 0.35))), skin.light, 0.30)
                tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 0.35, y0 + h - 1.0, x0 + w - 0.35, y0 + h - 0.35), _box(p, dx, dy, x0 + w - 0.9, y0 + 0.35, x0 + w - 0.35, y0 + h - 0.35))), skin.dark, 0.30)
                joints.append((x0, y0, w, h))
                x0 += w
            y0 += h
        tile.tone((tile.noise(6, 6, 3) - 0.5) * 0.14)
        tile.put(np.clip((tile.noise(5, 5, 2) - 0.58) * 4.0, 0.0, 1.0), skin.dark, 0.22)
        # Moss in the joints: the joint lines, a little wider, where a
        # noise is high.
        seams = tile.mask(lambda p, dx, dy: [(_box(p, dx, dy, x0 - 0.2, y0 - 0.6, x0 + w + 0.2, y0 + 0.6), _box(p, dx, dy, x0 - 0.6, y0, x0 + 0.6, y0 + h)) for x0, y0, w, h in joints])
        tile.put(seams * np.clip((tile.noise(8, 8, 2) - 0.64) * 6.0, 0.0, 1.0), skin.cap_colour, 0.55)
        grit = [(rng.uniform(0, 64), rng.uniform(0, 64)) for _ in range(50)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 0.25) for x, yy in grit]), skin.dark, 0.35)
    elif skin.material == "raked_gravel":
        # White gravel in a courtyard of Heian-kyo, raked in parallel lines.
        # The rake leaves ridges of gravel with flat tops and narrow furrows
        # between them, where the dark earth shows. The lines are straight
        # and wave only a little. A few small dark stones lie in the gravel.
        tile.put(np.ones_like(tile.alpha), skin.dark)
        period = 4.0
        f = tile.y + 0.35 * np.sin(tile.x * 2.0 * math.pi / 64.0) + (tile.noise(3, 6, 2) - 0.5) * 0.3
        phase = f % period
        ridge = np.clip((period * 0.5 - np.abs(phase - period * 0.5)) / 0.9, 0.0, 1.0)
        tile.put(ridge, skin.base)
        tile.put(ridge * np.clip(1.0 - np.abs(phase - 1.0) / 0.45, 0.0, 1.0), skin.light, 0.45)
        tile.put(ridge * np.clip(1.0 - np.abs(phase - 3.1) / 0.45, 0.0, 1.0), skin.dark, 0.22)
        tile.tone((tile.noise(8, 8, 3) - 0.5) * 0.12)
        # The grains of the gravel: pale and grey points on the ridges.
        grains = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.2, 0.4)) for _ in range(220)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r) for x, yy, r in grains[::2]]) * ridge, (236, 232, 222), 0.50)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r) for x, yy, r in grains[1::2]]) * ridge, _mix(skin.base, skin.dark, 0.45), 0.50)
        stones = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.6, 1.1)) for _ in range(5)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy + 0.3, r + 0.3, ry=(r + 0.3) * 0.75) for x, yy, r in stones]), skin.dark, 0.6)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r, ry=r * 0.75) for x, yy, r in stones]), (104, 96, 88))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - r * 0.3, yy - r * 0.3, r * 0.45, ry=r * 0.25) for x, yy, r in stones]), (170, 162, 150), 0.6)
    elif skin.material == "palace_granite":
        # Long blocks of pale granite, as the masons of Joseon laid the
        # terraces of Gyeongbokgung: even courses, each block twice as long
        # as it is high and half a block along from the course under it.
        # Each face has a smooth margin round a field of fine slanted tool
        # marks, and the stone is speckled.
        tile.put(np.ones_like(tile.alpha), skin.dark)
        row_h, unit = 16.0, 32.0
        hatch = np.clip(1.0 - np.abs(((tile.x + tile.y) % 1.3) - 0.65) / 0.16, 0.0, 1.0)
        for row in range(4):
            y0 = row * row_h
            for i in range(2):
                x0 = i * unit + (unit * 0.5 if row % 2 else 0.0) + rng.uniform(-1.5, 1.5) * (i == 1)
                w = unit if i == 0 else 64.0 - (x0 - (unit * 0.5 if row % 2 else 0.0))
                tone = rng.uniform(-0.08, 0.08)
                colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.5)
                face = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.3, y0 + 0.3, x0 + w - 0.3, y0 + row_h - 0.3))
                tile.put(face, colour)
                field = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 2.0, y0 + 2.0, x0 + w - 2.0, y0 + row_h - 2.0))
                tile.put(field * hatch, skin.dark, 0.22)
                tile.put((face - field).clip(0, 1) * tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 0.3, y0 + 0.3, x0 + w - 0.3, y0 + 1.1), _box(p, dx, dy, x0 + 0.3, y0 + 0.3, x0 + 1.1, y0 + row_h - 0.3))), skin.light, 0.45)
                tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 0.3, y0 + row_h - 1.0, x0 + w - 0.3, y0 + row_h - 0.3), _box(p, dx, dy, x0 + w - 1.0, y0 + 0.3, x0 + w - 0.3, y0 + row_h - 0.3))), skin.dark, 0.35)
                tile.put(field * tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 2.0, y0 + 2.0, x0 + w - 2.0, y0 + 2.4), _box(p, dx, dy, x0 + 2.0, y0 + 2.0, x0 + 2.4, y0 + row_h - 2.0))), skin.dark, 0.25)
        tile.tone((tile.noise(6, 6, 3) - 0.5) * 0.08)
        dark_grains = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.2, 0.36)) for _ in range(90)]
        pale_grains = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.22, 0.42)) for _ in range(50)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r) for x, yy, r in pale_grains]), (240, 234, 222), 0.40)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r) for x, yy, r in dark_grains]), (50, 46, 44), 0.45)
        tile.put(np.clip((tile.noise(3, 8, 2) - 0.64) * 4.0, 0.0, 1.0), (96, 90, 74), 0.18)
    elif skin.material == "river_silt":
        # The silt that the Buriganga lays down in each flood: thin layers
        # of dark and less dark mud that wave a little, lenses of paler
        # sand between them, fine roots of grass that go down through
        # them, and small pale bits of shell.
        tile.put(np.ones_like(tile.alpha), skin.base)
        warp = np.sin(tile.x * 2.0 * math.pi / 32.0 + 1.3) * 0.7 + (tile.noise(4, 4, 3) - 0.5) * 4.0
        layers = 0.5 + 0.5 * np.sin((tile.y + warp) * 2.0 * math.pi / 4.0)
        tile.put(np.clip(layers * 1.6 - 0.6, 0.0, 1.0) * (0.4 + 0.6 * tile.noise(3, 8, 2)), skin.dark, 0.50)
        tile.put(np.clip((tile.noise(3, 12, 3) - 0.60) * 5.0, 0.0, 1.0), skin.light, 0.35)
        tile.tone((tile.noise(8, 8, 2) - 0.5) * 0.12)
        roots = []
        for _ in range(9):
            x, yy = rng.uniform(0, 64), rng.uniform(0, 64)
            pts = [(x, yy)]
            for _ in range(5):
                x, yy = x + rng.uniform(-0.9, 0.9), yy + rng.uniform(1.0, 2.0)
                pts.append((x, yy))
            roots.append(pts)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.22) for pts in roots]), _mix(skin.light, (196, 176, 136), 0.4), 0.35)
        shells = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.25, 0.5)) for _ in range(14)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r, ry=r * 0.5) for x, yy, r in shells]), (210, 200, 180), 0.45)
    elif skin.material == "laterite_brick":
        # A wall of the Company's Calcutta: courses of red laterite, a stone
        # full of small pits and of ochre streaks, and between them bands
        # of two courses of thin red brick in lime mortar.
        mortar = _mix(skin.light, (226, 214, 190), 0.55)
        tile.put(np.ones_like(tile.alpha), _mix(skin.dark, mortar, 0.25))
        pits = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.2, 0.55)) for _ in range(160)]
        for band in range(4):
            y0 = band * 16.0
            x = rng.uniform(0.0, 20.0)
            for w in (20.0, 22.0, 22.0):
                tone = rng.uniform(-0.10, 0.10)
                colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.6)
                block = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x + 0.4, y0 + 0.4, x + w - 0.4, y0 + 10.0 - 0.4))
                tile.put(block, colour)
                tile.put(block * tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x + 0.4, y0 + 0.4, x + w - 0.4, y0 + 1.1), _box(p, dx, dy, x + 0.4, y0 + 0.4, x + 1.1, y0 + 9.6))), skin.light, 0.30)
                tile.put(block * tile.mask(lambda p, dx, dy: _box(p, dx, dy, x + 0.4, y0 + 8.9, x + w - 0.4, y0 + 9.6)), skin.dark, 0.35)
                x += w
            for row in range(2):
                yb = y0 + 10.0 + row * 3.0
                x = rng.uniform(0.0, 8.0)
                while x < 64.0 + 8.0:
                    tone = rng.uniform(-0.12, 0.12)
                    colour = _mix(_mix(skin.base, (180, 80, 56), 0.35), skin.light if tone > 0 else skin.dark, abs(tone) * 1.5)
                    brick = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x + 0.3, yb + 0.35, x + 8.0 - 0.3, yb + 3.0 - 0.35))
                    tile.put(brick, colour)
                    tile.put(brick * tile.mask(lambda p, dx, dy: _box(p, dx, dy, x + 0.3, yb + 0.35, x + 7.7, yb + 0.9)), skin.light, 0.22)
                    x += 8.0
        laterite = np.zeros_like(tile.alpha)
        for band in range(4):
            laterite = np.maximum(laterite, ((tile.y >= band * 16.0) & (tile.y < band * 16.0 + 10.0)).astype(np.float32))
        tile.put(laterite * tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r, ry=r * 0.7) for x, yy, r in pits]), skin.dark, 0.55)
        tile.put(laterite * np.clip((tile.noise(6, 14, 2) - 0.62) * 5.0, 0.0, 1.0), (206, 150, 80), 0.30)
        tile.tone((tile.noise(4, 4, 3) - 0.5) * 0.16)
    elif skin.material == "brick_paving":
        # Red brick paving laid in a basket weave: in each square of eight
        # units two bricks lie side by side, along in one square and across
        # in the next. Sand fills the joints, feet wore the faces, and moss
        # grows in some joints.
        tile.put(np.ones_like(tile.alpha), _mix(skin.dark, (150, 130, 100), 0.35))
        bricks = []
        for i in range(8):
            for j in range(8):
                x0, y0 = i * 8.0, j * 8.0
                if (i + j) % 2:
                    bricks += [(x0, y0, x0 + 8.0, y0 + 4.0), (x0, y0 + 4.0, x0 + 8.0, y0 + 8.0)]
                else:
                    bricks += [(x0, y0, x0 + 4.0, y0 + 8.0), (x0 + 4.0, y0, x0 + 8.0, y0 + 8.0)]
        for x0, y0, x1, y1 in bricks:
            tone = rng.uniform(-0.14, 0.12)
            colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.5)
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.35, y0 + 0.35, x1 - 0.35, y1 - 0.35)), colour)
            tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 0.35, y0 + 0.35, x1 - 0.35, y0 + 0.9), _box(p, dx, dy, x0 + 0.35, y0 + 0.35, x0 + 0.9, y1 - 0.35))), skin.light, 0.28)
            tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 0.35, y1 - 0.9, x1 - 0.35, y1 - 0.35), _box(p, dx, dy, x1 - 0.9, y0 + 0.35, x1 - 0.35, y1 - 0.35))), skin.dark, 0.28)
        tile.tone((tile.noise(5, 5, 3) - 0.5) * 0.16)
        joints = 1.0 - tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x0 + 0.35, y0 + 0.35, x1 - 0.35, y1 - 0.35) for x0, y0, x1, y1 in bricks])
        tile.put(joints * np.clip((tile.noise(8, 8, 2) - 0.62) * 6.0, 0, 1), skin.cap_colour, 0.55)
        grit = [(rng.uniform(0, 64), rng.uniform(0, 64)) for _ in range(60)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 0.22) for x, yy in grit]), skin.dark, 0.35)
    elif skin.material == "ridged_laterite":
        # Red laterite earth laid in courses, as the builders of Benin laid
        # their walls: each course is a band with a rounded ridge on its top
        # that catches the light and a dark groove under it. The earth has
        # small pebbles, nodules of iron rust and the marks of the hands that
        # smoothed it.
        tile.put(np.ones_like(tile.alpha), skin.base)
        tile.tone((tile.noise(6, 6, 3) - 0.5) * 0.18)
        course = 64.0 / 6.0
        wave = tile.y + 0.6 * np.sin(tile.x * math.pi / 32.0 + 1.3)
        u = (wave % course) / course
        tile.put(np.clip(1.0 - np.abs(u - 0.10) / 0.08, 0.0, 1.0), skin.light, 0.45)
        tile.put(np.clip(1.0 - np.abs(u - 0.94) / 0.06, 0.0, 1.0), skin.dark, 0.60)
        tile.put(np.clip((u - 0.55) / 0.40, 0.0, 1.0), skin.dark, 0.16)
        strokes = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(2.0, 4.0)) for _ in range(14)]
        tile.put(tile.mask(lambda p, dx, dy: [p.arc([(x - r) * K + dx, (y - r * 0.4) * K + dy, (x + r) * K + dx, (y + r * 0.4) * K + dy], 200, 340, fill=255, width=max(1, int(0.25 * K))) for x, y, r in strokes]), skin.light, 0.22)
        pebbles = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(0.4, 1.0)) for _ in range(16)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y + 0.3, r, ry=r * 0.7) for x, y, r in pebbles]), skin.dark, 0.5)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r * 0.8, ry=r * 0.6) for x, y, r in pebbles]), _mix(skin.light, (220, 200, 180), 0.3), 0.7)
        nodules = [(rng.uniform(0, 64), rng.uniform(0, 64)) for _ in range(26)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.4) for x, y in nodules]), _mix(skin.dark, (120, 40, 20), 0.4), 0.7)
    else:  # earth
        tile.put(np.ones_like(tile.alpha), skin.base)
        tile.tone((tile.noise(6, 6, 4) - 0.5) * 0.5)
        stones = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(1.6, 4.2)) for _ in range(9)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y + 0.5, r, ry=r * 0.7) for x, y, r in stones]), skin.dark, 0.7)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r * 0.92, ry=r * 0.62) for x, y, r in stones]), _mix(skin.light, (150, 150, 150), 0.3))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - r * 0.25, y - r * 0.2, r * 0.45, ry=r * 0.26) for x, y, r in stones]), (220, 220, 210), 0.22)
        roots = []
        for _ in range(5):
            x, y = rng.uniform(0, 64), rng.uniform(0, 64)
            pts = [(x, y)]
            for _ in range(6):
                x, y = x + rng.uniform(2, 6), y + rng.uniform(-3, 3)
                pts.append((x, y))
            roots.append(pts)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.7) for pts in roots]), skin.light, 0.5)
        specks = [(rng.uniform(0, 64), rng.uniform(0, 64)) for _ in range(40)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.4) for x, y in specks]), skin.dark, 0.6)
    return tile.publish()


# ---------------------------------------------------------------------------
# Caps
# ---------------------------------------------------------------------------


def cap(skin: Skin) -> Image.Image:
    tile = Tile(CAP, True, False, skin.key, "cap")
    rng = tile.rng
    s = CAP_SURFACE
    y = tile.y
    if skin.cap == "deck":
        # The edge of a deck of planks: a thick board seen from its end, with
        # the butt joints of the planks, nails, and a dark seam under it.
        thick = 5.0
        body = ((y >= s - 0.4) & (y < s + thick)).astype(np.float32)
        tile.put(body, skin.cap_colour)
        tile.tone(((tile.noise(12, 2, 2) - 0.5) * 0.24) * body)
        tile.put(((y >= s - 0.4) & (y < s + 0.5)).astype(np.float32), _mix(skin.cap_colour, (255, 244, 220), 0.45))
        tile.put(((y >= s + thick - 0.9) & (y < s + thick)).astype(np.float32), skin.dark, 0.75)
        joints = [rng.uniform(0, 64) for _ in range(3)]
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 0.3, s, x + 0.3, s + thick) for x in joints]), skin.dark, 0.8)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x + side, s + 2.4, 0.45) for x in joints for side in (-1.4, 1.4)]), skin.dark, 0.7)
        # The shade the deck throws on the boards under it.
        tile.put(np.clip(1.0 - (y - s - thick) / 3.0, 0.0, 1.0) * (y >= s + thick), (0, 0, 0), 0.35)
        return tile.publish()
    if skin.cap == "pencil":
        # The top of the page is a line drawn in pencil, twice, as a hand
        # draws it; the paper under it is hatched.
        body = (y >= s - 0.3).astype(np.float32) * (y < s + 6.0)
        tile.put(body, skin.cap_colour)
        tile.put(np.clip((y - s - 3.0) / 3.0, 0, 1) * body, skin.base, 0.6)
        for k, (lift, width) in enumerate(((0.0, 1.4), (0.8, 0.6))):
            wobble = (tile.profile(6 + k * 3, 2) - 0.5) * 0.7
            tile.put((np.abs(y - s - lift - wobble[None, :]) < width * 0.5).astype(np.float32), skin.accent, 0.95 - k * 0.3)
        hatch = ((((tile.x - y) % 2.0) < 0.35) & (y > s + 1.4) & (y < s + 4.5)).astype(np.float32)
        tile.put(hatch, skin.accent, 0.30)
        tile.put(np.clip(1.0 - (y - s - 6.0) / 3.0, 0, 1) * (y >= s + 6.0), (0, 0, 0), 0.20)
        return tile.publish()
    if skin.cap == "pages":
        # The edges of the pages of the top book: a pale band of many thin
        # lines, gilt on its top, and the shade it throws under it.
        thick = 5.0
        body = ((y >= s - 0.3) & (y < s + thick)).astype(np.float32)
        tile.put(body, skin.cap_colour)
        lines = (((y - s) % 0.8) < 0.22) & (y > s + 1.2) & (y < s + thick - 0.6)
        tile.put(lines.astype(np.float32), _mix(skin.cap_colour, skin.dark, 0.35), 0.55)
        tile.tone(((tile.profile(10, 2) - 0.5) * 0.12)[None, :] * body)
        tile.put(((y >= s - 0.3) & (y < s + 1.0)).astype(np.float32), skin.accent)
        tile.put(((y >= s - 0.3) & (y < s + 0.3)).astype(np.float32), _mix(skin.accent, (255, 250, 220), 0.5))
        tile.put(((y >= s + thick - 0.8) & (y < s + thick)).astype(np.float32), skin.dark, 0.6)
        tile.put(np.clip(1.0 - (y - s - thick) / 3.0, 0.0, 1.0) * (y >= s + thick), (0, 0, 0), 0.35)
        return tile.publish()
    if skin.cap == "brass":
        # A rail of polished brass: a round top that catches the light, a
        # line cut along it, and a strip of red felt under it, as under the
        # keys of a piano.
        thick = 4.6
        body = ((y >= s - 0.2) & (y < s + thick)).astype(np.float32)
        tile.put(body, skin.cap_colour)
        tile.put(np.clip(1.0 - np.abs(y - s - 0.9) / 0.9, 0.0, 1.0) * body, (255, 244, 200), 0.75)
        tile.put(((y >= s + 2.5) & (y < s + 2.9)).astype(np.float32), _mix(skin.cap_colour, skin.dark, 0.6), 0.8)
        tile.put(((y >= s + 3.6) & (y < s + thick)).astype(np.float32), (140, 30, 44))
        tile.tone(((tile.profile(4, 2) - 0.5) * 0.18)[None, :] * body)
        tile.put(np.clip(1.0 - (y - s - thick) / 3.0, 0.0, 1.0) * (y >= s + thick), (0, 0, 0), 0.40)
        return tile.publish()
    if skin.cap == "footlights":
        # The edge of a stage: a board with a moulding of gold, and in it a
        # footlight each sixteen units, a small warm light in a hood.
        thick = 5.0
        body = ((y >= s - 0.2) & (y < s + thick)).astype(np.float32)
        tile.put(body, _mix(skin.base, skin.dark, 0.3))
        tile.put(((y >= s - 0.2) & (y < s + 1.3)).astype(np.float32), skin.cap_colour)
        tile.put(((y >= s - 0.2) & (y < s + 0.4)).astype(np.float32), _mix(skin.cap_colour, (255, 250, 220), 0.5))
        tile.put(((y >= s + 3.6) & (y < s + 4.3)).astype(np.float32), skin.cap_colour, 0.8)
        hoods = tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 16.0 + 8.0, s + 2.5, 2.2, ry=1.1) for k in range(4)])
        tile.put(hoods, skin.dark)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 16.0 + 8.0, s + 2.2, 2.6, ry=1.6) for k in range(4)], blur=0.9), (255, 220, 150), 0.55)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 16.0 + 8.0, s + 2.3, 1.0, ry=0.6) for k in range(4)]), (255, 244, 210))
        tile.put(np.clip(1.0 - (y - s - thick) / 3.0, 0.0, 1.0) * (y >= s + thick), (0, 0, 0), 0.40)
        return tile.publish()
    if skin.cap == "copper":
        # A plate of copper on the edge: rivets, joints, and the green of
        # age in a few places.
        thick = 4.8
        body = ((y >= s - 0.2) & (y < s + thick)).astype(np.float32)
        tile.put(body, skin.cap_colour)
        tile.tone(((tile.noise(10, 2, 2) - 0.5) * 0.20) * body)
        tile.put(((y >= s - 0.2) & (y < s + 0.7)).astype(np.float32), _mix(skin.cap_colour, (255, 226, 190), 0.55))
        tile.put(((y >= s + thick - 0.8) & (y < s + thick)).astype(np.float32), skin.dark, 0.7)
        patina = np.clip((tile.noise(8, 2, 3) - 0.62) * 6.0, 0.0, 1.0) * body * (y > s + 1.0)
        tile.put(patina, (86, 160, 136), 0.55)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32.0 - 0.3, s, k * 32.0 + 0.3, s + thick) for k in range(3)]), skin.dark, 0.7)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 8.0 + 4.0, s + 2.6, 0.65) for k in range(8)]), _mix(skin.cap_colour, (255, 236, 200), 0.5))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 8.0 + 4.2, s + 2.9, 0.65) for k in range(8)]), skin.dark, 0.35)
        tile.put(np.clip(1.0 - (y - s - thick) / 3.0, 0.0, 1.0) * (y >= s + thick), (0, 0, 0), 0.40)
        return tile.publish()
    if skin.cap == "kerb":
        # A kerb of round stones set in the earth, of a few sizes, with moss
        # in the joints between them.
        stones = []
        x = rng.uniform(0.0, 3.0)
        end = x + 64.0
        while x < end - 2.0:
            w = min(rng.uniform(5.0, 9.0), end - x)
            if end - (x + w) < 4.0:
                w = end - x
            stones.append((x, w, rng.uniform(4.2, 5.6), rng.uniform(-0.18, 0.14)))
            x += w
        tile.put(((y >= s) & (y < s + 4.8)).astype(np.float32), skin.dark)
        tile.put(np.clip(1.0 - (y - s - 4.8) / 3.0, 0.0, 1.0) * (y >= s + 4.8), (0, 0, 0), 0.32)
        for x0, w, h, tone in stones:
            colour = _mix(skin.cap_colour, (255, 255, 250) if tone > 0 else skin.dark, abs(tone) * 1.5)
            soft = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.35, s - 0.6, x0 + w - 0.35, s - 0.6 + h), blur=0.9)
            body = np.clip((soft - 0.5) * 6.0 + 0.5, 0.0, 1.0)
            tile.put(body, colour)
            tile.put(body * np.clip(1.0 - (y - s + 0.6) / 1.4, 0.0, 1.0), (240, 236, 226), 0.35)
            tile.put(body * np.clip((y - s - h + 2.4) / 1.8, 0.0, 1.0), skin.dark, 0.45)
        # The kerb covers its surface line from end to end.
        tile.put(((y >= s - 0.2) & (y < s + 1.2)).astype(np.float32), _mix(skin.cap_colour, (240, 236, 226), 0.25), 0.55)
        moss = [(x0, s + rng.uniform(0.5, 3.5)) for x0, _w, _h, _t in stones]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 0.8, ry=0.5) for x, yy in moss]), (86, 110, 70), 0.75)
        return tile.publish()
    if skin.cap == "hazard":
        # The steel edge of a deck: a light lip, then stripes at a slant of
        # the accent and of pale warning paint, eight to the tile. The
        # stripes are on the face of the edge only: nothing is under it.
        thick = 5.0
        body = ((y >= s) & (y < s + thick)).astype(np.float32)
        tile.put(body, skin.cap_colour)
        tile.put(((y >= s) & (y < s + 0.7)).astype(np.float32), _mix(skin.cap_colour, (255, 255, 255), 0.42))
        face = ((y >= s + 1.5) & (y < s + thick - 0.8)).astype(np.float32)
        stripe = (np.mod((tile.x + (y - s)) / 8.0, 1.0) < 0.5).astype(np.float32)
        tile.put(face * stripe, _mix(skin.accent, skin.dark, 0.12))
        tile.put(face * (1.0 - stripe), _mix((214, 196, 140), skin.dark, 0.18))
        tile.put(((y >= s + thick - 0.8) & (y < s + thick)).astype(np.float32), skin.dark, 0.7)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 16 + 8, s + 1.05, 0.4) for k in range(4)]), skin.dark, 0.6)
        return tile.publish()
    if skin.cap == "rim":
        # The edge of the void: one crisp white line on the surface, and the
        # black of the block under it. No shade.
        tile.put(((y >= s - 0.3) & (y < s + 1.1)).astype(np.float32), skin.dark)
        tile.put(((y >= s - 0.3) & (y < s + 0.9)).astype(np.float32), skin.cap_colour)
        return tile.publish()
    if skin.cap == "bricks_on_edge":
        # A course of mudbricks laid on their edges: an end of a brick each
        # four units, of its own tone, the top worn round.
        thick = 5.2
        tile.put(((y >= s - 0.3) & (y < s + thick)).astype(np.float32), _mix(skin.dark, skin.base, 0.3))
        for k in range(16):
            x0 = k * 4.0
            tone = rng.uniform(-0.16, 0.12)
            colour = _mix(skin.cap_colour, (255, 236, 200) if tone > 0 else skin.dark, abs(tone) * 1.4)
            soft = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.3, s - 0.6, x0 + 3.7, s + thick - 0.4), blur=0.4)
            tile.put(np.clip((soft - 0.5) * 5.0 + 0.5, 0.0, 1.0), colour)
        tile.put(((y >= s - 0.3) & (y < s + 0.9)).astype(np.float32), _mix(skin.cap_colour, (255, 240, 210), 0.35), 0.75)
        tile.put(((y >= s + thick - 0.9) & (y < s + thick)).astype(np.float32), skin.dark, 0.6)
        tile.tone(((tile.noise(16, 2, 2) - 0.5) * 0.20) * (tile.alpha > 0))
        tile.put(np.clip(1.0 - (y - s - thick) / 3.0, 0.0, 1.0) * (y >= s + thick), (0, 0, 0), 0.34)
        return tile.publish()
    if skin.cap == "hieroglyphs":
        # A band of sandstone with a roll moulding on its top and signs cut
        # in it: an ankh, an eye, water, a reed and a bird, painted in lapis
        # and red.
        thick = 6.4
        body = ((y >= s - 0.3) & (y < s + thick)).astype(np.float32)
        tile.put(body, skin.cap_colour)
        tile.tone(((tile.noise(12, 2, 2) - 0.5) * 0.14) * body)
        tile.put(((y >= s - 0.3) & (y < s + 1.1)).astype(np.float32), _mix(skin.cap_colour, (255, 244, 214), 0.45))
        tile.put(((y >= s + 1.1) & (y < s + 1.5)).astype(np.float32), skin.dark, 0.55)
        tile.put(((y >= s + thick - 0.7) & (y < s + thick)).astype(np.float32), skin.dark, 0.6)
        red = (168, 64, 44)
        c = s + 3.9

        def sign(p, dx, dy, k, x):
            kind = k % 5
            if kind == 0:  # ankh
                p.ellipse([(x - 0.8) * K + dx, (c - 2.3) * K + dy, (x + 0.8) * K + dx, (c - 0.4) * K + dy], outline=255, width=int(0.4 * K))
                _line(p, dx, dy, [(x, c - 0.5), (x, c + 2.0)], 0.45)
                _line(p, dx, dy, [(x - 1.3, c - 0.2), (x + 1.3, c - 0.2)], 0.45)
            elif kind == 1:  # eye
                _dot(p, dx, dy, x, c - 0.6, 1.6, ry=0.7)
                _line(p, dx, dy, [(x - 0.4, c + 0.1), (x - 0.9, c + 1.8)], 0.35)
                _line(p, dx, dy, [(x + 0.6, c + 0.1), (x + 1.4, c + 1.2), (x + 1.9, c + 0.9)], 0.35)
            elif kind == 2:  # water
                _line(p, dx, dy, [(x - 1.8 + i * 0.6, c + (0.4 if i % 2 else -0.4)) for i in range(7)], 0.35)
                _line(p, dx, dy, [(x - 1.8 + i * 0.6, c + 1.4 + (0.4 if i % 2 else -0.4)) for i in range(7)], 0.35)
            elif kind == 3:  # reed
                _line(p, dx, dy, [(x, c + 2.0), (x, c - 1.6)], 0.4)
                _poly(p, dx, dy, [(x, c - 2.2), (x + 1.0, c - 1.0), (x, c - 0.6)])
            else:  # bird
                _dot(p, dx, dy, x, c, 1.3, ry=0.8)
                _dot(p, dx, dy, x + 1.2, c - 1.0, 0.5)
                _line(p, dx, dy, [(x - 1.2, c + 0.2), (x - 2.0, c + 0.8)], 0.35)
                _line(p, dx, dy, [(x, c + 0.6), (x, c + 2.0)], 0.25)

        for k in range(8):
            x = k * 8.0 + 4.0
            colour = skin.accent if k % 2 == 0 else red
            tile.put(tile.mask(lambda p, dx, dy: sign(p, dx, dy, k, x + 0.25)), skin.dark, 0.35)
            tile.put(tile.mask(lambda p, dx, dy: sign(p, dx, dy, k, x)), colour, 0.85)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 8.0 - 0.15, s + 1.6, k * 8.0 + 0.15, s + thick - 0.8) for k in range(9)]), skin.dark, 0.35)
        tile.put(np.clip(1.0 - (y - s - thick) / 3.0, 0.0, 1.0) * (y >= s + thick), (0, 0, 0), 0.36)
        return tile.publish()
    if skin.cap == "meander":
        # A band of marble with the key pattern of the Greeks in terracotta:
        # one line that runs along and turns in on itself each eight units.
        thick = 6.2
        body = ((y >= s - 0.3) & (y < s + thick)).astype(np.float32)
        tile.put(body, skin.cap_colour)
        tile.put(((y >= s - 0.3) & (y < s + 0.6)).astype(np.float32), (255, 255, 250), 0.7)
        tile.put(((y >= s + 0.9) & (y < s + 1.3)).astype(np.float32), skin.accent, 0.8)
        tile.put(((y >= s + thick - 1.3) & (y < s + thick - 0.9)).astype(np.float32), skin.accent, 0.8)
        t, b = s + 1.8, s + thick - 1.8
        h = b - t

        def key(p, dx, dy, x):
            _line(p, dx, dy, [(x, b), (x, t), (x + 6.0, t), (x + 6.0, b - h * 0.28), (x + 2.4, b - h * 0.28), (x + 2.4, t + h * 0.38), (x + 4.0, t + h * 0.38)], 0.55)
            _line(p, dx, dy, [(x, b), (x + 8.0, b)], 0.55)

        tile.put(tile.mask(lambda p, dx, dy: [key(p, dx, dy, k * 8.0 + 0.5) for k in range(8)]), skin.accent)
        tile.put(((y >= s + thick - 0.6) & (y < s + thick)).astype(np.float32), skin.dark, 0.5)
        tile.put(np.clip(1.0 - (y - s - thick) / 3.0, 0.0, 1.0) * (y >= s + thick), (0, 0, 0), 0.34)
        return tile.publish()
    if skin.cap == "glazed":
        # A course of glazed tiles: turquoise and cobalt by turns, a flower
        # of four petals on each, a shine on the glaze, white grout.
        thick = 5.6
        body = ((y >= s - 0.3) & (y < s + thick)).astype(np.float32)
        tile.put(body, (226, 220, 200))
        cobalt = (40, 60, 140)
        for k in range(8):
            x0 = k * 8.0
            colour = skin.cap_colour if k % 2 == 0 else cobalt
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.35, s - 0.3, x0 + 7.65, s + thick - 0.35)), colour)
            cx, cy = x0 + 4.0, s + thick * 0.5
            petal = (240, 220, 140) if k % 2 == 0 else (236, 236, 226)
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, cx + ox, cy + oy, 0.75) for ox, oy in ((-1.1, 0.0), (1.1, 0.0), (0.0, -1.1), (0.0, 1.1))]), petal, 0.9)
            tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy, 0.5)), (196, 60, 50))
        tile.put(((y >= s - 0.3) & (y < s + 0.7)).astype(np.float32), (255, 255, 255), 0.35)
        tile.put(((y >= s + thick - 0.8) & (y < s + thick)).astype(np.float32), skin.dark, 0.55)
        tile.put(np.clip(1.0 - (y - s - thick) / 3.0, 0.0, 1.0) * (y >= s + thick), (0, 0, 0), 0.36)
        return tile.publish()
    if skin.cap == "maya_frieze":
        # A frieze of stucco painted red, with a cream moulding on its top,
        # and a glyph block each sixteen units with a number in it in bars
        # and dots: a shell (zero), seven, thirteen and nineteen.
        thick = 6.6
        body = ((y >= s - 0.3) & (y < s + thick)).astype(np.float32)
        tile.put(body, skin.cap_colour)
        tile.tone(((tile.noise(12, 2, 2) - 0.5) * 0.16) * body)
        cream = _mix(skin.light, (250, 244, 226), 0.4)
        tile.put(((y >= s - 0.3) & (y < s + 1.3)).astype(np.float32), cream)
        tile.put(((y >= s + 1.0) & (y < s + 1.3)).astype(np.float32), skin.dark, 0.5)
        tile.put(((y >= s + thick - 0.8) & (y < s + thick)).astype(np.float32), skin.dark, 0.7)
        ink = _mix(skin.dark, (20, 16, 14), 0.5)
        for k, (bars, dots) in enumerate(((None, 0), (1, 2), (2, 3), (3, 4))):
            x0 = k * 16.0 + 4.0
            block = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, s + 1.8, x0 + 8.0, s + 6.0), blur=0.15)
            tile.put(block, cream, 0.92)
            tile.put(block * (tile.y > s + 5.4), skin.dark, 0.25)
            if bars is None:
                shell = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, x0 + 4.0, s + 3.9, 2.6, ry=1.3), _poly(p, dx, dy, [(x0 + 1.6, s + 3.9), (x0 + 0.8, s + 3.0), (x0 + 1.0, s + 4.8)])))
                tile.put(shell, ink, 0.85)
                tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x0 + 2.8 + j * 1.0, s + 3.1), (x0 + 2.8 + j * 1.0, s + 4.7)], 0.22) for j in range(4)]), cream, 0.9)
            else:
                tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x0 + 1.0, s + 5.2 - j * 0.9, x0 + 7.0, s + 5.7 - j * 0.9) for j in range(bars)]), ink, 0.9)
                top = s + 5.2 - bars * 0.9
                gap = 6.0 / (dots + 1)
                tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x0 + 1.0 + gap * (j + 1), top - 0.4, 0.38) for j in range(dots)]), ink, 0.9)
        tile.put(np.clip(1.0 - (y - s - thick) / 3.0, 0.0, 1.0) * (y >= s + thick), (0, 0, 0), 0.36)
        return tile.publish()
    if skin.cap == "polished_earth":
        # The top course of a wall of Benin: earth darker than the wall,
        # rubbed smooth until it shines. Its top is round and lit, a soft
        # shine runs along it, and its lower edge is a ridge over a groove.
        thick = 5.6
        body = ((y >= s - 0.4) & (y < s + thick)).astype(np.float32)
        tile.put(body, skin.cap_colour)
        tile.tone(((tile.noise(10, 2, 2) - 0.5) * 0.14) * body)
        tile.put(np.clip(1.0 - np.abs(y - s - 0.2) / 0.7, 0.0, 1.0) * body, _mix(skin.cap_colour, skin.light, 0.55), 0.8)
        shine = np.clip(1.0 - np.abs(y - s - 1.6) / 0.5, 0.0, 1.0) * np.clip((tile.noise(6, 1, 2) - 0.35) * 3.0, 0.0, 1.0)
        tile.put(shine * body, (255, 226, 190), 0.30)
        tile.put(((y >= s + thick - 1.4) & (y < s + thick - 0.8)).astype(np.float32), _mix(skin.cap_colour, skin.light, 0.30), 0.7)
        tile.put(((y >= s + thick - 0.8) & (y < s + thick)).astype(np.float32), skin.dark, 0.8)
        tile.put(np.clip(1.0 - (y - s - thick) / 3.0, 0.0, 1.0) * (y >= s + thick), (0, 0, 0), 0.34)
        return tile.publish()
    if skin.cap == "young_rice":
        # The top of a flooded paddy: dark wet mud under a thin film of
        # water that shines, and young rice that stands out of the water in
        # clumps, one each four units in a row, as the planters set it. Each
        # clump is a fan of thin bright blades.
        lower = s + 4.6 + tile.profile(8, 3)[None, :] * 1.6
        body = np.clip((lower - y) * K * 0.5 + 0.5, 0, 1) * (y >= s - 0.3)
        tile.put(np.clip((lower + 2.5 - y) / 2.5, 0, 1) * (y >= s), (0, 0, 0), 0.32)
        mud = _mix(skin.base, skin.dark, 0.55)
        tile.put(body, mud)
        tile.tone((tile.noise(12, 3, 2) - 0.5) * 0.14 * body)
        water = body * np.clip(1.0 - (y - s) / 1.4, 0, 1)
        tile.put(water, (150, 176, 182), 0.75)
        tile.put(body * np.clip(1.0 - np.abs(y - s - 0.25) / 0.35, 0, 1), (236, 246, 246), 0.8)
        tile.put(body * np.clip((y - (lower - 1.4)) / 1.4, 0, 1), skin.dark, 0.45)
        clumps = []
        for k in range(16):
            cx = k * 4.0 + 2.0 + rng.uniform(-0.6, 0.6)
            h = rng.uniform(2.8, 4.0)
            for j in range(5):
                t = j / 4.0 - 0.5
                tip = (cx + t * 2.6 + rng.uniform(-0.3, 0.3), s - h * (1.0 - abs(t) * 0.5) * rng.uniform(0.85, 1.05))
                clumps.append(([(cx + t * 0.5 - 0.18, s + 0.6), (cx + t * 0.5 + 0.18, s + 0.6), tip], j % 2))
        for shade in (1, 0):
            colour = _mix(skin.cap_colour, skin.dark, 0.25) if shade else skin.cap_colour
            tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, pts) for pts, kind in clumps if kind == shade]), colour)
        # The rice is mirrored in the water at its foot.
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(pts[0][0], s + 0.4), (pts[0][0], s + 1.4)], 0.3) for pts, _ in clumps[::5]]) * body, skin.cap_colour, 0.35)
        return tile.publish()
    if skin.cap == "packed_earth":
        # The top of a platform of Caral: earth and clay packed hard by many
        # feet. Its top is flat and a little lit, small stones show in it, and
        # its lower edge has crumbled a little onto the stones of the wall.
        lower = s + 4.4 + tile.profile(8, 3)[None, :] * 1.6
        body = np.clip((lower - y) * K * 0.5 + 0.5, 0, 1) * (y >= s - 0.3)
        tile.put(np.clip((lower + 2.5 - y) / 2.5, 0, 1) * (y >= s), (0, 0, 0), 0.30)
        tile.put(body, skin.cap_colour)
        tile.tone((tile.noise(12, 3, 2) - 0.5) * 0.16 * body)
        tile.put(body * np.clip(1.0 - np.abs(y - s) / 0.7, 0, 1), _mix(skin.cap_colour, (255, 240, 210), 0.45), 0.8)
        tile.put(body * np.clip((y - (lower - 1.6)) / 1.6, 0, 1), skin.dark, 0.40)
        gravel = [(rng.uniform(0, 64), s + rng.uniform(1.0, 3.6), rng.uniform(0.3, 0.6)) for _ in range(26)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r, ry=r * 0.7) for x, yy, r in gravel]) * body, _mix(skin.base, skin.light, 0.4), 0.8)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x + r * 0.2, yy + r * 0.3, r * 0.6, ry=r * 0.35) for x, yy, r in gravel]) * body, skin.dark, 0.35)
        return tile.publish()
    if skin.cap == "ichu":
        # The cap of the high plain: a thin layer of dark soil under ichu, a
        # tawny grass that grows in tussocks. A tussock is a dense clump of
        # thin, stiff blades that fan up and out from one base. Short grass
        # grows between the tussocks.
        lower = s + 3.6 + tile.profile(8, 3)[None, :] * 2.4
        body = np.clip((lower - y) * K * 0.5 + 0.5, 0, 1) * (y >= s - 0.3)
        tile.put(np.clip((lower + 2.5 - y) / 2.5, 0, 1) * (y >= s), (0, 0, 0), 0.32)
        tile.put(body, _mix(skin.cap_colour, skin.dark, 0.55))
        tile.put(body * np.clip(1.0 - np.abs(y - s - 0.4) / 1.2, 0, 1), _mix(skin.cap_colour, skin.dark, 0.25), 0.8)
        short = []
        for _ in range(60):
            x = rng.uniform(0, 64)
            h = rng.uniform(0.8, 1.8)
            short.append([(x - 0.3, s + 0.8), (x + 0.3, s + 0.8), (x + rng.uniform(-0.6, 0.6), s - h)])
        tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, pts) for pts in short]), _mix(skin.cap_colour, skin.dark, 0.15))
        for k in range(6):
            cx = k * (64.0 / 6.0) + rng.uniform(-2.0, 2.0)
            h = rng.uniform(2.6, 3.8)
            blades = []
            for j in range(13):
                t = j / 12.0 - 0.5
                tip = (cx + t * 5.0 + rng.uniform(-0.3, 0.3), s - h * (1.0 - abs(t) * 0.6) * rng.uniform(0.85, 1.05))
                blades.append([(cx + t * 1.4 - 0.25, s + 1.0), (cx + t * 1.4 + 0.25, s + 1.0), tip])
            for shade, part in ((0.0, blades[::2]), (0.30, blades[1::2])):
                tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, pts) for pts in part]), _mix(skin.cap_colour, (255, 244, 200), shade))
        return tile.publish()
    if skin.cap == "leaf_litter":
        # The floor of a chestnut forest in autumn: a soft layer of moss in
        # round cushions, and on it the fallen leaves of chestnut and beech
        # in rust, gold and brown. A leaf is long and pointed, with a dark
        # rib. A few brown chestnuts lie among them.
        lower = s + 4.4 + tile.profile(8, 3)[None, :] * 3.0
        body = np.clip((lower - y) * K * 0.5 + 0.5, 0, 1) * (y >= s - 0.3)
        tile.put(np.clip((lower + 2.5 - y) / 2.5, 0, 1) * (y >= s), (0, 0, 0), 0.32)
        tile.put(body, _mix(skin.cap_colour, skin.dark, 0.30))
        tile.tone((tile.noise(16, 5, 2) - 0.5) * 0.26 * body)
        tile.put(body * np.clip((y - (lower - 2.0)) / 2.0, 0, 1), skin.dark, 0.5)
        lumps = [(rng.uniform(0, 64), s + rng.uniform(-0.2, 0.7), rng.uniform(1.2, 2.6)) for _ in range(22)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r, ry=r * 0.6) for x, yy, r in lumps]), skin.cap_colour)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - r * 0.2, yy - r * 0.3, r * 0.5, ry=r * 0.22) for x, yy, r in lumps]), _mix(skin.cap_colour, (240, 240, 180), 0.35), 0.7)
        colours = (skin.accent, (214, 160, 60), (140, 84, 44), (176, 152, 64))
        leaves = []
        for _ in range(26):
            x = rng.uniform(0, 64)
            yy = s + rng.uniform(-0.6, 1.8)
            a = rng.uniform(-0.5, 0.5)
            half = rng.uniform(1.4, 2.4)
            leaves.append((x, yy, a, half, rng.randrange(len(colours))))

        def leaf(p, dx, dy, x, yy, a, half):
            ca, sa = math.cos(a), math.sin(a)
            pts = [(-half, 0.0), (-half * 0.3, -half * 0.32), (half, 0.0), (-half * 0.3, half * 0.32)]
            _poly(p, dx, dy, [(x + u * ca - v * sa, yy + u * sa + v * ca) for u, v in pts])

        for index, colour in enumerate(colours):
            tile.put(tile.mask(lambda p, dx, dy: [leaf(p, dx, dy, x, yy, a, h) for x, yy, a, h, k in leaves if k == index]), colour)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x - h * math.cos(a), yy - h * math.sin(a)), (x + h * math.cos(a), yy + h * math.sin(a))], 0.18) for x, yy, a, h, k in leaves]), skin.dark, 0.45)
        nuts = [(rng.uniform(0, 64), s + rng.uniform(-0.2, 0.6)) for _ in range(3)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 1.0, ry=0.85) for x, yy in nuts]), (96, 54, 30))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.3, yy - 0.35, 0.4, ry=0.25) for x, yy in nuts]), (230, 190, 140), 0.6)
        return tile.publish()
    if skin.cap in ("moss_catkin", "moss_maple"):
        # The moss of a garden, kept and not trodden: a soft, even cushion
        # over the edge with round lumps on its top and a fine texture, and
        # small clumps that hang a little over the edge. At Hangzhou the
        # white fluff of willow catkins lies on it; at Heian-kyo red leaves
        # of maple.
        lower = s + 3.6 + tile.profile(10, 3)[None, :] * 2.4
        top = s - (tile.profile(16, 2)[None, :] - 0.5) * 0.8
        body = np.clip((lower - y) * K * 0.5 + 0.5, 0, 1) * np.clip((y - top) * K * 0.5 + 0.5, 0, 1)
        tile.put(np.clip((lower + 2.5 - y) / 2.5, 0, 1) * (y >= top), (0, 0, 0), 0.32)
        tile.put(body, _mix(skin.cap_colour, skin.dark, 0.18))
        tile.tone((tile.noise(24, 6, 2) - 0.5) * 0.34 * body)
        tile.put(body * np.clip((y - (lower - 1.8)) / 1.8, 0, 1), skin.dark, 0.45)
        lumps = [(rng.uniform(0, 64), s + rng.uniform(-0.2, 0.5), rng.uniform(1.4, 2.8)) for _ in range(26)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r, ry=r * 0.5) for x, yy, r in lumps]), skin.cap_colour)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - r * 0.2, yy - r * 0.22, r * 0.55, ry=r * 0.2) for x, yy, r in lumps]), _mix(skin.cap_colour, (240, 246, 190), 0.40), 0.75)
        fuzz = [(rng.uniform(0, 64), s + rng.uniform(-0.4, 2.6)) for _ in range(90)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 0.22) for x, yy in fuzz]) * body, _mix(skin.cap_colour, (230, 240, 170), 0.45), 0.6)
        if skin.cap == "moss_catkin":
            # The catkins: small soft white tufts, each with a few fine hairs.
            tufts = [(rng.uniform(0, 64), s + rng.uniform(-0.6, 0.8), rng.uniform(0.5, 0.9)) for _ in range(9)]
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r * 1.5, ry=r) for x, yy, r in tufts], blur=0.25), (246, 244, 234), 0.85)
            tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, yy), (x + math.cos(a) * 1.5, yy - abs(math.sin(a)) * 1.1)], 0.12) for x, yy, r in tufts for a in (0.5, 1.6, 2.6)]), (250, 250, 244), 0.7)
        else:
            # The maple leaves: small red stars of seven points, flat on
            # the moss, each turned its own way.
            leaves = [(rng.uniform(0, 64), s + rng.uniform(-0.3, 1.0), rng.uniform(1.0, 1.5), rng.uniform(0, math.pi), k % 3) for k in range(10)]
            colours = (skin.accent, _mix(skin.accent, (236, 120, 40), 0.5), _mix(skin.accent, (90, 20, 20), 0.35))

            def star(p, dx, dy, x, yy, r, turn):
                pts = []
                for k in range(14):
                    a = turn + k * math.pi / 7.0
                    rr = r if k % 2 == 0 else r * 0.4
                    pts.append((x + math.cos(a) * rr, yy + math.sin(a) * rr * 0.6))
                _poly(p, dx, dy, pts)

            for index, colour in enumerate(colours):
                tile.put(tile.mask(lambda p, dx, dy: [star(p, dx, dy, x, yy, r, t) for x, yy, r, t, k in leaves if k == index]), colour)
        return tile.publish()
    if skin.cap == "trimmed_grass":
        # Grass of a palace court, cut short and even: a dense top of short
        # blades all of near one height, a clean cut edge, the dark soil of
        # the sod under the grass, and a few small leaves of clover.
        lower = s + 4.2 + tile.profile(12, 2)[None, :] * 0.8
        body = np.clip((lower - y) * K * 0.5 + 0.5, 0, 1) * (y >= s - 0.2)
        tile.put(np.clip((lower + 2.5 - y) / 2.5, 0, 1) * (y >= s), (0, 0, 0), 0.32)
        tile.put(body, skin.cap_colour)
        tile.tone((tile.noise(20, 4, 2) - 0.5) * 0.20 * body)
        soil = body * np.clip((y - s - 2.2) / 0.6, 0, 1)
        tile.put(soil, (78, 60, 42))
        tile.put(soil * np.clip((y - (lower - 0.8)) / 0.8, 0, 1), skin.dark, 0.5)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, s + 2.4), (x + 0.3, s + 3.6)], 0.18) for x in np.arange(0.5, 64.0, 1.6)]) * soil, (130, 106, 70), 0.45)
        blades = []
        for k in range(220):
            x = k * 64.0 / 220.0 + rng.uniform(-0.2, 0.2)
            h = rng.uniform(1.0, 1.5)
            lean = rng.uniform(-0.25, 0.25)
            blades.append([(x - 0.22, s + 1.0), (x + 0.22, s + 1.0), (x + lean, s - h)])
        for shade, part in ((-0.12, blades[1::3]), (0.0, blades[::3]), (0.25, blades[2::3])):
            colour = _mix(skin.cap_colour, (240, 240, 160), shade) if shade >= 0 else _mix(skin.cap_colour, skin.dark, -shade)
            tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, pts) for pts in part]), colour)
        tile.put(((y >= s - 1.5) & (y < s - 0.9)).astype(np.float32) * np.clip(tile.noise(32, 1, 2) * 1.6 - 0.3, 0, 1), _mix(skin.cap_colour, (250, 250, 200), 0.5), 0.55)
        clover = [(rng.uniform(0, 64), s + rng.uniform(0.2, 1.2)) for _ in range(5)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x + ox, yy + oy, 0.45) for x, yy in clover for ox, oy in ((-0.45, 0.0), (0.45, 0.0), (0.0, -0.45))]), _mix(skin.cap_colour, (40, 90, 40), 0.35))
        return tile.publish()
    if skin.cap == "delta_grass":
        # The edge of a bank of the delta in the rains: a lip of wet silt
        # that shines a little, and on it thick grass, short and long, the
        # long blades bent over by their weight, with a few small pools of
        # water among their feet.
        lower = s + 3.2 + tile.profile(10, 3)[None, :] * 2.4
        body = np.clip((lower - y) * K * 0.5 + 0.5, 0, 1) * (y >= s - 0.3)
        tile.put(np.clip((lower + 2.5 - y) / 2.5, 0, 1) * (y >= s), (0, 0, 0), 0.32)
        tile.put(body, _mix(skin.base, skin.dark, 0.25))
        tile.tone((tile.noise(16, 4, 2) - 0.5) * 0.25 * body)
        tile.put(body * np.clip(1.0 - np.abs(y - s - 1.4) / 0.5, 0, 1), _mix(skin.light, (230, 236, 230), 0.4), 0.35)
        pools = [(rng.uniform(0, 64), s + rng.uniform(0.6, 1.4), rng.uniform(1.0, 2.2)) for _ in range(4)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r, ry=0.35) for x, yy, r in pools]), (190, 200, 196), 0.55)
        blades = []
        for _ in range(130):
            x = rng.uniform(0, 64)
            h = rng.uniform(1.0, 2.4) if rng.random() < 0.8 else rng.uniform(2.6, 3.6)
            lean = rng.uniform(-1.2, 1.2)
            blades.append([(x - 0.4, s + 0.9), (x + 0.4, s + 0.9), (x + lean, s - h)])
        for shade, part in ((-0.25, blades[0::3]), (0.0, blades[1::3]), (0.30, blades[2::3])):
            colour = _mix(skin.cap_colour, (232, 240, 160), shade) if shade >= 0 else _mix(skin.cap_colour, skin.dark, -shade)
            tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, pts) for pts in part]), colour)
        bent = []
        for _ in range(12):
            x = rng.uniform(0, 64)
            side = rng.choice([-1.0, 1.0])
            bent.append([(x, s + 0.6), (x + side * 0.5, s - 2.2), (x + side * 1.4, s - 3.0), (x + side * 2.2, s - 2.9)])
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.32) for pts in bent]), _mix(skin.cap_colour, (220, 232, 150), 0.18))
        return tile.publish()
    if skin.cap == "rope_beam":
        # A beam of tarred timber on the edge of the quay, a rope lashed
        # round it each sixteen units, wet on its top.
        thick = 5.4
        body = ((y >= s - 0.3) & (y < s + thick)).astype(np.float32)
        tile.put(body, skin.cap_colour)
        tile.tone(((np.sin(tile.x * 0.9 + np.sin(tile.x * 0.1) * 3.0) * 0.5) * 0.10 + (tile.noise(10, 2, 2) - 0.5) * 0.16) * body)
        tile.put(((y >= s - 0.3) & (y < s + 0.7)).astype(np.float32), _mix(skin.cap_colour, (230, 236, 230), 0.45))
        tile.put(((y >= s + thick - 0.9) & (y < s + thick)).astype(np.float32), skin.dark, 0.7)
        rope = (184, 156, 108)
        for k in range(4):
            x0 = k * 16.0 + 6.0
            turns = tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x0 + j * 1.1, s - 0.5), (x0 + j * 1.1 + 1.0, s + thick + 0.3)], 0.75) for j in range(4)])
            tile.put(turns, _mix(rope, skin.dark, 0.35))
            tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x0 + j * 1.1 - 0.15, s - 0.4), (x0 + j * 1.1 + 0.85, s + thick + 0.2)], 0.3) for j in range(4)]), rope, 0.9)
        tile.put(np.clip(1.0 - (y - s - thick) / 3.0, 0.0, 1.0) * (y >= s + thick), (0, 0, 0), 0.36)
        return tile.publish()
    if skin.cap == "iron":
        # An edge of iron: a band with a row of rivets, the joints of its
        # plates, a top worn bright by feet, and rust in a few places.
        thick = 4.6
        body = ((y >= s - 0.3) & (y < s + thick)).astype(np.float32)
        tile.put(body, skin.cap_colour)
        tile.tone(((tile.noise(10, 2, 2) - 0.5) * 0.18) * body)
        tile.put(((y >= s - 0.3) & (y < s + 0.6)).astype(np.float32), (176, 178, 184), 0.8)
        rust = np.clip((tile.noise(8, 2, 3) - 0.6) * 5.0, 0.0, 1.0) * body * (y > s + 0.8)
        tile.put(rust, (130, 70, 40), 0.55)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32.0 - 0.25, s, k * 32.0 + 0.25, s + thick) for k in range(3)]), skin.dark, 0.8)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 6.4 + 3.2, s + 2.5, 0.6) for k in range(10)]), _mix(skin.cap_colour, (220, 220, 226), 0.5))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 6.4 + 3.4, s + 2.8, 0.6) for k in range(10)]), skin.dark, 0.35)
        tile.put(((y >= s + thick - 0.7) & (y < s + thick)).astype(np.float32), skin.dark, 0.75)
        tile.put(np.clip(1.0 - (y - s - thick) / 3.0, 0.0, 1.0) * (y >= s + thick), (0, 0, 0), 0.40)
        return tile.publish()
    if skin.cap == "moulding":
        # A moulding of andesite, carved as on the terraces of Borobudur: a
        # flat top, a round torus under it, a dark groove, and a band of
        # small lotus petals side by side. A joint is each twenty-one
        # units, and moss grows on the top here and there.
        thick = 6.6
        stone = skin.cap_colour
        body = ((y >= s - 0.3) & (y < s + thick)).astype(np.float32)
        tile.put(body, stone)
        tile.tone(((tile.noise(12, 2, 2) - 0.5) * 0.16) * body)
        tile.put(((y >= s - 0.3) & (y < s + 0.9)).astype(np.float32), _mix(stone, (255, 250, 236), 0.45))
        torus = ((y >= s + 0.9) & (y < s + 3.2)).astype(np.float32)
        tile.put(torus * np.clip(1.0 - np.abs(y - s - 1.6) / 0.8, 0, 1), _mix(stone, (255, 250, 236), 0.35), 0.8)
        tile.put(torus * np.clip((y - s - 2.0) / 1.2, 0, 1), skin.dark, 0.45)
        tile.put(((y >= s + 3.2) & (y < s + 3.8)).astype(np.float32), skin.dark, 0.75)
        petals = [k * 64.0 / 24.0 + 64.0 / 48.0 for k in range(24)]
        shape = tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(x - 1.1, s + thick - 0.5), (x - 1.0, s + 5.0), (x, s + 3.9), (x + 1.0, s + 5.0), (x + 1.1, s + thick - 0.5)]) for x in petals])
        tile.put(shape, _mix(stone, (255, 250, 236), 0.15))
        tile.put(shape * np.clip(1.0 - (tile.x % (64.0 / 24.0)) / 1.2, 0, 1), (255, 250, 236), 0.25)
        tile.put(((y >= s + 3.8) & (y < s + thick)).astype(np.float32) * (1.0 - shape), skin.dark, 0.55)
        tile.put(((y >= s + thick - 0.6) & (y < s + thick)).astype(np.float32), skin.dark, 0.7)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 64.0 / 3.0 + 5.0 - 0.25, s, k * 64.0 / 3.0 + 5.0 + 0.25, s + thick) for k in range(3)]), skin.dark, 0.8)
        moss = [(rng.uniform(0, 64), rng.uniform(1.4, 3.2)) for _ in range(4)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, s - 0.1, w, ry=0.8) for x, w in moss]), skin.accent, 0.9)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.3, s - 0.4, w * 0.6, ry=0.4) for x, w in moss]), _mix(skin.accent, (230, 240, 170), 0.4), 0.8)
        tile.put(np.clip(1.0 - (y - s - thick) / 3.0, 0.0, 1.0) * (y >= s + thick), (0, 0, 0), 0.38)
        return tile.publish()
    if skin.cap == "sandstone_coping":
        # A coping of grey-pink sandstone over the laterite, as the Khmer
        # faced their laterite cores with sandstone. A flat top worn by
        # feet, a band with a row of small carved rosettes of four petals,
        # and a moulding under it. A joint is each thirty-two units; dark
        # lichen grows on it in spots.
        thick = 7.0
        stone = skin.cap_colour
        body = ((y >= s - 0.3) & (y < s + thick)).astype(np.float32)
        tile.put(body, stone)
        tile.tone(((tile.noise(10, 2, 3) - 0.5) * 0.18) * body)
        tile.put(((y >= s - 0.3) & (y < s + 0.9)).astype(np.float32), _mix(stone, (255, 246, 236), 0.45))
        tile.put(((y >= s + 1.4) & (y < s + 1.9)).astype(np.float32), skin.dark, 0.45)
        tile.put(((y >= s + 4.9) & (y < s + 5.4)).astype(np.float32), skin.dark, 0.45)
        centres = [k * 4.0 + 2.0 for k in range(16)]
        rosettes = tile.mask(lambda p, dx, dy: [[_dot(p, dx, dy, x + ox, s + 3.4 + oy, 0.55) for ox, oy in ((-0.7, 0.0), (0.7, 0.0), (0.0, -0.7), (0.0, 0.7))] for x in centres])
        tile.put(rosettes, _mix(stone, skin.dark, 0.40))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, s + 3.4, 0.35) for x in centres]), _mix(stone, (255, 246, 236), 0.4))
        tile.put(((y >= s + 5.4) & (y < s + thick)).astype(np.float32) * np.clip(1.0 - (y - s - 5.4) / 1.6, 0, 1), _mix(stone, (255, 246, 236), 0.2), 0.6)
        tile.put(((y >= s + thick - 0.6) & (y < s + thick)).astype(np.float32), skin.dark, 0.7)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32.0 + 13.0 - 0.25, s, k * 32.0 + 13.0 + 0.25, s + thick) for k in range(2)]), skin.dark, 0.8)
        tile.put(body * np.clip((tile.noise(14, 3, 2) - 0.68) * 6.0, 0.0, 1.0), (70, 66, 60), 0.35)
        tile.put(np.clip(1.0 - (y - s - thick) / 3.0, 0.0, 1.0) * (y >= s + thick), (0, 0, 0), 0.40)
        return tile.publish()
    if skin.cap in ("strip", "plate", "edge"):
        thick = {"strip": 5.5, "plate": 5.0, "edge": 4.2}[skin.cap]
        body = ((y >= s) & (y < s + thick)).astype(np.float32)
        tile.put(body, skin.cap_colour)
        tile.put(((y >= s) & (y < s + 0.7)).astype(np.float32), _mix(skin.cap_colour, (255, 255, 255), 0.45))
        tile.put(((y >= s + thick - 0.8) & (y < s + thick)).astype(np.float32), skin.dark, 0.7)
        # The shade the cap throws on the block under it.
        tile.put(np.clip(1.0 - (y - s - thick) / 3.5, 0.0, 1.0) * (y >= s + thick), (0, 0, 0), 0.42)
        if skin.cap == "strip":
            tile.put(((y >= s + 1.7) & (y < s + 2.9)).astype(np.float32) * tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 16 + 1.5, 0, k * 16 + 14.5, 20) for k in range(4)]), skin.accent)
            tile.put(np.clip(1.0 - np.abs(y - s - 2.3) / 2.6, 0, 1) ** 2, skin.accent, 0.22)
            tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 16 - 0.4, s, k * 16 + 0.4, s + thick) for k in range(5)]), skin.dark, 0.7)
        elif skin.cap == "plate":
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 8 + 4, s + 2.6, 0.75) for k in range(8)]), _mix(skin.cap_colour, (255, 255, 255), 0.35))
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 8 + 4.2, s + 2.9, 0.75) for k in range(8)]), skin.dark, 0.35)
            tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32 - 0.3, s, k * 32 + 0.3, s + thick) for k in range(3)]), skin.dark, 0.8)
            # Heat in the joints of the stone under the plate.
            seams = []
            for _ in range(3):
                x, yy = rng.uniform(0, 64), s + thick + rng.uniform(0.3, 1.0)
                pts = [(x, yy)]
                for _ in range(5):
                    x, yy = x + rng.uniform(-1.6, 1.6), yy + rng.uniform(0.8, 1.9)
                    pts.append((x, yy))
                seams.append(pts)
            glow = tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.3) for pts in seams])
            fade = np.clip(1.0 - (y - s - thick) / 9.0, 0.0, 1.0)
            tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.4) for pts in seams], blur=0.9) * fade, skin.accent, 0.45)
            tile.put(glow * fade, _mix(skin.accent, (255, 255, 220), 0.3), 0.7)
        else:
            tile.put(((y >= s) & (y < s + 0.9)).astype(np.float32), skin.accent)
            tile.put(np.clip(1.0 - np.abs(y - s - 0.4) / 3.0, 0, 1) ** 2, skin.accent, 0.30)
            signs = tile.mask(lambda p, dx, dy: [(_box(p, dx, dy, k * 8 + 2.5, s + 2.0, k * 8 + 5.5, s + 2.5) if k % 3 else _dot(p, dx, dy, k * 8 + 4, s + 2.4, 0.7)) for k in range(8)])
            tile.put(signs, skin.accent, 0.7)
    else:
        # Soft ground: a body that the surface cuts, with an uneven lower edge.
        depth = {"grass": (5.0, 6.0), "moss": (4.0, 9.0), "sand": (3.5, 2.5), "frosting": (5.0, 0.0), "sauce": (5.0, 0.0), "paint": (5.0, 0.0), "ink": (5.0, 0.0), "turf": (6.5, 3.5), "plaster": (4.4, 1.6), "snow": (5.5, 4.0), "flowstone": (4.0, 0.0), "foam": (4.0, 3.0)}[skin.cap]
        lower = s + depth[0] + tile.profile(8, 3)[None, :] * depth[1]
        if skin.cap == "frosting":
            # Icing that runs down in round drips, eight to the tile.
            lower = s + 4.2 + 4.6 * np.abs(np.sin(tile.x * math.pi / 8.0)) ** 0.7 * (0.55 + 0.45 * np.cos(tile.x * math.pi / 16.0) ** 2)
        elif skin.cap == "flowstone":
            # Calcite that ran over the edge and set in round folds, like a
            # curtain: eight folds to the tile.
            lower = s + 3.2 + 3.4 * (0.5 + 0.5 * np.cos(tile.x * math.pi / 4.0)) ** 2 * (0.6 + 0.4 * np.cos(tile.x * math.pi / 32.0 + 1.0) ** 2)
        elif skin.cap == "sauce":
            # Sauce that runs down the edge: drips of three lengths, four of
            # the long ones to the tile.
            # A drip is a round end: half an ellipse under the body of the sauce.
            lower = np.full_like(tile.x, s + 3.0)
            for k, (length, half) in enumerate(((7.4, 2.5), (2.8, 3.4), (5.2, 2.2), (2.2, 3.0), (6.4, 2.4), (3.4, 3.6), (4.6, 2.0), (2.6, 3.2))):
                dx_ = (tile.x - (k * 8.0 + 4.0) + 32.0) % 64.0 - 32.0
                lower = np.maximum(lower, s + 3.0 + length * np.sqrt(np.clip(1.0 - (dx_ / half) ** 2, 0.0, 1.0)))
        elif skin.cap in ("paint", "ink"):
            # A thick coat that runs over the edge in drips of each length,
            # each with a round end.
            lower = np.full_like(tile.x, s + 3.2)
            for k, (length, half) in enumerate(((8.4, 2.2), (3.0, 3.2), (5.6, 1.8), (1.8, 2.8), (9.2, 2.0), (2.6, 3.4), (6.2, 1.9), (3.4, 2.6))):
                dx_ = (tile.x - (k * 8.0 + 3.0 + (k % 3)) + 32.0) % 64.0 - 32.0
                lower = np.maximum(lower, s + 3.2 + length * np.sqrt(np.clip(1.0 - (dx_ / half) ** 2, 0.0, 1.0)))
        top = s - (tile.profile(16, 2)[None, :] - 0.5) * (1.0 if skin.cap != "sand" else 0.6)
        body = np.clip((lower - y) * K * 0.5 + 0.5, 0, 1) * np.clip((y - top) * K * 0.5 + 0.5, 0, 1)
        tile.put(np.clip((lower + 2.5 - y) / 2.5, 0, 1) * (y >= top), (0, 0, 0), 0.34)
        tile.put(body, skin.cap_colour)
        tile.tone((tile.noise(16, 5, 2) - 0.5) * 0.30 * (tile.alpha > 0))
        tile.put(body * np.clip((y - (lower - 2.2)) / 2.2, 0, 1), skin.dark, 0.5)
        tile.put(body * np.clip(1.0 - (y - top) / 1.2, 0, 1), _mix(skin.cap_colour, (255, 255, 235), 0.42), 0.8)
        if skin.cap == "paint":
            # The coat is in bands of the three primaries, side by side, with
            # a soft join where two run together; a line of shine on top.
            bands = ((0.0, skin.cap_colour), (22.0, skin.accent), (38.0, (40, 200, 236)), (56.0, skin.cap_colour))
            for (x0, colour), (x1, _next) in zip(bands, bands[1:]):
                part = np.clip((tile.x - x0 + 1.0) / 2.0, 0, 1) * np.clip((x1 + 1.0 - tile.x) / 2.0, 0, 1)
                tile.put(body * part, colour)
            tile.put(body * np.clip((y - (lower - 2.0)) / 2.0, 0, 1), skin.dark, 0.35)
            tile.put(body * np.clip(1.0 - np.abs(y - s - 1.2) / 0.6, 0, 1), (255, 255, 255), 0.55)
        elif skin.cap == "ink":
            # Living ink: it glows at its ends, and a light line runs on it.
            tile.put(body * np.clip((y - s - 3.0) / 6.0, 0, 1), skin.accent, 0.45)
            tile.put(body * np.clip(1.0 - np.abs(y - s - 1.2) / 0.6, 0, 1), (255, 220, 250), 0.6)
        elif skin.cap == "sauce":
            # The shine of the sauce, grated cheese on it and bits of basil.
            tile.put(body * np.clip(1.0 - np.abs(y - s - 1.4) / 0.6, 0, 1), _mix(skin.cap_colour, (255, 236, 210), 0.6), 0.5)
            cheese = [(rng.uniform(0, 64), s + rng.uniform(0.4, 3.2), rng.uniform(0, 3.14)) for _ in range(34)]
            tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x - 0.6 * math.cos(a), yy - 0.3 * math.sin(a)), (x + 0.6 * math.cos(a), yy + 0.3 * math.sin(a))], 0.34) for x, yy, a in cheese]), (250, 236, 190), 0.9)
            basil = [(rng.uniform(0, 64), s + rng.uniform(0.8, 3.4), rng.uniform(0.5, 0.9)) for _ in range(9)]
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r, ry=r * 0.55) for x, yy, r in basil]), (64, 128, 62))
        elif skin.cap == "frosting":
            # A line of light along the top of the icing, and sprinkles on it.
            tile.put(body * np.clip(1.0 - np.abs(y - s - 1.5) / 0.7, 0, 1), (255, 255, 255), 0.55)
            sprinkles = [(rng.uniform(0, 64), s + rng.uniform(2.0, 4.6), rng.uniform(0, 3.14), k % 3) for k in range(18)]
            for kind, colour in enumerate((skin.accent, skin.base, (170, 200, 255))):
                tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x - 0.7 * math.cos(a), yy - 0.7 * math.sin(a)), (x + 0.7 * math.cos(a), yy + 0.7 * math.sin(a))], 0.45) for x, yy, a, kk in sprinkles if kk == kind]), colour)
        elif skin.cap == "grass":
            blades = []
            for _ in range(70):
                x = rng.uniform(0, 64)
                h = rng.uniform(1.6, 3.8)
                lean = rng.uniform(-1.0, 1.0)
                blades.append([(x - 0.45, s + 0.8), (x + 0.45, s + 0.8), (x + lean, s - h)])
            for shade, part in ((0.0, blades[::2]), (0.28, blades[1::2])):
                tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, pts) for pts in part]), _mix(skin.cap_colour, (255, 255, 200), shade))
            flowers = [(rng.uniform(0, 64), s - rng.uniform(0.6, 2.2)) for _ in range(5)]
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 0.55) for x, yy in flowers]), skin.accent)
        elif skin.cap == "turf":
            # A thick sod: short grass dense on its top, the roots of the
            # grass in it, and tufts that stand higher here and there.
            tile.put(body * np.clip((y - s - 1.6) / 4.0, 0, 1), (60, 46, 30), 0.55)
            roots = [(rng.uniform(0, 64), s + rng.uniform(2.0, 5.0), rng.uniform(-0.8, 0.8), rng.uniform(1.0, 2.6)) for _ in range(30)]
            tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, yy), (x + ox, yy + oy)], 0.25) for x, yy, ox, oy in roots]) * body, (120, 100, 66), 0.6)
            blades = []
            for _ in range(120):
                x = rng.uniform(0, 64)
                h = rng.uniform(0.8, 2.2) if rng.random() < 0.85 else rng.uniform(2.6, 4.0)
                lean = rng.uniform(-0.8, 0.8)
                blades.append([(x - 0.35, s + 0.9), (x + 0.35, s + 0.9), (x + lean, s - h)])
            for shade, part in ((0.0, blades[::2]), (0.25, blades[1::2])):
                tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, pts) for pts in part]), _mix(skin.cap_colour, (240, 236, 150), shade))
            flowers = [(rng.uniform(0, 64), s - rng.uniform(0.6, 1.8)) for _ in range(4)]
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 0.5) for x, yy in flowers]), (236, 220, 120))
        elif skin.cap == "plaster":
            # Plaster with lime in it, smooth and round on its edge as a
            # hand smoothed it, a few cracks, and the shine of the sun on top.
            tile.put(body * np.clip(1.0 - np.abs(y - s - 1.0) / 0.8, 0, 1), (255, 252, 240), 0.45)
            cracks = [(rng.uniform(0, 64), s + rng.uniform(1.0, 2.5)) for _ in range(5)]
            tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, yy), (x + 0.6, yy + 1.0), (x + 0.2, yy + 2.0)], 0.2) for x, yy in cracks]) * body, skin.dark, 0.4)
        elif skin.cap == "snow":
            # Snow: round lumps on its top, blue shade in its lower part, and
            # small points of light where the sun catches the crystals.
            tile.put(body * np.clip((y - s - 1.2) / 4.0, 0, 1), _mix(skin.base, skin.cap_colour, 0.45), 0.7)
            lumps = [(rng.uniform(0, 64), s + rng.uniform(0.2, 0.8), rng.uniform(1.6, 3.6)) for _ in range(16)]
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r, ry=r * 0.45) for x, yy, r in lumps]), skin.cap_colour)
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - r * 0.2, yy - r * 0.25, r * 0.6, ry=r * 0.18) for x, yy, r in lumps]), (255, 255, 255), 0.6)
            sparks = [(rng.uniform(0, 64), s + rng.uniform(-0.4, 3.0)) for _ in range(14)]
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 0.28) for x, yy in sparks]), (255, 255, 255), 0.9)
        elif skin.cap == "foam":
            # The sea that washes over the gunwale: white foam in lumps on
            # its top, blue water under it that shows the wood through, and
            # bubbles.
            tile.put(body * np.clip((y - s - 1.4) / 3.0, 0, 1), (80, 150, 170), 0.45)
            lumps = [(rng.uniform(0, 64), s + rng.uniform(-0.2, 0.9), rng.uniform(1.0, 2.6)) for _ in range(20)]
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r, ry=r * 0.5) for x, yy, r in lumps]), skin.cap_colour)
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - r * 0.2, yy - r * 0.2, r * 0.5, ry=r * 0.18) for x, yy, r in lumps]), (255, 255, 255), 0.7)
            bubbles = [(rng.uniform(0, 64), s + rng.uniform(1.2, 4.6), rng.uniform(0.25, 0.55)) for _ in range(24)]
            tile.put(tile.mask(lambda p, dx, dy: [p.ellipse([(x - r) * K + dx, (yy - r) * K + dy, (x + r) * K + dx, (yy + r) * K + dy], outline=255, width=max(1, int(0.18 * K))) for x, yy, r in bubbles]) * body, (240, 250, 255), 0.8)
        elif skin.cap == "flowstone":
            # Thin bands of calcite along the folds, and a wet shine on each
            # fold.
            tile.put(np.clip(1.0 - np.abs(((y - s) % 1.6) - 0.8) / 0.25, 0, 1) * body, skin.light, 0.22)
            tile.put(body * np.clip(1.0 - np.abs(tile.x % 8.0 - 4.0) / 1.2, 0, 1) * np.clip((y - s - 1.5) / 3.0, 0, 1), (255, 250, 236), 0.30)
        elif skin.cap == "moss":
            lumps = [(rng.uniform(0, 64), s + rng.uniform(-0.3, 0.6), rng.uniform(1.2, 2.6)) for _ in range(22)]
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r, ry=r * 0.6) for x, yy, r in lumps]), _mix(skin.cap_colour, (255, 255, 235), 0.2))
            lights = [(rng.uniform(0, 64), s + rng.uniform(1.5, 5.0)) for _ in range(7)]
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 1.3) for x, yy in lights], blur=0.5), skin.accent, 0.45)
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 0.42) for x, yy in lights]), _mix(skin.accent, (255, 255, 255), 0.4))
        else:
            pebbles = [(rng.uniform(0, 64), s + rng.uniform(1.0, 3.0), rng.uniform(0.35, 0.8)) for _ in range(12)]
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r, ry=r * 0.7) for x, yy, r in pebbles]), skin.dark, 0.45)
            tufts = []
            for _ in range(4):
                x = rng.uniform(0, 64)
                for k in range(4):
                    tufts.append([(x + k * 0.5 - 0.3, s + 0.6), (x + k * 0.5 + 0.3, s + 0.6), (x + k * 0.9 - 1.2, s - rng.uniform(1.5, 3.2))])
            tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, pts) for pts in tufts]), (96, 140, 110))
    return tile.publish()


# ---------------------------------------------------------------------------
# Undersides
# ---------------------------------------------------------------------------


def under(skin: Skin) -> Image.Image:
    tile = Tile(UNDER, True, False, skin.key, "under")
    rng = tile.rng
    e = UNDER_EDGE
    y = tile.y
    # The lower lip of the block is in shade.
    tile.put(np.clip(1.0 - (e - y) / e, 0.0, 1.0) * (y < e), (0, 0, 0), 0.5)
    rock, rock_light = skin.dark, _mix(skin.base, skin.light, 0.3)
    if skin.under == "pipes":
        tile.put(((y >= e + 0.8) & (y < e + 4.4)).astype(np.float32), _mix(skin.base, skin.dark, 0.3))
        tile.put(((y >= e + 1.1) & (y < e + 1.8)).astype(np.float32), skin.light, 0.7)
        tile.put(((y >= e + 3.6) & (y < e + 4.4)).astype(np.float32), skin.dark, 0.7)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 16 + 2, e - 0.5, k * 16 + 4.2, e + 5.2) for k in range(4)]), _mix(skin.base, skin.light, 0.25))
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, 40, e + 4.4, 41.5, e + 7.5), _dot(p, dx, dy, 40.75, e + 8.2, 1.1)]), _mix(skin.base, skin.dark, 0.2))
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, 40.75, e + 8.2, 0.45)), skin.accent)
    elif skin.under in ("stalactites", "spikes"):
        teeth = []
        x = 0.0
        while x < 64.0:
            w = 4.0 if skin.under == "spikes" else rng.uniform(2.6, 7.0)
            h = rng.uniform(4.5, 6.5) if skin.under == "spikes" else rng.uniform(2.5, 11.0)
            teeth.append((x, min(w, 64.0 - x) if 64.0 - x < 2.6 else w, h))
            x += w
        tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(x0, e - 0.6), (x0 + w, e - 0.6), (x0 + w * 0.55, e + h)]) for x0, w, h in teeth]), rock)
        tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(x0, e - 0.6), (x0 + w * 0.32, e - 0.6), (x0 + w * 0.55, e + h)]) for x0, w, h in teeth]), rock_light, 0.75)
        if skin.under == "stalactites":
            drops = [(x0 + w * 0.55, e + h + 0.5) for x0, w, h in teeth if h > 8.0]
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 0.45) for x, yy in drops]), skin.accent, 0.9)
    elif skin.under in ("roots", "weed"):
        weed = skin.under == "weed"
        colour = (34, 112, 92) if weed else _mix(skin.light, (120, 96, 70), 0.5)
        leaf = (70, 160, 120) if weed else _mix(skin.cap_colour, (255, 255, 220), 0.1)
        strands, leaves = [], []
        for _ in range(9):
            x = rng.uniform(0, 64)
            length = rng.uniform(4.0, 11.0)
            phase = rng.uniform(0, 6.28)
            pts = [(x + math.sin(phase + t * 0.5) * 0.9 * (t / 10.0), e - 0.8 + length * t / 10.0) for t in range(11)]
            strands.append((pts, rng.uniform(0.45, 0.8) if weed else rng.uniform(0.3, 0.6)))
            if weed:
                leaves.extend((px + (1.0 if k % 2 else -1.0), py, 1 if k % 2 else -1) for k, (px, py) in enumerate(pts[2::2]))
            elif rng.random() < 0.35:
                leaves.append((pts[-1][0], pts[-1][1], 1))
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, w) for pts, w in strands]), colour)
        tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(x - s * 1.0, yy), (x + s * 0.9, yy - 0.5), (x + s * 0.9, yy + 0.5)]) for x, yy, s in leaves]), leaf)
    elif skin.under == "icicles":
        # Icicles that hang from the edge: thin and pointed, of each length,
        # light on one side, with a drop at the tip of a long one.
        ice, ice_light = _mix(skin.base, skin.light, 0.45), _mix(skin.light, (255, 255, 255), 0.5)
        teeth = []
        x = 0.0
        while x < 63.0:
            w = min(rng.uniform(1.4, 3.2), 64.0 - x)
            teeth.append((x, w, rng.uniform(1.5, 10.0) if rng.random() < 0.7 else rng.uniform(0.6, 1.4)))
            x += w + rng.uniform(0.0, 1.2)
        tile.put(((y >= e - 0.6) & (y < e + 0.8)).astype(np.float32), ice)
        tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(x0, e - 0.6), (x0 + w, e - 0.6), (x0 + w * 0.5, e + h)]) for x0, w, h in teeth]), ice)
        tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(x0 + w * 0.15, e), (x0 + w * 0.42, e), (x0 + w * 0.5, e + h * 0.9)]) for x0, w, h in teeth]), ice_light, 0.7)
        drops = [(x0 + w * 0.5, e + h + 0.6) for x0, w, h in teeth if h > 8.0]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 0.35) for x, yy in drops]), ice_light, 0.8)
    elif skin.under == "drips":
        # Drops of paint that hang under the block, each a run with a round
        # end, in the colour of the coat on top and the accent.
        drops = []
        for k in range(9):
            x = (k + rng.uniform(0.2, 0.8)) * 64.0 / 9.0
            drops.append((x, rng.uniform(1.5, 8.0), rng.uniform(0.55, 0.95), skin.cap_colour if k % 3 else skin.accent))
        for x, length, w, colour in drops:
            tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x - w, e - 0.6, x + w, e + length), _dot(p, dx, dy, x, e + length, w * 1.35))), colour)
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x - w * 0.6, e, x - w * 0.15, e + length)), (255, 255, 255), 0.35)
    elif skin.under == "ribbons":
        # Bookmarks that hang out of the books: ribbons of each length, each
        # with a notch cut in its end.
        for k in range(5):
            x = (k + rng.uniform(0.25, 0.75)) * 64.0 / 5.0
            length = rng.uniform(4.0, 10.0)
            w = rng.uniform(0.7, 1.0)
            colour = (skin.accent, (168, 40, 52), (60, 110, 160))[k % 3]
            ribbon = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x - w, e - 0.6), (x + w, e - 0.6), (x + w, e + length), (x, e + length - w * 1.2), (x - w, e + length)]))
            tile.put(ribbon, colour)
            tile.put(ribbon * (tile.x < x - w * 0.3), (255, 255, 255), 0.20)
    elif skin.under == "fringe":
        # A skirt of red velvet under the stage, in swags, with a gold fringe
        # on its lower edge.
        drop = e + 3.2 + 2.0 * np.abs(np.sin(tile.x * math.pi / 16.0))
        body = np.clip((drop - y) * K * 0.5 + 0.5, 0, 1) * (y >= e - 0.6)
        tile.put(body, (128, 22, 36))
        tile.put(body * (0.5 + 0.5 * np.cos(tile.x * math.pi / 2.0)) ** 2, (60, 6, 16), 0.45)
        fringe = (y >= drop - 0.2) & (y < drop + 1.4) & ((tile.x % 1.0) < 0.55)
        tile.put(fringe.astype(np.float32), skin.accent)
    elif skin.under == "noodles":
        # Noodles that hang under the block: many, of each length, and the
        # end of a long one turns up in a curl.
        strands = []
        for k in range(15):
            x = (k + rng.uniform(0.15, 0.85)) * 64.0 / 15.0
            length = rng.uniform(2.5, 11.0)
            phase = rng.uniform(0, 6.28)
            pts = [(x + math.sin(phase + t * 0.6) * 0.8 * (t / 10.0), e - 0.8 + length * t / 10.0) for t in range(11)]
            if length > 7.0:
                side = rng.choice([-1.0, 1.0])
                tx, ty = pts[-1]
                pts += [(tx + side * 0.9 * (1.0 - math.cos(a)), ty + 0.9 * math.sin(a) - 0.25 * a) for a in (0.6, 1.2, 1.8, 2.4, 3.0, 3.6)]
            strands.append((pts, rng.uniform(0.7, 1.0), rng.uniform(-0.18, 0.12)))
        for pts, w, tone in strands:
            colour = _mix(skin.light, (250, 226, 160), 0.35)
            colour = _mix(colour, skin.dark if tone < 0 else (255, 244, 200), abs(tone) * 1.6)
            tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x + 0.3, y) for x, y in pts], w)), skin.dark, 0.55)
            tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, pts, w)), colour)
    elif skin.under == "girder":
        # The bottom flange of a girder under a deck: a band of steel with a
        # row of rivets, and a stiffener each 16 units on the web over it.
        tile.put(((y >= e - 0.4) & (y < e + 3.0)).astype(np.float32), _mix(skin.cap_colour, skin.dark, 0.25))
        tile.put(((y >= e + 1.8) & (y < e + 3.0)).astype(np.float32), skin.cap_colour)
        tile.put(((y >= e + 1.8) & (y < e + 2.3)).astype(np.float32), _mix(skin.cap_colour, (255, 255, 255), 0.25))
        tile.put(((y >= e + 2.6) & (y < e + 3.0)).astype(np.float32), skin.dark, 0.8)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 16 + 7.4, e - 0.4, k * 16 + 8.6, e + 1.8) for k in range(4)]), _mix(skin.cap_colour, skin.light, 0.2))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 4 + 2, e + 2.4, 0.4) for k in range(16)]), skin.dark, 0.6)
    elif skin.under == "bolts":
        tile.put(((y >= e - 0.4) & (y < e + 2.6)).astype(np.float32), skin.cap_colour)
        tile.put(((y >= e - 0.4) & (y < e + 0.2)).astype(np.float32), _mix(skin.cap_colour, (255, 255, 255), 0.3))
        tile.put(((y >= e + 2.0) & (y < e + 2.6)).astype(np.float32), skin.dark, 0.8)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 8 + 4, e + 1.1, 0.7) for k in range(8)]), _mix(skin.cap_colour, (255, 255, 255), 0.3))
        hooks = [(10.0, 4.5), (41.0, 6.5)]
        tile.put(tile.mask(lambda p, dx, dy: [[_dot(p, dx, dy, x, e + 2.8 + k * 1.3, 0.45, ry=0.7) for k in range(int(h))] for x, h in hooks]), skin.cap_colour)
        tile.put(np.clip(1.0 - (y - e - 2.6) / 5.0, 0, 1) ** 2 * (y >= e + 2.6), skin.accent, 0.16)
    elif skin.under == "rim":
        # The white line on the bottom edge, and no shade. Nothing hangs from
        # it: a white point under a block reads as a spike.
        tile.alpha[:] = 0.0
        tile.put(((y >= e - 0.9) & (y < e + 0.4)).astype(np.float32), skin.cap_colour)
    else:  # lip
        tile.put(((y >= e - 0.3) & (y < e + 1.4)).astype(np.float32), _mix(skin.base, skin.dark, 0.5))
        tile.put(((y >= e + 0.9) & (y < e + 1.4)).astype(np.float32), skin.accent, 0.55)
        tile.put(np.clip(1.0 - (y - e - 1.4) / 4.0, 0, 1) ** 2 * (y >= e + 1.4), skin.accent, 0.16)
    return tile.publish()


def side(skin: Skin) -> Image.Image:
    tile = Tile(SIDE, False, True, skin.key, "side")
    x = tile.x
    if skin.material == "void":
        # The same crisp white line as the top edge, and no shade.
        tile.put((x < 1.2).astype(np.float32), skin.cap_colour)
        return tile.publish()
    tile.put(np.clip(1.0 - x / 9.0, 0.0, 1.0) ** 1.6, (0, 0, 0), 0.46)
    tile.put(((x >= 0.25) & (x < 0.85)).astype(np.float32), skin.light, 0.42)
    tile.put((x < 0.25).astype(np.float32), skin.dark, 0.8)
    return tile.publish()


# ---------------------------------------------------------------------------
# One-way platforms
# ---------------------------------------------------------------------------


def oneway(skin: Skin) -> Image.Image:
    tile = Tile(ONEWAY, True, False, skin.key, "oneway")
    rng = tile.rng
    y = tile.y
    if skin.oneway == "grate":
        metal = _mix(skin.cap_colour, skin.light, 0.35)
        tile.put((y < 3.4).astype(np.float32), metal)
        tile.put((y < 0.7).astype(np.float32), _mix(metal, (255, 255, 255), 0.5))
        tile.put(((y >= 1.3) & (y < 2.2)).astype(np.float32) * tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 8 + 1, 0, k * 8 + 7, 16) for k in range(8)]), skin.accent)
        tile.put(((y >= 2.8) & (y < 3.4)).astype(np.float32), skin.dark, 0.8)
        truss = tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(k * 8, 3.4), (k * 8 + 4, 9.2), (k * 8 + 8, 3.4)], 0.8) for k in range(8)])
        tile.put(truss, _mix(metal, skin.dark, 0.45))
        tile.put(((y >= 9.0) & (y < 10.2)).astype(np.float32), _mix(metal, skin.dark, 0.3))
        tile.put(np.clip(1.0 - (y - 10.2) / 3.0, 0, 1) * (y >= 10.2), (0, 0, 0), 0.22)
    elif skin.oneway == "plank":
        wood, wood_dark, wood_light = (126, 88, 54), (60, 38, 24), (178, 136, 88)
        wood = _mix(wood, skin.base, 0.25)
        tile.put((y < 5.6).astype(np.float32), wood)
        tile.tone((tile.noise(3, 10, 2) - 0.5) * 0.3 * (tile.alpha > 0))
        tile.put((y < 0.8).astype(np.float32), wood_light, 0.85)
        tile.put(((y >= 4.8) & (y < 5.6)).astype(np.float32), wood_dark, 0.8)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 16 - 0.3, 0, k * 16 + 0.3, 5.6) for k in range(5)]), wood_dark, 0.85)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 16 + s, 2.6, 0.5) for k in range(4) for s in (1.6, 14.4)]), wood_dark, 0.8)
        brackets = tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(k * 32 + 14, 5.6), (k * 32 + 18, 5.6), (k * 32 + 18, 12.5), (k * 32 + 16.8, 12.5)]) for k in range(2)])
        tile.put(brackets, wood_dark)
        tile.put(np.clip(1.0 - (y - 5.6) / 3.0, 0, 1) * (y >= 5.6) * (1.0 - brackets), (0, 0, 0), 0.25)
    elif skin.oneway == "lasagne":
        # A sheet of lasagne on a line of sauce on a second sheet: the edge
        # of each sheet is a row of small waves, as the pasta is cut.
        pasta = _mix(skin.light, (250, 226, 160), 0.45)
        wave = 0.5 * np.sin(tile.x * math.pi / 4.0)
        top = ((y >= 0.5 + wave * 0.6) & (y < 2.9 + wave)).astype(np.float32)
        low = ((y >= 4.1 + wave) & (y < 6.6 - wave * 0.8)).astype(np.float32)
        tile.put(((y >= 2.6) & (y < 4.4)).astype(np.float32), skin.cap_colour)
        tile.put(low, _mix(pasta, skin.base, 0.25))
        tile.put(top, pasta)
        tile.put(top * (y < 1.3 + wave * 0.6), _mix(pasta, (255, 255, 240), 0.5), 0.8)
        tile.put(low * (y > 5.8 - wave * 0.8), skin.dark, 0.5)
        # Sauce that runs out of the edge here and there.
        drips = [(rng.uniform(0, 64), rng.uniform(1.6, 3.6)) for _ in range(5)]
        tile.put(tile.mask(lambda p, dx, dy: [(_box(p, dx, dy, x - 0.5, 4.2, x + 0.5, 6.4 + h), _dot(p, dx, dy, x, 6.4 + h, 0.75)) for x, h in drips]), skin.cap_colour)
        tile.put(np.clip(1.0 - (y - 6.6) / 3.0, 0, 1) * (y >= 6.6) * (tile.alpha < 0.5), (0, 0, 0), 0.22)
    elif skin.oneway == "palette":
        # A painter's palette seen from its edge: a board of pale wood with
        # blobs of paint on it, and the shade under it.
        wood = (204, 160, 108)
        wood_dark = (126, 88, 52)
        tile.put((y < 5.4).astype(np.float32), wood)
        tile.tone(((np.sin(tile.x * 0.9 + np.sin(tile.x * 0.13) * 3.0) * 0.5) * 0.10) * (y < 5.4))
        tile.put((y < 0.8).astype(np.float32), _mix(wood, (255, 248, 230), 0.5))
        tile.put(((y >= 4.4) & (y < 5.4)).astype(np.float32), wood_dark, 0.8)
        blobs = [(k * 10.6 + rng.uniform(1.0, 4.0), rng.uniform(1.6, 2.6), c) for k, c in enumerate(((232, 54, 172), (255, 210, 50), (40, 200, 236), (250, 250, 250), (118, 64, 196), (255, 130, 60)))]
        for x, r, colour in blobs:
            tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x, 0.9, r, ry=r * 0.55)), colour)
            tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x - r * 0.3, 0.6, r * 0.35, ry=r * 0.18)), (255, 255, 255), 0.6)
        tile.put(np.clip(1.0 - (y - 5.4) / 3.0, 0, 1) * (y >= 5.4), (0, 0, 0), 0.22)
    elif skin.oneway == "ruler":
        # A wooden ruler laid flat: marks along its top edge, a long one each
        # eight units, and its numbers as small dark dots.
        wood = (226, 196, 140)
        tile.put((y < 5.0).astype(np.float32), wood)
        tile.put((y < 0.7).astype(np.float32), _mix(wood, (255, 255, 240), 0.5))
        tile.put(((y >= 4.3) & (y < 5.0)).astype(np.float32), (140, 108, 64), 0.8)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 2 - 0.15, 0.0, k * 2 + 0.15, 2.8 if k % 4 == 0 else 1.4) for k in range(33)]), skin.accent, 0.85)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 8 + 2.0, 3.6, 0.45) for k in range(8)]), skin.accent, 0.7)
        tile.put(np.clip(1.0 - (y - 5.0) / 3.0, 0, 1) * (y >= 5.0), (0, 0, 0), 0.20)
    elif skin.oneway == "shelf":
        # A shelf board: a gilt edge on its front, and a bracket of turned
        # wood under it each 32 units.
        wood, wood_dark = (118, 72, 44), (58, 34, 22)
        tile.put((y < 4.6).astype(np.float32), wood)
        tile.tone(((np.sin(tile.x * 0.8 + np.sin(tile.x * 0.11) * 3.0) * 0.5) * 0.12) * (y < 4.6))
        tile.put((y < 0.8).astype(np.float32), _mix(wood, (255, 236, 200), 0.45))
        tile.put(((y >= 1.6) & (y < 2.2)).astype(np.float32), skin.accent, 0.85)
        tile.put(((y >= 3.8) & (y < 4.6)).astype(np.float32), wood_dark, 0.8)
        brackets = tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(k * 32 + 13, 4.6), (k * 32 + 19, 4.6), (k * 32 + 17, 7.0), (k * 32 + 17.6, 9.0), (k * 32 + 16, 11.0), (k * 32 + 14.4, 9.0), (k * 32 + 15, 7.0)]) for k in range(2)])
        tile.put(brackets, wood_dark)
        tile.put(np.clip(1.0 - (y - 4.6) / 3.0, 0, 1) * (y >= 4.6) * (1.0 - brackets), (0, 0, 0), 0.24)
    elif skin.oneway == "stave":
        # A line of a stave: a strip of the paper of sheet music on a rail of
        # brass, its five lines in ink, a bar line each 32 units, and a note
        # here and there.
        paper = (196, 188, 166)
        tile.put((y < 6.4).astype(np.float32), paper)
        tile.put((y < 0.9).astype(np.float32), skin.cap_colour)
        tile.put((y < 0.35).astype(np.float32), (255, 244, 200), 0.7)
        for k in range(5):
            tile.put(((y >= 1.5 + k * 1.0) & (y < 1.75 + k * 1.0)).astype(np.float32), skin.dark, 0.75)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32 + 0.0, 1.5, k * 32 + 0.35, 5.75) for k in range(3)]), skin.dark, 0.8)
        heads = [(rng.uniform(4, 28) + k * 32.0, 1.6 + rng.randint(0, 8) * 0.5) for k in range(2)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 0.75, ry=0.55) for x, yy in heads]), skin.dark)
        tile.put(((y >= 5.8) & (y < 6.4)).astype(np.float32), skin.dark, 0.8)
        tile.put(np.clip(1.0 - (y - 6.4) / 3.0, 0, 1) * (y >= 6.4), skin.accent, 0.18)
    elif skin.oneway == "catwalk":
        # A catwalk over a stage: a deck of black steel with holes in it, a
        # line of gold on its edge, and a lamp clamped under it.
        steel = (40, 34, 40)
        tile.put((y < 3.2).astype(np.float32), steel)
        tile.put((y < 0.6).astype(np.float32), skin.accent, 0.9)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 4.0 + 2.0, 1.9, 0.6) for k in range(16)]), skin.dark, 0.8)
        truss = tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(k * 8, 3.2), (k * 8 + 4, 7.4), (k * 8 + 8, 3.2)], 0.6) for k in range(8)])
        tile.put(truss, _mix(steel, (90, 80, 90), 0.4))
        tile.put(((y >= 7.0) & (y < 7.8)).astype(np.float32), _mix(steel, (90, 80, 90), 0.4))
        lamps = tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(k * 32 + 14, 7.8), (k * 32 + 18, 7.8), (k * 32 + 19.5, 11.0), (k * 32 + 12.5, 11.0)]) for k in range(2)])
        tile.put(lamps, steel)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 32 + 16, 11.0, 2.4, ry=0.8) for k in range(2)]), (255, 236, 190))
        tile.put(np.clip(1.0 - (y - 7.8) / 3.0, 0, 1) * (y >= 7.8) * (1.0 - lamps), (0, 0, 0), 0.20)
    elif skin.oneway == "bench":
        # A workbench: a thick top of wood with the marks of tools on it, a
        # vise at one end, and braces under it.
        wood, wood_dark = (150, 104, 62), (72, 46, 28)
        tile.put((y < 5.2).astype(np.float32), wood)
        tile.tone((tile.noise(3, 10, 2) - 0.5) * 0.28 * (y < 5.2))
        tile.put((y < 0.8).astype(np.float32), _mix(wood, (255, 236, 200), 0.4))
        tile.put(((y >= 4.4) & (y < 5.2)).astype(np.float32), wood_dark, 0.8)
        cuts = [(rng.uniform(0, 64), rng.uniform(1.4, 3.6), rng.uniform(2.0, 4.0)) for _ in range(5)]
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, yy), (x + w, yy + 0.3)], 0.25) for x, yy, w in cuts]), wood_dark, 0.6)
        tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, 40.0, 0.4, 46.0, 6.6), _box(p, dx, dy, 42.4, 6.6, 43.6, 9.0))), (92, 96, 104))
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 40.0, 0.4, 46.0, 1.2)), (170, 176, 184), 0.8)
        braces = tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(k * 32 + 6, 5.2), (k * 32 + 12, 11.0)], 1.1) for k in range(2)] + [_line(p, dx, dy, [(k * 32 + 26, 5.2), (k * 32 + 20, 11.0)], 1.1) for k in range(2)])
        tile.put(braces, wood_dark)
        tile.put(np.clip(1.0 - (y - 5.2) / 3.0, 0, 1) * (y >= 5.2) * (1.0 - braces), (0, 0, 0), 0.24)
    elif skin.oneway == "roof":
        # A ridge of roof tiles: a cap of half-round tiles along the top,
        # and the round ends of the rows of tiles hanging below it.
        tile_c, tile_dark = (72, 78, 94), (30, 32, 42)
        tile_light = _mix(tile_c, (220, 226, 240), 0.35)
        tile.put((y < 3.0).astype(np.float32), tile_c)
        tile.put((y < 0.7).astype(np.float32), tile_light, 0.9)
        tile.put(((y >= 2.4) & (y < 3.0)).astype(np.float32), tile_dark, 0.8)
        ends = tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 8 + 4, 4.6, 3.6, ry=2.6) for k in range(8)])
        tile.put(ends * (y >= 2.0), tile_c)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 8 + 4, 4.6, 1.5, ry=1.0) for k in range(8)]), tile_dark, 0.6)
        tile.put(ends * (y >= 6.2), tile_dark, 0.6)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 8 - 0.25, 0.8, k * 8 + 0.25, 3.0) for k in range(9)]), tile_dark, 0.6)
        tile.put(np.clip(1.0 - (y - 7.2) / 2.5, 0, 1) * (y >= 7.2) * (tile.alpha < 0.5), (0, 0, 0), 0.20)
    elif skin.oneway == "rim":
        # A thin bar of the void: black, with the white line all round it,
        # and a grey joint each 32 units.
        tile.put((y < 4.2).astype(np.float32), skin.cap_colour)
        tile.put(((y >= 1.0) & (y < 3.2)).astype(np.float32), skin.dark)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32 - 0.25, 1.0, k * 32 + 0.25, 3.2) for k in range(3)]), (70, 70, 72))
    elif skin.oneway == "reed_mat":
        # A mat of reeds bound in bundles: reeds along it in fine lines of
        # each tone, a binding of cord each eight units, and the cut ends of
        # the reeds that hang a little under it.
        reed, reed_dark = (204, 178, 112), (110, 88, 50)
        tile.put((y < 5.0).astype(np.float32), reed)
        for k in range(10):
            yy = 0.4 + k * 0.46
            tone = rng.uniform(-0.18, 0.12)
            tile.put(((y >= yy) & (y < yy + 0.22)).astype(np.float32), _mix(reed, reed_dark if tone < 0 else (250, 236, 190), abs(tone) * 2.0), 0.8)
        tile.put((y < 0.7).astype(np.float32), (250, 236, 190), 0.6)
        bands = tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 8.0 + 3.2, -0.2, k * 8.0 + 4.6, 5.4) for k in range(8)])
        tile.put(bands, reed_dark)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(k * 8.0 + 3.2, 0.6 + j * 1.3), (k * 8.0 + 4.6, 1.2 + j * 1.3)], 0.25) for k in range(8) for j in range(4)]), (60, 46, 26), 0.6)
        tile.put(((y >= 4.4) & (y < 5.0)).astype(np.float32), reed_dark, 0.7)
        cut = [(rng.uniform(0, 64), rng.uniform(0.6, 2.2)) for _ in range(40)]
        ends = tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, 5.0), (x + 0.2, 5.0 + h)], 0.3) for x, h in cut])
        tile.put(ends, reed, 0.8)
        tile.put(np.clip(1.0 - (y - 5.0) / 3.0, 0, 1) * (y >= 5.0) * (1.0 - ends), (0, 0, 0), 0.22)
    elif skin.oneway == "palm_log":
        # A beam of palm log: round, the bark in small scales, a band of
        # lapis paint each thirty two units, and its round shade under it.
        wood, wood_dark = (130, 92, 58), (62, 42, 26)
        body = (y < 6.0).astype(np.float32)
        tile.put(body, wood)
        scales = (np.abs(((tile.x * 0.5 + y * 0.7) % 1.6) - 0.8) < 0.18) | (np.abs(((tile.x * 0.5 - y * 0.7) % 1.6) - 0.8) < 0.18)
        tile.put(scales.astype(np.float32) * body, wood_dark, 0.45)
        tile.put(np.clip(1.0 - np.abs(y - 1.4) / 1.2, 0, 1) * body, (230, 196, 150), 0.35)
        tile.put(np.clip((y - 3.5) / 2.5, 0, 1) * body, wood_dark, 0.6)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32.0 + 14.0, 0.0, k * 32.0 + 18.0, 6.0) for k in range(2)]), skin.accent, 0.75)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32.0 + 14.6, 0.0, k * 32.0 + 15.2, 6.0) for k in range(2)]), (236, 190, 70), 0.85)
        tile.put(np.clip(1.0 - (y - 6.0) / 3.0, 0, 1) * (y >= 6.0), (0, 0, 0), 0.24)
    elif skin.oneway == "lintel":
        # A lintel of marble: a face in three bands, a moulding on its top,
        # and a row of small blocks (dentils) under it.
        marble, marble_dark = (226, 222, 214), (140, 140, 150)
        tile.put((y < 5.6).astype(np.float32), marble)
        tile.tone((tile.noise(6, 2, 3) - 0.5) * 0.10 * (tile.alpha > 0))
        tile.put((y < 0.7).astype(np.float32), (255, 255, 250), 0.8)
        for yy in (1.4, 3.0, 4.4):
            tile.put(((y >= yy) & (y < yy + 0.35)).astype(np.float32), marble_dark, 0.55)
        dentils = tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 3.2 + 0.6, 5.6, k * 3.2 + 2.4, 7.6) for k in range(20)])
        tile.put(dentils, _mix(marble, marble_dark, 0.25))
        tile.put(dentils * (y > 7.0), marble_dark, 0.6)
        tile.put(np.clip(1.0 - (y - 5.6) / 3.0, 0, 1) * (y >= 5.6) * (1.0 - dentils), (0, 0, 0), 0.22)
    elif skin.oneway == "balcony":
        # A balcony rail of carved wood in red lacquer: a top rail, a lattice
        # of open fretwork under it, a low rail, and a post each sixteen units.
        red, red_dark, gold = (170, 40, 36), (84, 18, 18), (226, 176, 70)
        tile.put((y < 2.2).astype(np.float32), red)
        tile.put((y < 0.6).astype(np.float32), _mix(red, (255, 220, 200), 0.4))
        tile.put(((y >= 1.6) & (y < 2.2)).astype(np.float32), red_dark, 0.7)
        tile.put(((y >= 9.0) & (y < 10.4)).astype(np.float32), red)
        lattice = tile.mask(lambda p, dx, dy: [(_box(p, dx, dy, k * 4.0, 2.2, k * 4.0 + 0.6, 9.0), _box(p, dx, dy, k * 4.0, 5.3, k * 4.0 + 4.0, 5.9)) for k in range(16)])
        tile.put(lattice, red_dark)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 16.0 + 6.8, 0.0, k * 16.0 + 9.2, 10.4) for k in range(4)]), red)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 16.0 + 8.0, 1.1, 0.6) for k in range(4)]), gold)
        tile.put(np.clip(1.0 - (y - 10.4) / 3.0, 0, 1) * (y >= 10.4), (0, 0, 0), 0.20)
    elif skin.oneway == "felt":
        # A pole wrapped in white felt, with a band of red and a band of blue
        # felt on it, bound with cord each ten units.
        felt, felt_dark = (236, 228, 208), (150, 140, 124)
        tile.put((y < 5.4).astype(np.float32), felt)
        tile.tone((tile.noise(12, 3, 2) - 0.5) * 0.12 * (tile.alpha > 0))
        tile.put(((y >= 1.6) & (y < 2.4)).astype(np.float32), (170, 52, 40))
        tile.put(((y >= 2.9) & (y < 3.5)).astype(np.float32), skin.accent)
        tile.put((y < 0.7).astype(np.float32), (255, 252, 240), 0.6)
        tile.put(np.clip((y - 3.8) / 1.6, 0, 1) * (y < 5.4), felt_dark, 0.6)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(k * 10.67 + 4.0, -0.2), (k * 10.67 + 5.2, 5.6)], 0.5) for k in range(6)]), (110, 80, 50))
        tile.put(np.clip(1.0 - (y - 5.4) / 3.0, 0, 1) * (y >= 5.4), (0, 0, 0), 0.22)
    elif skin.oneway == "toron":
        # A beam of palm wood with its fibres along it, and under it the
        # ends of the toron: short beams that come out of the wall, one each
        # sixteen units.
        wood, wood_dark = (120, 86, 54), (58, 40, 26)
        tile.put((y < 4.6).astype(np.float32), wood)
        tile.put((((y * 3.0) % 1.0) < 0.25).astype(np.float32) * (y < 4.6), wood_dark, 0.35)
        tile.tone((tile.noise(10, 2, 2) - 0.5) * 0.20 * (tile.alpha > 0))
        tile.put((y < 0.7).astype(np.float32), _mix(wood, (255, 236, 200), 0.45), 0.8)
        tile.put(((y >= 3.9) & (y < 4.6)).astype(np.float32), wood_dark, 0.8)
        stubs = tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 16.0 + 6.0, 4.6, k * 16.0 + 10.0, 10.0) for k in range(4)])
        tile.put(stubs, _mix(wood, wood_dark, 0.3))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 16.0 + 8.0, 9.2, 1.6, ry=0.9) for k in range(4)]), _mix(wood, (230, 200, 150), 0.3))
        tile.put(np.clip(1.0 - (y - 4.6) / 3.0, 0, 1) * (y >= 4.6) * (1.0 - stubs), (0, 0, 0), 0.22)
    elif skin.oneway == "yard":
        # The yard of a mast: a round spar of wood, and the sail furled under
        # it in a long roll of canvas, held by gaskets of rope.
        wood, canvas = (140, 100, 62), (232, 222, 196)
        tile.put((y < 3.0).astype(np.float32), wood)
        tile.put(np.clip(1.0 - np.abs(y - 0.8) / 0.7, 0, 1) * (y < 3.0), (255, 236, 200), 0.4)
        tile.put(((y >= 2.4) & (y < 3.0)).astype(np.float32), (70, 48, 30), 0.7)
        bulge = 3.0 + 4.2 + 0.8 * np.sin(tile.x * math.pi / 8.0) ** 2
        roll = np.clip((bulge - y) * K * 0.5 + 0.5, 0, 1) * (y >= 2.8)
        tile.put(roll, canvas)
        tile.put(roll * np.clip((y - 5.0) / 3.0, 0, 1), (150, 140, 120), 0.6)
        tile.put(roll * (np.abs(((tile.x + y * 0.6) % 4.0) - 2.0) < 0.2), (180, 170, 150), 0.5)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 16.0 + 7.4, 2.6, k * 16.0 + 8.6, 8.6) for k in range(4)]), (150, 120, 80))
        tile.put(np.clip(1.0 - (y - bulge) / 3.0, 0, 1) * (y >= bulge), (0, 0, 0), 0.20)
    elif skin.oneway == "ironwork":
        # A lattice girder of iron: a top flange with rivets, a web of bars
        # in a zigzag, and a bottom flange.
        iron, iron_dark = _mix(skin.cap_colour, (140, 140, 146), 0.25), (30, 30, 34)
        tile.put((y < 2.2).astype(np.float32), iron)
        tile.put((y < 0.6).astype(np.float32), (180, 182, 188), 0.7)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 4.0 + 2.0, 1.3, 0.45) for k in range(16)]), iron_dark, 0.7)
        web = tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(k * 8.0, 2.0), (k * 8.0 + 4.0, 8.4), (k * 8.0 + 8.0, 2.0)], 0.8) for k in range(8)])
        tile.put(web, _mix(iron, iron_dark, 0.35))
        tile.put(((y >= 8.2) & (y < 9.6)).astype(np.float32), iron)
        tile.put(((y >= 9.1) & (y < 9.6)).astype(np.float32), iron_dark, 0.7)
        tile.put(np.clip(1.0 - (y - 9.6) / 3.0, 0, 1) * (y >= 9.6), (0, 0, 0), 0.22)
    elif skin.oneway == "log":
        # A log laid along: round, the bark in long cracks, a knot here and
        # there, and a lashing of rope each thirty two units.
        bark, bark_dark = _mix(skin.base, (120, 92, 66), 0.6), _mix(skin.dark, (40, 30, 22), 0.5)
        body = (y < 6.4).astype(np.float32)
        tile.put(body, bark)
        cracks = np.clip(1.0 - np.abs(((y + (tile.noise(6, 2, 2) - 0.5) * 1.6) % 1.3) - 0.65) / 0.12, 0, 1) * body
        tile.put(cracks, bark_dark, 0.45)
        tile.put(np.clip(1.0 - np.abs(y - 1.5) / 1.3, 0, 1) * body, (236, 214, 180), 0.30)
        tile.put(np.clip((y - 3.8) / 2.6, 0, 1) * body, bark_dark, 0.55)
        knots = [(rng.uniform(4.0, 28.0) + k * 32.0, rng.uniform(2.2, 4.2)) for k in range(2)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 1.2, ry=0.8) for x, yy in knots]), bark_dark, 0.8)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.2, yy - 0.2, 0.6, ry=0.4) for x, yy in knots]), bark, 0.8)
        rope = (190, 160, 110)
        for k in range(2):
            x0 = k * 32.0 + 14.0
            tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x0 + j * 1.0, -0.2), (x0 + j * 1.0 + 0.8, 6.6)], 0.6) for j in range(4)]), _mix(rope, bark_dark, 0.3))
            tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x0 + j * 1.0 - 0.1, -0.1), (x0 + j * 1.0 + 0.7, 6.4)], 0.25) for j in range(4)]), rope, 0.9)
        tile.put(np.clip(1.0 - (y - 6.4) / 3.0, 0, 1) * (y >= 6.4), (0, 0, 0), 0.24)
    elif skin.oneway == "bone":
        # Tusks of a mammoth laid end to end and lashed with strips of hide:
        # an ivory beam with fine growth lines, and a joint each thirty two
        # units with a strip of hide round it.
        ivory, ivory_dark, hide = (226, 216, 190), (140, 126, 100), (124, 86, 58)
        body = (y < 5.2).astype(np.float32)
        tile.put(body, ivory)
        tile.put(np.clip(1.0 - np.abs(((y + np.sin(tile.x * math.pi / 32.0) * 0.4) % 1.3) - 0.65) / 0.1, 0, 1) * body, ivory_dark, 0.18)
        tile.put((y < 0.8).astype(np.float32), (255, 250, 236), 0.6)
        tile.put(np.clip((y - 3.0) / 2.2, 0, 1) * body, ivory_dark, 0.55)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32.0 - 0.3, 0.0, k * 32.0 + 0.3, 5.2) for k in range(3)]), ivory_dark, 0.9)
        straps = tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32.0 - 2.2, -0.2, k * 32.0 + 2.2, 5.6) for k in range(3)])
        tile.put(straps, hide)
        tile.put(straps * (np.abs(((tile.x + 2.2) % 32.0) - 2.2) < 0.25), _mix(hide, (40, 26, 16), 0.5), 0.8)
        tile.put(straps * (y < 1.0), _mix(hide, (230, 200, 160), 0.4), 0.6)
        tile.put(np.clip(1.0 - (y - 5.2) / 3.0, 0, 1) * (y >= 5.2), (0, 0, 0), 0.24)
    elif skin.oneway == "sarsen":
        # A lintel of sarsen stone: dressed flat on its top and rough on its
        # lower edge, grey, with the marks of the tools that dressed it and
        # spots of lichen.
        stone, stone_dark = (152, 150, 142), (80, 80, 78)
        lower = 6.2 + tile.profile(8, 3)[None, :] * 2.2
        body = np.clip((lower - y) * K * 0.5 + 0.5, 0, 1)
        tile.put(body, stone)
        tile.tone((tile.noise(10, 3, 3) - 0.5) * 0.22 * (tile.alpha > 0))
        tile.put((y < 0.8).astype(np.float32), (214, 212, 204), 0.7)
        marks = [(rng.uniform(0, 64), rng.uniform(1.4, 5.0)) for _ in range(24)]
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, yy), (x + 0.8, yy + 0.6)], 0.22) for x, yy in marks]) * body, stone_dark, 0.35)
        lichen = [(rng.uniform(0, 64), rng.uniform(1.0, 6.0), rng.uniform(0.4, 1.1), rng.random() < 0.5) for _ in range(12)]
        for pale in (True, False):
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r, ry=r * 0.7) for x, yy, r, kind in lichen if kind == pale]) * body, (230, 230, 214) if pale else (200, 192, 110), 0.6)
        tile.put(body * np.clip((y - lower + 2.0) / 2.0, 0, 1), stone_dark, 0.5)
        tile.put(np.clip(1.0 - (y - lower) / 3.0, 0, 1) * (y >= lower), (0, 0, 0), 0.22)
    elif skin.oneway == "bamboo":
        # Two poles of bamboo, one on the other, a node each sixteen units,
        # and a binding of cord each thirty two units.
        cane, cane_dark, cane_light = (196, 184, 110), (110, 100, 56), (240, 232, 170)
        for top, offset in ((0.0, 0.0), (2.6, 8.0)):
            pole = ((y >= top) & (y < top + 2.6)).astype(np.float32)
            tile.put(pole, cane)
            tile.put(pole * np.clip(1.0 - np.abs(y - top - 0.8) / 0.6, 0, 1), cane_light, 0.6)
            tile.put(pole * np.clip((y - top - 1.4) / 1.2, 0, 1), cane_dark, 0.55)
            nodes = tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 16.0 + offset - 0.35, top, k * 16.0 + offset + 0.35, top + 2.6) for k in range(5)])
            tile.put(nodes * pole, cane_dark, 0.8)
            tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 16.0 + offset + 0.35, top, k * 16.0 + offset + 0.8, top + 2.6) for k in range(5)]) * pole, cane_light, 0.5)
        cord = (120, 86, 52)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(k * 32.0 + 20.0 + j * 0.9, -0.2), (k * 32.0 + 20.6 + j * 0.9, 5.4)], 0.45) for k in range(2) for j in range(3)]), cord)
        tile.put(np.clip(1.0 - (y - 5.2) / 3.0, 0, 1) * (y >= 5.2), (0, 0, 0), 0.24)
    elif skin.oneway == "basalt_column":
        # A column of basalt laid along, as the builders of the Gulf coast
        # set them in fences: six faces, so three show (a lit top face, a
        # front face and a dark lower face), rough, and a joint where one
        # column ends and the next begins.
        basalt = _mix(skin.dark, (90, 92, 96), 0.6)
        tile.put((y < 6.6).astype(np.float32), basalt)
        tile.put((y < 1.8).astype(np.float32), _mix(basalt, (200, 204, 206), 0.30))
        tile.put((y < 0.5).astype(np.float32), _mix(basalt, (230, 232, 230), 0.45))
        tile.put(((y >= 4.8) & (y < 6.6)).astype(np.float32), _mix(basalt, (0, 0, 0), 0.35))
        tile.tone((tile.noise(10, 3, 3) - 0.5) * 0.24 * (tile.alpha > 0))
        for k in range(2):
            x0 = k * 32.0 + 22.0
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 - 0.5, 0.0, x0 + 0.5, 6.6)), _mix(basalt, (0, 0, 0), 0.5))
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.5, 0.0, x0 + 1.0, 6.6)), _mix(basalt, (220, 220, 220), 0.3), 0.6)
        tile.put(np.clip(1.0 - (y - 6.6) / 3.0, 0, 1) * (y >= 6.6), (0, 0, 0), 0.24)
    elif skin.oneway == "zapote":
        # A lintel of sapodilla wood, hard and red-brown, carved along its
        # face with a row of glyph blocks in low relief.
        wood, wood_dark, wood_light = (128, 70, 46), (60, 30, 20), (176, 110, 72)
        tile.put((y < 6.4).astype(np.float32), wood)
        tile.tone((tile.noise(3, 10, 2) - 0.5) * 0.18 * (tile.alpha > 0))
        tile.put((y < 0.8).astype(np.float32), wood_light, 0.8)
        tile.put(((y >= 5.6) & (y < 6.4)).astype(np.float32), wood_dark, 0.8)
        for k in range(4):
            x0 = k * 16.0 + 3.0
            block = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, 1.4, x0 + 10.0, 5.0))
            tile.put(block, wood_dark, 0.35)
            tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0, 1.4, x0 + 10.0, 1.8), _box(p, dx, dy, x0, 1.4, x0 + 0.4, 5.0))), wood_dark, 0.6)
            tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0, 4.6, x0 + 10.0, 5.0), _box(p, dx, dy, x0 + 9.6, 1.4, x0 + 10.0, 5.0))), wood_light, 0.6)
            glyph = [(x0 + 2.0, 2.4), (x0 + 5.0, 2.2), (x0 + 8.0, 2.6), (x0 + 7.4, 4.2), (x0 + 3.0, 4.2)]
            tile.put(tile.mask(lambda p, dx, dy: (_line(p, dx, dy, glyph + [glyph[0]], 0.35), _dot(p, dx, dy, x0 + 4.0, 3.2, 0.6), _dot(p, dx, dy, x0 + 6.4, 3.4, 0.45))), wood_light, 0.75)
        tile.put(np.clip(1.0 - (y - 6.4) / 3.0, 0, 1) * (y >= 6.4), (0, 0, 0), 0.24)
    elif skin.oneway == "barbacoa":
        # A barbacoa, the Taino frame of green sticks on which meat and fish
        # were dried over a slow fire: thin sticks along it, the round ends
        # of the cross sticks under them, and a lashing of cord at each.
        green, green_dark, green_light = (120, 128, 66), (58, 64, 30), (176, 180, 104)
        for k, yy in enumerate((0.0, 1.5)):
            tile.put(((y >= yy) & (y < yy + 1.2)).astype(np.float32), green if k == 0 else _mix(green, green_dark, 0.3))
            tile.put(((y >= yy) & (y < yy + 0.35)).astype(np.float32), green_light, 0.7)
        ends = tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 8.0 + 4.0, 4.0, 1.25) for k in range(8)])
        tile.put(ends, _mix(green, (160, 120, 70), 0.4))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 8.0 + 4.0, 4.0, 0.6) for k in range(8)]), (210, 190, 130), 0.8)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(k * 8.0 + 2.6, 0.2), (k * 8.0 + 5.4, 2.8)], 0.3) for k in range(8)]), (190, 160, 110), 0.85)
        tile.put(((y >= 5.4) & (y < 6.6)).astype(np.float32), _mix(green, green_dark, 0.5))
        tile.put(np.clip(1.0 - (y - 6.6) / 3.0, 0, 1) * (y >= 6.6), (0, 0, 0), 0.22)
    elif skin.oneway == "stilt_deck":
        # The floor of a house on stilts: the round ends of the floor poles
        # in a row, on a bearer lashed with cord, and a stilt each thirty
        # two units.
        wood, wood_dark, wood_light = (150, 112, 74), (66, 46, 30), (206, 170, 120)
        poles = tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 4.0 + 2.0, 1.6, 1.6) for k in range(16)])
        tile.put(poles, wood)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 4.0 + 1.6, 1.2, 0.7) for k in range(16)]), wood_light, 0.6)
        tile.put(((y >= 3.0) & (y < 5.6)).astype(np.float32), _mix(wood, wood_dark, 0.35))
        tile.put(((y >= 3.0) & (y < 3.5)).astype(np.float32), wood_light, 0.4)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(k * 16.0 + 7.0 + j * 0.8, 2.4), (k * 16.0 + 7.6 + j * 0.8, 5.8)], 0.35) for k in range(4) for j in range(3)]), (190, 160, 110), 0.9)
        stilts = tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32.0 + 14.6, 5.6, k * 32.0 + 17.4, 16.0) for k in range(2)])
        tile.put(stilts * np.clip(1.0 - (y - 5.6) / 10.0, 0, 1), _mix(wood, wood_dark, 0.5))
        tile.put(np.clip(1.0 - (y - 5.6) / 3.0, 0, 1) * (y >= 5.6) * (1.0 - stilts), (0, 0, 0), 0.22)
    elif skin.oneway == "spar":
        # A spar of a voyaging canoe: a round pole of light wood, lashed to
        # the next with cord of coconut fibre in a cross, and a loop of cord
        # that hangs under each lashing.
        wood, wood_dark = (196, 168, 118), (110, 86, 56)
        body = (y < 4.0).astype(np.float32)
        tile.put(body, wood)
        tile.put(np.clip(1.0 - np.abs(y - 1.0) / 0.8, 0, 1) * body, (250, 236, 200), 0.45)
        tile.put(np.clip((y - 2.4) / 1.6, 0, 1) * body, wood_dark, 0.55)
        cord = _mix(skin.accent, (120, 90, 56), 0.4)
        for k in range(4):
            x0 = k * 16.0 + 8.0
            tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x0 - 1.6 + j * 0.8, -0.2), (x0 + 0.4 + j * 0.8, 4.2)], 0.35) for j in range(4)] + [_line(p, dx, dy, [(x0 + 1.6 - j * 0.8, -0.2), (x0 - 0.4 - j * 0.8, 4.2)], 0.35) for j in range(4)]), cord)
            tile.put(tile.mask(lambda p, dx, dy: p.arc([(x0 - 1.4) * K + dx, (2.6) * K + dy, (x0 + 1.4) * K + dx, (8.0) * K + dy], 0, 180, fill=255, width=max(1, int(0.35 * K)))), cord, 0.9)
        tile.put(np.clip(1.0 - (y - 4.0) / 3.0, 0, 1) * (y >= 4.0), (0, 0, 0), 0.22)
    elif skin.oneway == "ahu":
        # The face of an ahu: slabs of basalt dressed flat and fitted so
        # close that a blade does not go between them, each of its own size
        # and tone, the joints at a slant here and there.
        basalt, basalt_dark = (96, 96, 100), (40, 40, 44)
        tile.put((y < 7.0).astype(np.float32), basalt_dark)
        x, before = 0.0, 0.0
        while x < 64.0:
            w = min(rng.uniform(9.0, 15.0), 64.0 - x)
            if 64.0 - x - w < 6.0:
                w = 64.0 - x
            # The slant of the joint at the right end of this slab; the joint
            # at the end of the tile is upright, so the tile repeats.
            after = rng.uniform(-1.2, 1.2) if x + w < 64.0 else 0.0
            tone = rng.uniform(-0.14, 0.12)
            colour = _mix(basalt, (200, 200, 196) if tone > 0 else basalt_dark, abs(tone) * 1.6)
            x0, x1, left, right = x, x + w, before, after
            tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x0 + 0.25, 0.0), (x1 - 0.25, 0.0), (x1 - 0.25 + right, 7.0), (x0 + 0.25 + left, 7.0)])), colour)
            x, before = x + w, after
        tile.tone((tile.noise(10, 3, 2) - 0.5) * 0.16 * (tile.alpha > 0))
        tile.put((y < 0.8).astype(np.float32), (190, 190, 186), 0.6)
        tile.put(((y >= 6.2) & (y < 7.0)).astype(np.float32), basalt_dark, 0.7)
        tile.put(np.clip(1.0 - (y - 7.0) / 3.0, 0, 1) * (y >= 7.0), (0, 0, 0), 0.24)
    elif skin.oneway == "hardwood_beam":
        # A squared beam of dark hardwood, as in the roofs and the galleries
        # of Benin: the flat facets that the adze left on its face, its
        # grain along it, a joint each thirty-two units with a wooden peg on
        # each side of it, and a lit top edge.
        wood, wood_dark, wood_light = (110, 70, 44), (52, 30, 20), (164, 116, 76)
        body = (y < 6.2).astype(np.float32)
        tile.put(body, wood)
        facets = [(rng.uniform(0.0, 64.0), rng.uniform(3.0, 6.0)) for _ in range(9)]
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x, 0.9, x + w, 5.2) for x, w in facets]), wood_light, 0.18)
        grain = np.clip(1.0 - np.abs(((y + (tile.noise(3, 8, 2) - 0.5) * 2.4) % 1.3) - 0.65) / 0.12, 0.0, 1.0)
        tile.put(grain * body, wood_dark, 0.22)
        tile.put((y < 0.8).astype(np.float32), wood_light, 0.85)
        tile.put(((y >= 5.4) & (y < 6.2)).astype(np.float32), wood_dark, 0.85)
        for k in range(2):
            x0 = k * 32.0 + 20.0
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 - 0.35, 0.0, x0 + 0.35, 6.2)), wood_dark, 0.9)
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x0 + side, 3.1, 0.75) for side in (-2.6, 2.6)]), _mix(wood_light, (220, 190, 140), 0.3))
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x0 + side + 0.25, 3.35, 0.35) for side in (-2.6, 2.6)]), wood_dark, 0.6)
        tile.put(np.clip(1.0 - (y - 6.2) / 3.0, 0, 1) * (y >= 6.2), (0, 0, 0), 0.24)
    elif skin.oneway == "rough_plank":
        # A rough plank, sawn by hand: its edges are not quite straight, the
        # saw left slanted marks across its face, the grain runs along it
        # with a knot here and there, and one end has a split. It lies on a
        # cleat each thirty-two units, held by square iron nails.
        wood, wood_dark, wood_light = (128, 92, 60), (58, 38, 26), (182, 142, 96)
        wobble = 0.35 * np.sin(tile.x * math.pi / 32.0 + 0.8) + 0.25 * np.sin(tile.x * math.pi / 8.0 + 2.1)
        body = (y < 5.4 + wobble).astype(np.float32)
        tile.put(body, wood)
        tile.tone((tile.noise(2, 12, 2) - 0.5) * 0.28 * body)
        grain = np.clip(1.0 - np.abs(((y + (tile.noise(4, 6, 2) - 0.5) * 2.0) % 1.4) - 0.7) / 0.10, 0.0, 1.0)
        tile.put(grain * body, wood_dark, 0.22)
        saw = np.clip(1.0 - np.abs(((tile.x + y * 0.55) % 2.3) - 1.15) / 0.12, 0.0, 1.0) * (tile.noise(3, 3, 2) > 0.5)
        tile.put(saw * body, wood_light, 0.18)
        tile.put((y < 0.8).astype(np.float32) * body, wood_light, 0.85)
        tile.put(((y >= 4.6 + wobble) & (y < 5.4 + wobble)).astype(np.float32), wood_dark, 0.85)
        knots = [(rng.uniform(4.0, 28.0) + k * 32.0, rng.uniform(1.8, 3.6)) for k in range(2)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 1.1, ry=0.7) for x, yy in knots]), wood_dark, 0.75)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x - 3.0, yy - 0.5), (x - 0.8, yy - 0.2)], 0.15) for x, yy in knots]), wood_dark, 0.5)
        # The joint between two planks, and the split at its end.
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 40.0 - 0.35, 0.0, 40.0 + 0.35, 5.6)), wood_dark, 0.9)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(40.4, 2.6), (44.0, 2.9), (47.5, 2.5)], 0.18)), wood_dark, 0.8)
        cleats = tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32.0 + 12.0, 5.0, k * 32.0 + 17.0, 11.5) for k in range(2)])
        tile.put(cleats, _mix(wood_dark, wood, 0.35))
        tile.put(cleats * tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32.0 + 12.0, 5.0, k * 32.0 + 13.0, 11.5) for k in range(2)]), wood_light, 0.35)
        nails = [(k * 32.0 + 14.5 + side, 2.6) for k in range(2) for side in (-1.2, 1.2)]
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 0.45, yy - 0.45, x + 0.45, yy + 0.45) for x, yy in nails]), (52, 50, 54))
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 0.45, yy - 0.45, x, yy) for x, yy in nails]), (140, 136, 140), 0.6)
        tile.put(np.clip(1.0 - (y - 5.4 - wobble) / 3.0, 0, 1) * (y >= 5.4 + wobble) * (1.0 - cleats), (0, 0, 0), 0.24)
    elif skin.oneway == "timber_plank":
        # A heavy plank of timber, grey with salt and weather: thick, with a
        # worn round top edge, the grain along it, a joint each sixty-four
        # units, and iron bolts with square plates that go through it into
        # a short beam under it. The beam comes out of the wall each
        # thirty-two units.
        wood, wood_dark, wood_light = (118, 104, 86), (54, 46, 40), (170, 158, 138)
        thick = 7.2
        body = (y < thick).astype(np.float32)
        tile.put(body, wood)
        tile.tone((tile.noise(2, 10, 2) - 0.5) * 0.24 * body)
        grain = np.clip(1.0 - np.abs(((y + (tile.noise(3, 8, 2) - 0.5) * 2.6) % 1.5) - 0.75) / 0.10, 0.0, 1.0)
        tile.put(grain * body, wood_dark, 0.24)
        checks = [(rng.uniform(0.0, 64.0), rng.uniform(2.0, 5.0), rng.uniform(4.0, 9.0)) for _ in range(4)]
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, yy), (x + ln, yy + 0.3)], 0.22) for x, yy, ln in checks]), wood_dark, 0.65)
        tile.put((y < 0.8).astype(np.float32), wood_light, 0.85)
        tile.put(((y >= 0.8) & (y < 1.6)).astype(np.float32), wood_light, 0.30)
        tile.put(((y >= thick - 0.9) & (y < thick)).astype(np.float32), wood_dark, 0.85)
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 52.0 - 0.35, 0.0, 52.0 + 0.35, thick)), wood_dark, 0.9)
        beams = tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32.0 + 13.0, thick, k * 32.0 + 19.0, 13.0) for k in range(2)])
        tile.put(beams, _mix(wood_dark, wood, 0.45))
        tile.put(beams * tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32.0 + 13.0, thick, k * 32.0 + 14.0, 13.0) for k in range(2)]), wood_light, 0.30)
        tile.put(beams * tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32.0 + 13.0, 12.2, k * 32.0 + 19.0, 13.0) for k in range(2)]), wood_dark, 0.7)
        iron, iron_light = (58, 56, 58), (128, 124, 124)
        plates = [(k * 32.0 + 16.0, 3.6) for k in range(2)]
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 1.5, yy - 1.5, x + 1.5, yy + 1.5) for x, yy in plates]), iron)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 0.6) for x, yy in plates]), iron_light, 0.8)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 0.4, yy + 1.5, x + 0.4, yy + 3.6) for x, yy in plates]), (120, 72, 46), 0.35)
        tile.put(np.clip(1.0 - (y - thick) / 3.0, 0, 1) * (y >= thick) * (1.0 - beams), (0, 0, 0), 0.24)
    elif skin.oneway == "flagstone":
        # Slabs of flat stone, split from the rock of the mountain, laid end
        # to end. The top is flat and lit, the lower edge is rough, a corner
        # is chipped here and there, and each slab rests on a small stone at
        # each thirty-two units. Grey and yellow lichen grows on the top.
        stone, stone_dark, stone_light = _mix(skin.base, skin.light, 0.30), _mix(skin.base, skin.dark, 0.40), _mix(skin.light, (255, 250, 236), 0.25)
        lower = 4.6 + tile.profile(8, 3)[None, :] * 2.0
        body = np.clip((lower - y) * K * 0.5 + 0.5, 0, 1)
        props = tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(k * 32.0 + 12.0, 5.0), (k * 32.0 + 19.0, 5.0), (k * 32.0 + 20.0, 9.0), (k * 32.0 + 17.0, 10.6), (k * 32.0 + 12.6, 10.2),
                                                             (k * 32.0 + 11.4, 7.6)]) for k in range(2)])
        tile.put(props, _mix(skin.base, skin.dark, 0.25))
        tile.put(props * tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32.0 + 11.0, 5.0, k * 32.0 + 14.0, 11.0) for k in range(2)]), skin.light, 0.30)
        tile.put(body, stone)
        tile.tone((tile.noise(10, 3, 3) - 0.5) * 0.22 * (tile.alpha > 0))
        tile.put(body * (y < 0.9), stone_light, 0.8)
        tile.put(body * np.clip((y - lower + 1.6) / 1.6, 0, 1), stone_dark, 0.55)
        # The joint where two slabs meet, and a chipped corner at it.
        tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, 44.0 - 0.4, 0.0, 44.0 + 0.4, 7.0), _poly(p, dx, dy, [(42.6, 0.0), (44.0, 0.0), (44.0, 1.4)]))), stone_dark, 0.9)
        cracks = [(rng.uniform(0, 64), rng.uniform(1.2, 3.6)) for _ in range(4)]
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, yy), (x + 1.6, yy + 0.4), (x + 2.6, yy + 0.1)], 0.18) for x, yy in cracks]) * body, stone_dark, 0.55)
        lichen = [(rng.uniform(0, 64), rng.uniform(0.8, 3.6), rng.uniform(0.4, 1.0), rng.random() < 0.5) for _ in range(10)]
        for pale in (True, False):
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r, ry=r * 0.6) for x, yy, r, kind in lichen if kind == pale]) * body,
                     (226, 224, 206) if pale else _mix(skin.accent, stone, 0.45), 0.45)
        tile.put(np.clip(1.0 - (y - lower) / 3.0, 0, 1) * (y >= lower) * (1.0 - props), (0, 0, 0), 0.22)
    elif skin.oneway == "stone_step":
        # A step of a stair of Caral: a long block of stone, dressed flat on
        # its top and its front, set in clay. Its top edge is worn round by
        # feet, a joint is each thirty-two units, and a thin bed of clay is
        # under it.
        stone = _mix(skin.base, skin.light, 0.35)
        thick = 6.6
        body = (y < thick).astype(np.float32)
        tile.put(body, stone)
        tile.tone((tile.noise(8, 2, 3) - 0.5) * 0.18 * body)
        tile.put(body * (y < 0.8), _mix(stone, (255, 250, 236), 0.5), 0.85)
        tile.put(body * ((y >= 0.8) & (y < 1.8)), _mix(stone, (255, 250, 236), 0.2), 0.6)
        tile.put(body * np.clip((y - thick + 1.4) / 1.4, 0, 1), skin.dark, 0.45)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32.0 + 9.0 - 0.35, 0.0, k * 32.0 + 9.0 + 0.35, thick) for k in range(2)]), skin.dark, 0.8)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32.0 + 9.35, 0.0, k * 32.0 + 10.0, thick) for k in range(2)]), _mix(stone, (255, 250, 236), 0.4), 0.5)
        marks = [(rng.uniform(0, 64), rng.uniform(2.2, 5.6)) for _ in range(22)]
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, yy), (x + 0.5, yy + 0.7)], 0.2) for x, yy in marks]) * body, skin.dark, 0.30)
        bed = ((y >= thick) & (y < thick + 1.0)).astype(np.float32)
        tile.put(bed, skin.cap_colour)
        tile.put(bed * (y >= thick + 0.6), skin.dark, 0.4)
        tile.put(np.clip(1.0 - (y - thick - 1.0) / 3.0, 0, 1) * (y >= thick + 1.0), (0, 0, 0), 0.24)
    elif skin.oneway == "split_log":
        # A log split along its length, with its flat face up: a pale band
        # of split wood on top, with long splinters, and the round bark side
        # under it. Two logs meet each thirty-two units; there the
        # cut end of a log shows pale, and a stake holds the logs in place.
        bark, bark_dark = _mix(skin.base, (110, 82, 58), 0.5), _mix(skin.dark, (30, 22, 16), 0.4)
        wood, wood_light = (196, 156, 104), (232, 204, 158)
        thick = 6.4
        # The log is thickest at its middle and thinner at its two ends.
        lower = thick - 0.6 + 0.6 * np.cos(((tile.x - 38.0) % 32.0) / 32.0 * 2.0 * math.pi)
        body = np.clip((lower - y) * K * 0.5 + 0.5, 0, 1)
        tile.put(body, bark)
        cracks = np.clip(1.0 - np.abs(((y + (tile.noise(6, 2, 2) - 0.5) * 1.6) % 1.3) - 0.65) / 0.12, 0, 1) * body * (y > 1.6)
        tile.put(cracks, bark_dark, 0.45)
        tile.put(body * np.clip((y - 3.6) / 2.6, 0, 1), bark_dark, 0.55)
        face = body * (y < 1.6)
        tile.put(face, wood)
        tile.put(face * (y < 0.6), wood_light, 0.85)
        tile.put(face * np.clip(1.0 - np.abs(((tile.x + tile.noise(8, 2, 2) * 6.0) % 3.1) - 1.5) / 0.18, 0, 1), _mix(wood, bark_dark, 0.4), 0.45)
        tile.put(body * ((y >= 1.6) & (y < 2.0)), bark_dark, 0.7)
        for k in range(2):
            x0 = k * 32.0 + 22.0
            # The butt joint: a dark gap, and the pale cut end of the next log.
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 - 0.4, 0.0, x0 + 0.2, 7.0)) * body, bark_dark, 0.95)
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.2, 0.0, x0 + 1.2, 7.0)) * body, wood, 0.75)
            stake = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x0 - 9.0, 1.4), (x0 - 7.6, 1.4), (x0 - 7.8, 9.4), (x0 - 8.3, 10.6), (x0 - 8.8, 9.4)]))
            tile.put(stake, bark)
            tile.put(stake * (tile.x > x0 - 8.2), bark_dark, 0.5)
        tile.put(np.clip(1.0 - (y - lower) / 3.0, 0, 1) * (y >= lower), (0, 0, 0), 0.24)
    elif skin.oneway == "slate_slab":
        # A slab of dark slate, split thin along its layers. Its edge shows
        # the layers as fine lines, light and dark. The top is flat and lit,
        # the lower edge is ragged where the layers broke, and two slabs
        # meet each thirty-two units, the one a little over the other.
        slate, slate_dark, slate_light = (78, 84, 90), (36, 40, 44), (148, 156, 160)
        lower = 4.0 + tile.profile(10, 3)[None, :] * 1.8
        body = np.clip((lower - y) * K * 0.5 + 0.5, 0, 1)
        tile.put(body, slate)
        tile.tone((tile.noise(10, 3, 2) - 0.5) * 0.18 * (tile.alpha > 0))
        layers = np.clip(1.0 - np.abs(((y + (tile.noise(6, 2, 2) - 0.5) * 0.5) % 0.9) - 0.45) / 0.10, 0, 1) * body * (y > 0.9)
        tile.put(layers, slate_dark, 0.40)
        tile.put(body * (y < 0.8), slate_light, 0.85)
        tile.put(body * np.clip((y - lower + 1.2) / 1.2, 0, 1), slate_dark, 0.55)
        for k in range(2):
            x0 = k * 32.0 + 6.0
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 - 0.35, 0.0, x0 + 0.35, 6.0)) * body, slate_dark, 0.9)
            tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x0 + 0.35, 0.0), (x0 + 2.2, 0.0), (x0 + 0.35, 1.2)])), slate_dark, 0.5)
        moss = [(rng.uniform(0, 64), rng.uniform(1.4, 2.6)) for _ in range(3)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, -0.1, w, ry=0.6) for x, w in moss]), skin.cap_colour, 0.85)
        tile.put(np.clip(1.0 - (y - lower) / 3.0, 0, 1) * (y >= lower), (0, 0, 0), 0.22)
    elif skin.oneway == "granite_step":
        # A step of dressed granite: a long block with a flat top worn
        # smooth by feet and a flat front, speckled as granite is. A joint
        # is each thirty-two units, and it rests on a bed of small stones.
        stone = _mix(skin.base, skin.light, 0.25)
        thick = 6.4
        body = (y < thick).astype(np.float32)
        tile.put(body, stone)
        tile.tone((tile.noise(8, 2, 3) - 0.5) * 0.12 * body)
        tile.put(body * (y < 0.8), _mix(stone, (255, 250, 240), 0.55), 0.85)
        tile.put(body * ((y >= 0.8) & (y < 1.6)), _mix(stone, (255, 250, 240), 0.2), 0.6)
        tile.put(body * np.clip((y - thick + 1.4) / 1.4, 0, 1), skin.dark, 0.45)
        grains = [(rng.uniform(0, 64), rng.uniform(1.2, thick - 0.5), rng.uniform(0.18, 0.32)) for _ in range(70)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r) for x, yy, r in grains[::2]]), (44, 40, 40), 0.55)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r) for x, yy, r in grains[1::2]]), (240, 232, 220), 0.45)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32.0 + 13.0 - 0.3, 0.0, k * 32.0 + 13.0 + 0.3, thick) for k in range(2)]), skin.dark, 0.8)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32.0 + 13.3, 0.0, k * 32.0 + 13.9, thick) for k in range(2)]), _mix(stone, (255, 250, 240), 0.4), 0.5)
        bed = [(rng.uniform(0, 64), thick + rng.uniform(0.3, 0.9), rng.uniform(0.5, 1.0)) for _ in range(26)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r, ry=r * 0.6) for x, yy, r in bed]), _mix(skin.dark, skin.base, 0.35))
        tile.put(np.clip(1.0 - (y - thick - 1.2) / 3.0, 0, 1) * (y >= thick + 1.2), (0, 0, 0), 0.22)
    elif skin.oneway == "balustrade_walk":
        # A wooden walk by West Lake: a deck of planks with its edge beam,
        # and under the deck a balustrade of the Song kind, a low rail on
        # short posts. A post each sixteen units, with a round knob; between
        # two posts a row of short balusters, each thick in its middle, and
        # a rail along their feet. The wood is oiled and dark.
        wood, wood_dark, wood_light = (118, 82, 54), (52, 34, 24), (190, 150, 104)
        deck = (y < 3.2).astype(np.float32)
        tile.put(deck, wood)
        tile.tone((tile.noise(2, 12, 2) - 0.5) * 0.22 * deck)
        tile.put(deck * (y < 0.8), wood_light, 0.85)
        tile.put(deck * ((y >= 0.8) & (y < 1.4)), wood_light, 0.25)
        tile.put(deck * np.clip((y - 2.4) / 0.8, 0, 1), wood_dark, 0.55)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 0.3, 0.0, x + 0.3, 3.2) for x in (21.0, 53.0)]), wood_dark, 0.85)
        rail_top, rail_low = 3.2, 9.6
        balusters = [k * 16.0 + j * 3.2 + 4.8 for k in range(4) for j in range(3)]
        tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(x - 0.45, rail_top), (x + 0.45, rail_top), (x + 0.9, (rail_top + rail_low) * 0.5), (x + 0.45, rail_low), (x - 0.45, rail_low), (x - 0.9, (rail_top + rail_low) * 0.5)]) for x in balusters]), _mix(wood, wood_dark, 0.25))
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 0.7, rail_top, x - 0.2, rail_low) for x in balusters]), wood_light, 0.35)
        low = ((y >= rail_low) & (y < rail_low + 1.6)).astype(np.float32)
        tile.put(low, wood)
        tile.put(low * (y < rail_low + 0.5), wood_light, 0.5)
        tile.put(low * (y >= rail_low + 1.1), wood_dark, 0.6)
        posts = [k * 16.0 + 1.0 for k in range(4)]
        post = tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 1.3, 0.0, x + 1.3, rail_low + 3.0) for x in posts])
        tile.put(post, wood)
        tile.put(post * tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 1.3, 0.0, x - 0.6, rail_low + 3.0) for x in posts]), wood_light, 0.45)
        tile.put(post * tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x + 0.6, 0.0, x + 1.3, rail_low + 3.0) for x in posts]), wood_dark, 0.45)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, rail_low + 3.2, 1.2) for x in posts]), _mix(wood, wood_dark, 0.2))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.4, rail_low + 2.9, 0.45) for x in posts]), wood_light, 0.5)
        tile.put(post * tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 1.3, 0.8, x + 1.3, 1.4) for x in posts]), wood_dark, 0.5)
        tile.put(np.clip(1.0 - (y - rail_low - 1.6) / 3.0, 0, 1) * (y >= rail_low + 1.6) * (1.0 - post), (0, 0, 0), 0.20)
    elif skin.oneway == "engawa":
        # The edge of a veranda of a mansion of Heian-kyo: boards of cypress
        # laid along it, worn smooth and pale, and a thick edge beam under
        # them. Short posts each thirty-two units hold it up on round
        # stones, a thin tie beam joins them, and the dark space under the
        # floor shows between them.
        wood, wood_dark, wood_light = (170, 132, 92), (66, 46, 32), (230, 204, 160)
        floor = (y < 1.6).astype(np.float32)
        tile.put(floor, _mix(wood, wood_light, 0.35))
        tile.put(floor * (y < 0.7), wood_light, 0.85)
        beam = ((y >= 1.6) & (y < 5.4)).astype(np.float32)
        tile.put(beam, wood)
        tile.tone((tile.noise(2, 10, 2) - 0.5) * 0.18 * (tile.alpha > 0))
        grain = np.clip(1.0 - np.abs(((y + (tile.noise(3, 8, 2) - 0.5) * 2.0) % 1.2) - 0.6) / 0.10, 0.0, 1.0)
        tile.put(grain * beam, wood_dark, 0.20)
        tile.put(((y >= 1.6) & (y < 2.0)).astype(np.float32), wood_dark, 0.6)
        tile.put(beam * np.clip((y - 4.6) / 0.8, 0, 1), wood_dark, 0.55)
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 40.0 - 0.3, 1.6, 40.0 + 0.3, 5.4)), wood_dark, 0.8)
        posts = [k * 32.0 + 12.0 for k in range(2)]
        tie = ((y >= 8.2) & (y < 9.4)).astype(np.float32)
        tile.put(tie, _mix(wood, wood_dark, 0.45))
        tile.put(tie * (y < 8.6), wood, 0.6)
        post = tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 1.6, 5.4, x + 1.6, 12.6) for x in posts])
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 1.6, 5.4, x + 1.6, 6.6) for x in posts], blur=0.3), (0, 0, 0), 0.4)
        tile.put(post, _mix(wood, wood_dark, 0.15))
        tile.put(post * tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 1.6, 5.4, x - 0.8, 12.6) for x in posts]), wood_light, 0.35)
        tile.put(post * tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x + 0.8, 5.4, x + 1.6, 12.6) for x in posts]), wood_dark, 0.45)
        stones = tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, 13.4, 3.0, ry=1.5) for x in posts])
        tile.put(stones, (120, 116, 108))
        tile.put(stones * tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.6, 12.8, 1.8, ry=0.6) for x in posts]), (180, 176, 166), 0.6)
        tile.put(np.clip(1.0 - (y - 5.4) / 3.0, 0, 1) * (y >= 5.4) * (1.0 - post) * (1.0 - stones) * (1.0 - tie), (0, 0, 0), 0.24)
    elif skin.oneway == "terrace_step":
        # A step of the granite terrace of a palace hall: a long block with
        # a round nose that is worn smooth, a face dressed with fine
        # slanted tool marks, and a joint each thirty-two units. Under the
        # nose the face is in shade.
        stone = _mix(skin.base, skin.light, 0.30)
        thick = 6.8
        body = (y < thick).astype(np.float32)
        tile.put(body, stone)
        tile.tone((tile.noise(8, 2, 3) - 0.5) * 0.10 * body)
        nose = body * (y < 2.0)
        tile.put(nose * np.clip(1.0 - y / 1.6, 0, 1), _mix(stone, (255, 252, 244), 0.6), 0.9)
        tile.put(nose * np.clip((y - 1.2) / 0.8, 0, 1), skin.dark, 0.35)
        tile.put(body * ((y >= 2.0) & (y < 2.6)), skin.dark, 0.35)
        face = body * (y >= 2.6) * (y < thick - 0.8)
        hatch = np.clip(1.0 - np.abs(((tile.x + y) % 1.2) - 0.6) / 0.15, 0.0, 1.0)
        tile.put(face * hatch, skin.dark, 0.18)
        tile.put(body * np.clip((y - thick + 1.2) / 1.2, 0, 1), skin.dark, 0.45)
        grains = [(rng.uniform(0, 64), rng.uniform(0.6, thick - 0.4), rng.uniform(0.16, 0.28)) for _ in range(60)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r) for x, yy, r in grains[::2]]), (52, 48, 46), 0.45)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r) for x, yy, r in grains[1::2]]), (244, 238, 228), 0.40)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32.0 + 22.0 - 0.3, 0.0, k * 32.0 + 22.0 + 0.3, thick) for k in range(2)]), skin.dark, 0.8)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32.0 + 22.3, 0.0, k * 32.0 + 22.9, thick) for k in range(2)]), _mix(stone, (255, 252, 244), 0.4), 0.5)
        tile.put(np.clip(1.0 - (y - thick) / 3.0, 0, 1) * (y >= thick), (0, 0, 0), 0.24)
    elif skin.oneway == "bamboo_walk":
        # A walk of bamboo over the mud of the bank, as the villages of the
        # delta build them: two thick poles laid side by side, the near one
        # a little lower, with a node each ten units and a shine along the
        # top. A pair of crossed bamboo legs each thirty-two units holds it
        # up, lashed to the poles and at their crossing with cord.
        cane, cane_dark, cane_light = (176, 158, 92), (86, 74, 42), (232, 222, 156)
        legs = [k * 32.0 + 16.0 for k in range(2)]
        leg_lines = [[(x - 4.6, 4.0), (x + 4.0, 14.6)] for x in legs] + [[(x + 4.6, 4.0), (x - 4.0, 14.6)] for x in legs]
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 1.3) for pts in leg_lines]), _mix(cane, cane_dark, 0.45))
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(a[0] - 0.4, a[1]), (b[0] - 0.4, b[1])], 0.35) for a, b in leg_lines]), cane, 0.6)
        # The legs go into the mud: they fade out at the foot of the picture.
        tile.alpha *= np.clip((15.6 - y) / 2.0, 0.0, 1.0)
        # The far pole shows as a thin strip over the near one.
        far = (y < 1.6).astype(np.float32)
        tile.put(far, _mix(cane, cane_dark, 0.30))
        tile.put(far * np.clip(1.0 - y / 0.6, 0, 1), cane_light, 0.55)
        pole = ((y >= 1.3) & (y < 5.4)).astype(np.float32)
        tile.put(pole, cane)
        tile.tone((tile.noise(3, 2, 2) - 0.5) * 0.16 * pole)
        tile.put(pole * np.clip(1.0 - np.abs(y - 2.3) / 0.6, 0, 1), cane_light, 0.75)
        tile.put(pole * np.clip((y - 4.4) / 1.0, 0, 1), cane_dark, 0.55)
        nodes = [k * 12.8 + 5.0 for k in range(5)]
        tile.put(pole * tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 0.30, 1.3, x + 0.30, 5.4) for x in nodes]), cane_dark, 0.70)
        tile.put(pole * tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x + 0.30, 1.3, x + 0.90, 5.4) for x in nodes]), cane_light, 0.40)
        cord = (120, 92, 58)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x - 1.6 + k * 0.8, 0.2), (x - 1.0 + k * 0.8, 5.2)], 0.30) for x in legs for k in range(4)]), cord)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, 9.3, 0.9) for x in legs]), cord)
        tile.put(np.clip(1.0 - (y - 5.4) / 3.0, 0, 1) * (y >= 5.4) * (tile.alpha > 0.5), (0, 0, 0), 0.18)
    elif skin.oneway == "ghat_step":
        # A step of a ghat on the Hooghly, where people go down to the
        # river: a long slab of pale sandstone with a rounded nose worn
        # smooth by feet, a joint each twenty-one units, and below the nose
        # the face that the river wets, dark at its foot with a thin line
        # of green weed.
        stone, stone_dark, stone_light = (204, 182, 156), (102, 86, 72), (240, 228, 206)
        thick = 7.0
        body = (y < thick).astype(np.float32)
        tile.put(body, stone)
        tile.tone((tile.noise(10, 2, 3) - 0.5) * 0.14 * body)
        tile.put(body * np.clip(1.0 - y / 1.4, 0, 1), stone_light, 0.85)
        tile.put(body * ((y >= 1.6) & (y < 2.2)), stone_dark, 0.40)
        wet = body * np.clip((y - 3.4) / 2.6, 0, 1)
        tile.put(wet, _mix(stone_dark, (70, 76, 70), 0.4), 0.65)
        tile.put(body * np.clip(1.0 - np.abs(y - 4.6) / 0.35, 0, 1) * np.clip(tile.noise(16, 1, 2) * 2.0 - 0.4, 0, 1), (90, 122, 70), 0.55)
        joints = [3.0, 24.3, 45.6]
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 0.3, 0.0, x + 0.3, thick) for x in joints]), stone_dark, 0.75)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x + 0.3, 0.0, x + 0.8, 3.0) for x in joints]), stone_light, 0.45)
        pits = [(rng.uniform(0, 64), rng.uniform(1.0, 3.2), rng.uniform(0.15, 0.3)) for _ in range(30)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r) for x, yy, r in pits]), stone_dark, 0.40)
        tile.put(np.clip(1.0 - (y - thick) / 3.0, 0, 1) * (y >= thick), (0, 0, 0), 0.24)
    elif skin.oneway == "hall_step":
        # A step at the door of Curzon Hall: a slab of pale grey sandstone
        # with a chamfered nose, on a riser of two courses of red brick, the
        # same brick as the hall.
        stone, stone_dark, stone_light = (206, 200, 186), (112, 106, 98), (244, 240, 230)
        slab = (y < 3.4).astype(np.float32)
        tile.put(slab, stone)
        tile.tone((tile.noise(10, 2, 3) - 0.5) * 0.10 * slab)
        tile.put(slab * np.clip(1.0 - y / 1.0, 0, 1), stone_light, 0.85)
        tile.put(slab * ((y >= 2.6) & (y < 3.4)), stone_dark, 0.45)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 0.25, 0.0, x + 0.25, 3.4) for x in (10.0, 42.0)]), stone_dark, 0.7)
        for row in range(2):
            y0 = 3.4 + row * 3.0
            offset = 4.0 if row else 0.0
            for k in range(8):
                x0 = k * 8.0 + offset
                tone = rng.uniform(-0.12, 0.12)
                colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.5)
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.3, y0 + 0.3, x0 + 8.0 - 0.3, y0 + 3.0 - 0.3)), colour)
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.3, y0 + 0.3, x0 + 7.7, y0 + 0.8)), skin.light, 0.30)
            tile.put(((y >= y0) & (y < y0 + 0.3)).astype(np.float32), _mix(skin.dark, (200, 190, 170), 0.4))
        tile.put(((y >= 3.4) & (y < 4.2)).astype(np.float32), (0, 0, 0), 0.30)
        tile.put(np.clip(1.0 - (y - 9.4) / 3.0, 0, 1) * (y >= 9.4), (0, 0, 0), 0.24)
    elif skin.oneway == "limestone_shelf":
        # A shelf of limestone that stands out of the rock. Its top is flat
        # and lit, with a few tufts of moss on it. Its lower side is
        # rough and has short drips of stone (small stalactites) that hang
        # from it, as the water left them.
        stone, stone_dark, stone_light = skin.base, _mix(skin.base, skin.dark, 0.45), _mix(skin.light, (255, 252, 240), 0.3)
        lower = 4.4 + tile.profile(8, 3)[None, :] * 1.8
        drips = [(rng.uniform(0, 64), rng.uniform(1.2, 2.4), rng.uniform(1.6, 5.0)) for _ in range(9)]
        teeth = tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(x - w * 0.5, 4.0), (x + w * 0.5, 4.0), (x + 0.15, 4.0 + h), (x - 0.15, 4.0 + h)]) for x, w, h in drips])
        tile.put(teeth, stone_dark)
        tile.put(teeth * np.clip(1.0 - (y - 4.0) / 3.0, 0, 1), stone, 0.5)
        body = np.clip((lower - y) * K * 0.5 + 0.5, 0, 1)
        tile.put(body, stone)
        tile.tone((tile.noise(10, 3, 3) - 0.5) * 0.20 * (tile.alpha > 0))
        tile.put(body * (y < 0.9), stone_light, 0.85)
        tile.put(body * np.clip((y - lower + 1.6) / 1.6, 0, 1), stone_dark, 0.55)
        pits = [(rng.uniform(0, 64), rng.uniform(1.4, 3.4), rng.uniform(0.3, 0.6)) for _ in range(8)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r, ry=r * 0.7) for x, yy, r in pits]) * body, stone_dark, 0.7)
        moss = [(rng.uniform(0, 64), rng.uniform(1.2, 2.6)) for _ in range(5)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, 0.2, w, ry=0.7) for x, w in moss]), skin.cap_colour, 0.95)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.3, -0.1, w * 0.6, ry=0.35) for x, w in moss]), _mix(skin.cap_colour, skin.accent, 0.5), 0.8)
        tile.put(np.clip(1.0 - (y - lower) / 3.0, 0, 1) * (y >= lower) * (1.0 - teeth), (0, 0, 0), 0.22)
    elif skin.oneway == "split_bamboo":
        # A walkway over a paddy: halves of big bamboo laid side by side,
        # their round outer skin up, on cross poles that are lashed with
        # rattan each thirty-two units. The nodes of the halves do not line
        # up, because each half is cut from its own cane.
        cane, cane_dark, cane_light = (184, 176, 102), (104, 96, 52), (232, 226, 164)
        top = ((y >= 0.0) & (y < 3.2)).astype(np.float32)
        tile.put(top, cane)
        tile.put(top * np.clip(1.0 - np.abs(y - 0.7) / 0.6, 0, 1), cane_light, 0.7)
        tile.put(top * np.clip((y - 1.8) / 1.4, 0, 1), cane_dark, 0.55)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 0.3, 0.0, x + 0.3, 3.2) for x in (5.0, 17.0, 26.0, 39.0, 50.0, 59.0)]) * top, cane_dark, 0.85)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x + 0.3, 0.0, x + 0.8, 3.2) for x in (5.0, 17.0, 26.0, 39.0, 50.0, 59.0)]) * top, cane_light, 0.5)
        tile.put(((y >= 3.0) & (y < 3.6)).astype(np.float32), cane_dark, 0.9)
        poles = tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 32.0 + 12.0, 5.2, 1.9) for k in range(2)])
        tile.put(poles, _mix(cane, cane_dark, 0.35))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 32.0 + 12.0, 5.2, 1.1) for k in range(2)]), cane_dark, 0.8)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 32.0 + 11.5, 4.6, 0.5) for k in range(2)]), cane_light, 0.6)
        rattan = (150, 104, 60)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(k * 32.0 + 9.6 + j * 1.2, -0.2), (k * 32.0 + 10.4 + j * 1.2, 6.8)], 0.4) for k in range(2) for j in range(4)]), rattan)
        tile.put(np.clip(1.0 - (y - 3.6) / 3.0, 0, 1) * (y >= 3.6) * (1.0 - poles), (0, 0, 0), 0.24)
    elif skin.oneway == "plank_walk":
        # A walkway over the mud: a thick plank seen from its side, butt
        # joints with pegs of wood, and under it the round ends of the cross
        # beams it lies on, each lashed to it with rattan.
        wood, wood_dark, wood_light = _mix(skin.base, (120, 88, 58), 0.4), skin.dark, _mix(skin.light, (220, 190, 140), 0.3)
        thick = 4.0
        top = (y < thick).astype(np.float32)
        tile.put(top, wood)
        tile.tone((tile.noise(3, 10, 2) - 0.5) * 0.28 * (tile.alpha > 0))
        tile.put(top * (y < 0.8), wood_light, 0.8)
        tile.put(top * np.clip((y - thick + 1.0) / 1.0, 0, 1), wood_dark, 0.6)
        joints = (5.0, 26.0, 47.0)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 0.3, 0.0, x + 0.3, thick) for x in joints]), wood_dark, 0.85)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x + sd, 2.0, 0.45) for x in joints for sd in (-1.6, 1.6)]), wood_light, 0.7)
        beams = [k * 16.0 + 12.0 for k in range(4)]
        ends = tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, thick + 1.9, 2.0) for x in beams])
        tile.put(ends, _mix(wood, wood_dark, 0.3))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, thick + 1.9, 1.2) for x in beams]), _mix(wood, wood_light, 0.35))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, thick + 1.9, 0.5) for x in beams]), wood_dark, 0.6)
        rattan = (162, 124, 74)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x - 2.2 + j * 1.1, -0.2), (x - 1.4 + j * 1.1, thick + 3.6)], 0.4) for x in beams[::2] for j in range(3)]), rattan)
        tile.put(np.clip(1.0 - (y - thick - 0.4) / 3.0, 0, 1) * (y >= thick + 0.4) * (1.0 - ends), (0, 0, 0), 0.24)
    elif skin.oneway == "andesite_step":
        # A step of andesite: a long block, flat and worn on its top, with a
        # round moulding along its front and a groove under the moulding.
        # A joint is each sixteen units, and moss grows in a few joints.
        stone = _mix(skin.base, skin.light, 0.30)
        thick = 6.4
        body = (y < thick).astype(np.float32)
        tile.put(body, stone)
        tile.tone((tile.noise(8, 2, 3) - 0.5) * 0.18 * body)
        tile.put(body * (y < 0.8), _mix(stone, (255, 250, 236), 0.5), 0.85)
        tile.put(body * np.clip(1.0 - np.abs(y - 1.9) / 0.7, 0, 1), _mix(stone, (255, 250, 236), 0.30), 0.7)
        tile.put(body * ((y >= 2.6) & (y < 3.2)), skin.dark, 0.65)
        tile.put(body * np.clip((y - thick + 1.4) / 1.4, 0, 1), skin.dark, 0.45)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 16.0 + 7.0 - 0.3, 0.0, k * 16.0 + 7.0 + 0.3, thick) for k in range(4)]), skin.dark, 0.8)
        holes = [(rng.uniform(0, 64), rng.uniform(3.6, 5.6), rng.uniform(0.2, 0.4)) for _ in range(16)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r) for x, yy, r in holes]) * body, skin.dark, 0.6)
        moss = [k * 16.0 + 7.0 for k in range(4) if rng.random() < 0.6]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, 0.2, 1.4, ry=0.8) for x in moss]), skin.accent, 0.9)
        tile.put(np.clip(1.0 - (y - thick) / 3.0, 0, 1) * (y >= thick), (0, 0, 0), 0.26)
    elif skin.oneway == "sandstone_lintel":
        # A lintel of grey-pink sandstone: a beam with a flat lit top and a
        # carved band on its face, a vine that winds along it with small
        # leaves, as on the lintels of the Khmer. A joint is each thirty-two
        # units.
        stone = skin.cap_colour
        thick = 6.2
        body = (y < thick).astype(np.float32)
        tile.put(body, stone)
        tile.tone((tile.noise(8, 2, 3) - 0.5) * 0.16 * body)
        tile.put(body * (y < 0.8), _mix(stone, (255, 246, 236), 0.5), 0.85)
        tile.put(body * ((y >= 1.3) & (y < 1.7)), skin.dark, 0.5)
        tile.put(body * ((y >= 4.7) & (y < 5.1)), skin.dark, 0.5)
        vine = [(x, 3.2 + 0.9 * math.sin(x * math.pi / 8.0)) for x in np.linspace(-1.0, 65.0, 67)]
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, vine, 0.45)), _mix(stone, skin.dark, 0.5))
        leaves = [(k * 8.0 + 4.0, 3.2 + (0.9 if k % 2 == 0 else -0.9)) for k in range(8)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 0.9, ry=0.55) for x, yy in leaves]), _mix(stone, skin.dark, 0.35))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.2, yy - 0.2, 0.4, ry=0.25) for x, yy in leaves]), _mix(stone, (255, 246, 236), 0.4))
        tile.put(body * np.clip((y - thick + 1.2) / 1.2, 0, 1), skin.dark, 0.45)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32.0 + 22.0 - 0.3, 0.0, k * 32.0 + 22.0 + 0.3, thick) for k in range(2)]), skin.dark, 0.8)
        tile.put(body * np.clip((tile.noise(12, 2, 2) - 0.70) * 6.0, 0.0, 1.0), (70, 66, 60), 0.30)
        tile.put(np.clip(1.0 - (y - thick) / 3.0, 0, 1) * (y >= thick), (0, 0, 0), 0.26)
    else:  # slab
        stone = _mix(skin.base, skin.light, 0.45)
        tile.put((y < 6.4).astype(np.float32), stone)
        tile.tone((tile.noise(6, 3, 3) - 0.5) * 0.16 * (tile.alpha > 0))
        tile.put((y < 0.8).astype(np.float32), _mix(stone, (255, 255, 255), 0.5))
        tile.put(((y >= 5.5) & (y < 6.4)).astype(np.float32), skin.dark, 0.7)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32 - 0.3, 0, k * 32 + 0.3, 6.4) for k in range(3)]), skin.dark, 0.7)
        corbels = tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(k * 32 + 12, 6.4), (k * 32 + 20, 6.4), (k * 32 + 18, 10.5), (k * 32 + 14, 10.5)]) for k in range(2)])
        tile.put(corbels, _mix(skin.base, skin.dark, 0.3))
        tile.put(np.clip(1.0 - (y - 6.4) / 3.0, 0, 1) * (y >= 6.4) * (1.0 - corbels), (0, 0, 0), 0.22)
    del rng
    return tile.publish()


PARTS: dict[str, Callable[[Skin], Image.Image]] = {
    "fill": fill,
    "breakable_brick": breakable_brick,
    "cap": cap,
    "under": under,
    "side": side,
    "oneway": oneway,
}


def mockup(skin: Skin, parts: dict[str, Image.Image], scale: int = 2) -> Image.Image:
    """A small made-up room in the skin, to look at without the game: a
    floor, a block in the air and a one-way platform, on the mean colour of
    a dark room."""
    w, h = 384, 216
    px = PX_PER_UNIT
    out = Image.new("RGBA", (w * px, h * px), (*_mix(skin.dark, (20, 24, 34), 0.55), 255))

    def lay(part: str, x0: float, y0: float, bw: float, bh: float, flip: bool = False) -> None:
        tile = parts[part]
        if flip:
            tile = tile.transpose(Image.FLIP_LEFT_RIGHT)
        strip = Image.new("RGBA", (int(bw * px), int(bh * px)))
        for tx in range(0, strip.width, tile.width):
            for ty in range(0, strip.height, tile.height):
                strip.paste(tile, (tx, ty))
        out.alpha_composite(strip, (int(x0 * px), int(y0 * px)))

    for x0, y0, bw, bh in ((0, 160, 384, 56), (200, 70, 120, 40), (0, 40, 40, 120)):
        lay("fill", x0, y0, bw, bh)
        lay("side", x0, y0, SIDE[0], bh)
        lay("side", x0 + bw - SIDE[0], y0, SIDE[0], bh, flip=True)
        if y0 + bh < h:
            lay("under", x0, y0 + bh - UNDER_EDGE, bw, UNDER[1])
        lay("cap", x0, y0 - CAP_SURFACE, bw, CAP[1])
    lay("oneway", 70, 110, 96, 16)
    return out.resize((out.width * scale // px, out.height * scale // px), Image.LANCZOS)
