"""The scenes of the hub and of the fights: the station, the arena, the eclipse."""

from __future__ import annotations

import numpy as np

from .artkit import Art, mix, polar, scale, smoothstep
from .parts import HORIZON, cloud_mask, fog, haze, lamps, solid, stars, vignette, window_grid

# ---------------------------------------------------------------------------
# The hub: a station city at night
# ---------------------------------------------------------------------------

HUB = {
    "zenith": (9, 11, 38),
    "mid": (28, 32, 88),
    "horizon": (98, 78, 156),
    "glow": (190, 200, 255),
    "warm": (255, 206, 140),
    "city": (14, 16, 46),
    "city_light": (58, 60, 124),
    "accent": (134, 112, 226),
}


def hub(layer_key: str, art: Art) -> np.ndarray:
    p = HUB
    planet = (0.27, 0.40)
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["zenith"]), (0.34, p["mid"]), (HORIZON, p["horizon"]), (0.76, p["mid"]), (1.0, p["zenith"])]))
        art.light(layer, cloud_mask(art, "nebula", 0.38, 0.22, cells=2.5, cover=0.55, soft=0.4, stretch=1.6), p["accent"], 0.30)
        stars(art, layer, 560, (226, 232, 255), HORIZON - 0.03)
        # A planet with rings: the rings go behind it and in front of it.
        r = 0.072
        back, pen = art.drawing()
        for k, w in ((1.9, 0.006), (2.25, 0.003)):
            pen.draw.ellipse([(planet[0] - r * k) * art.n, (planet[1] - r * k * 0.26) * art.n, (planet[0] + r * k) * art.n, (planet[1] + r * k * 0.26) * art.n], outline=255, width=int(w * art.n))
        rings = art.mask_of(back, blur=0.3)
        art.light(layer, rings, p["glow"], 0.55)
        disc, pen = art.drawing()
        pen.ellipse(*planet, r)
        mask = art.mask_of(disc)
        bands = art.noise("planet bands", cells=14.0, octaves=3, stretch=14.0)
        face = art.flat(mix(p["accent"], p["warm"], 0.35)) * (0.62 + 0.5 * bands)[:, :, None]
        art.put(layer, mask, face)
        art.shade(layer, mask * smoothstep(-0.2, 0.9, (art.u - planet[0]) / r * 0.8 + (art.v - planet[1]) / r * 0.5), 0.72)
        art.light(layer, rings * (art.v > planet[1]), p["glow"], 0.6)
        art.light(layer, art.spot(*planet, r * 3.2, 2.2), p["accent"], 0.3)
        art.light(layer, art.band(HORIZON, 0.09, 2.0), p["horizon"], 0.3)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        rng = art.rand("skyline")
        image, pen = art.drawing()
        cool, cool_pen = art.drawing()
        warm, warm_pen = art.drawing()
        tips = []
        u = -0.02
        while u < 1.02:
            w = rng.uniform(0.03, 0.075)
            top = HORIZON - rng.uniform(0.05, 0.26)
            pen.rect(u, top, u + w, 1.0)
            if rng.random() < 0.5:
                pen.rect(u + w * 0.2, top - 0.02, u + w * 0.8, top)
            if rng.random() < 0.35:
                pen.rect(u + w * 0.5 - 0.001, top - 0.07, u + w * 0.5 + 0.001, top)
                tips.append((u + w * 0.5, top - 0.07, 0.002))
            window_grid(warm_pen if rng.random() < 0.55 else cool_pen, rng, u + 0.004, top + 0.01, u + w - 0.004, HORIZON + 0.06, 0.0095, 0.013, rng.uniform(0.2, 0.55))
            u += w + rng.uniform(-0.006, 0.014)
        # The spire of the station, with its rings.
        cu = 0.66
        pen.poly([(cu - 0.016, 1.0), (cu - 0.008, 0.30), (cu, 0.24), (cu + 0.008, 0.30), (cu + 0.016, 1.0)])
        for v, w in ((0.36, 0.034), (0.43, 0.026)):
            pen.ellipse(cu, v, w, 0.006)
        tips.append((cu, 0.24, 0.0028))
        mask = art.mask_of(image)
        layer = solid(art, mask, mix(p["city_light"], p["horizon"], 0.3), p["city"], HORIZON - 0.3, HORIZON + 0.06, None)
        art.light(layer, art.rim(mask, 0.003, 0.003, 0.5) * mask, p["glow"], 0.20)
        art.light(layer, art.mask_of(warm, blur=0.3) * mask, p["warm"], 0.62)
        art.light(layer, art.mask_of(cool, blur=0.3) * mask, p["glow"], 0.50)
        lamps(art, layer, tips, (255, 120, 120), halo=4.0, strength=0.9)
        haze(art, layer, p["horizon"], 0.34, HORIZON + 0.04)
        return layer
    if layer_key == "near_background":
        rng = art.rand("station")
        image, pen = art.drawing()
        # A truss across the top of the view.
        top, bottom = 0.315, 0.365
        pen.rect(0.0, top, 1.0, top + 0.008)
        pen.rect(0.0, bottom, 1.0, bottom + 0.008)
        for k in range(21):
            a, b = k / 20.0, (k + 1) / 20.0
            pen.line([(a, bottom + 0.004), ((a + b) * 0.5, top + 0.004), (b, bottom + 0.004)], 0.0032)
        # Masts with dishes, and a dome.
        lights = []
        for u, h in ((0.14, 0.26), (0.86, 0.20)):
            pen.rect(u - 0.004, 0.69 - h, u + 0.004, 1.0)
            pen.line([(u, 0.69 - h * 0.5), (u - 0.03, 0.69)], 0.002)
            pen.line([(u, 0.69 - h * 0.5), (u + 0.03, 0.69)], 0.002)
            pen.draw.pieslice([(u - 0.045) * art.n, (0.69 - h - 0.05) * art.n, (u + 0.045) * art.n, (0.69 - h + 0.04) * art.n], 20, 160, fill=255)
            pen.line([(u, 0.69 - h), (u + 0.012, 0.69 - h - 0.045)], 0.002)
            lights.append((u + 0.012, 0.69 - h - 0.047, 0.003))
        cu = 0.44
        pen.draw.pieslice([(cu - 0.10) * art.n, (0.69 - 0.085) * art.n, (cu + 0.10) * art.n, (0.69 + 0.085) * art.n], 180, 360, fill=255)
        for k in range(1, 6):
            a = 180 + k * 30
            pen.line([(cu, 0.69), polar(cu, 0.69, 0.10, a)], 0.0016, value=120)
        pen.rect(cu - 0.004, 0.57, cu + 0.004, 0.61)
        lights.append((cu, 0.568, 0.003))
        # A rail along the walk, with lamp posts.
        pen.rect(0.0, 0.665, 1.0, 0.669)
        for k in range(50):
            pen.rect(k / 50.0, 0.665, k / 50.0 + 0.0012, 0.69)
        posts = []
        for u in (0.27, 0.62, 0.75, 0.96):
            pen.rect(u - 0.002, 0.60, u + 0.002, 0.69)
            pen.rect(u - 0.008, 0.596, u + 0.008, 0.602)
            posts.append((u, 0.607, 0.0045))
        pen.rect(0.0, 0.69, 1.0, 1.0)
        mask = art.mask_of(image)
        layer = solid(art, mask, mix(p["city"], p["city_light"], 0.45), scale(p["city"], 0.8), 0.28, 0.72, "station metal", 0.06)
        art.light(layer, art.rim(mask, 0.003, 0.003, 0.4) * mask, p["glow"], 0.34)
        art.shade(layer, art.rim(mask, -0.004, -0.004, 1.2) * mask, 0.28)
        lamps(art, layer, posts, p["warm"], halo=7.0, strength=1.0)
        lamps(art, layer, lights, (255, 120, 120), halo=4.0, strength=0.9)
        haze(art, layer, p["mid"], 0.12, 0.72)
        return layer
    layer = art.blank()
    art.put(layer, fog(art, "city haze", 0.68, 0.16), p["accent"], 0.30)
    vignette(art, layer, p["zenith"], 0.34)
    return layer


# ---------------------------------------------------------------------------
# The arena: spires under a black sun
# ---------------------------------------------------------------------------

BOSS = {
    "black": (14, 4, 12),
    "deep": (50, 10, 28),
    "blood": (132, 26, 42),
    "fire": (255, 112, 72),
    "hot": (255, 212, 152),
    "rock": (18, 6, 14),
    "rock_light": (88, 26, 40),
}


def boss(layer_key: str, art: Art) -> np.ndarray:
    p = BOSS
    sun = (0.50, 0.405)
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["black"]), (0.30, p["deep"]), (HORIZON, p["blood"]), (0.78, p["deep"]), (1.0, p["black"])]))
        # The black sun: a ring of fire, and rays from it through the cloud.
        art.light(layer, art.spot(*sun, 0.50, 2.2), p["fire"], 0.55)
        rays, pen = art.drawing()
        rng = art.rand("rays")
        for k in range(18):
            a = k * 20.0 + rng.uniform(-6, 6)
            w = rng.uniform(2.0, 5.0)
            pen.poly([sun, polar(*sun, 0.7, a - w), polar(*sun, 0.7, a + w)], rng.randint(90, 200))
        art.light(layer, art.mask_of(rays, blur=7.0) * art.spot(*sun, 0.6, 1.2), p["fire"], 0.30)
        art.light(layer, art.spot(*sun, 0.13, 3.0), p["hot"], 0.95)
        disc, pen = art.drawing()
        pen.ellipse(*sun, 0.072)
        art.put(layer, art.mask_of(disc, blur=0.5), p["black"])
        art.shade(layer, cloud_mask(art, "ash cloud", 0.34, 0.2, cells=3.0, cover=0.55, soft=0.3, stretch=4.0) * (1.0 - art.spot(*sun, 0.2, 1.0)), 0.50)
        art.shade(layer, cloud_mask(art, "low ash", 0.56, 0.08, cells=4.0, cover=0.5, soft=0.3, stretch=6.0), 0.30)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        rng = art.rand("spires")
        range_, _ = art.ridge("spire range", HORIZON + 0.02, 0.14, cells=10.0, octaves=3, sharp=1.0)
        image, pen = art.drawing()
        for _ in range(11):
            u = rng.choice([rng.uniform(0.0, 0.38), rng.uniform(0.62, 1.0)])
            h, w = rng.uniform(0.16, 0.34), rng.uniform(0.012, 0.024)
            lean = rng.uniform(-0.015, 0.015)
            pen.poly([(u - w, HORIZON + 0.05), (u + lean - w * 0.3, HORIZON - h * 0.6), (u + lean, HORIZON - h), (u + lean + w * 0.4, HORIZON - h * 0.55), (u + w, HORIZON + 0.05)])
        mask = np.maximum(range_, art.mask_of(image))
        layer = solid(art, mask, mix(p["rock_light"], p["blood"], 0.3), p["rock"], HORIZON - 0.3, HORIZON + 0.08, "spire rock", 0.10)
        toward = np.sign(sun[0] - art.u)
        art.light(layer, (art.rim(mask, 0.004, 0.002, 0.6) * (toward < 0) + art.rim(mask, -0.004, 0.002, 0.6) * (toward > 0)) * mask, p["fire"], 0.5)
        haze(art, layer, p["blood"], 0.32, HORIZON + 0.06)
        return layer
    if layer_key == "near_background":
        rng = art.rand("arena")
        image, pen = art.drawing()
        cloth, cloth_pen = art.drawing()
        # The wall of the arena at each side: arches, the top broken away.
        for u0, u1 in ((-0.02, 0.30), (0.70, 1.02)):
            span = (u1 - u0) / 3.0
            pen.rect(u0, 0.40, u1, 1.0)
            for k in range(3):
                cu = u0 + span * (k + 0.5)
                r = span * 0.34
                pen.rect(cu - r, 0.52, cu + r, 1.0, value=0)
                pen.ellipse(cu, 0.52, r, r, value=0)
            # The top is broken away to the middle of the arena.
            inner = u1 if u0 < 0.5 else u0
            away = -1 if u0 < 0.5 else 1
            pts = [(inner + away * -0.01, 0.38)]
            for k in range(7):
                pts.append((inner + away * k * 0.03, 0.62 - k * 0.034 + rng.uniform(-0.012, 0.012)))
            pts.append((inner + away * 0.19, 0.38))
            pen.poly(pts, value=0)
        # Broken columns between them.
        for u in (0.36, 0.44, 0.585, 0.645):
            top = rng.uniform(0.50, 0.62)
            pen.rect(u - 0.013, top, u + 0.013, 1.0)
            pen.poly([(u - 0.013, top), (u + 0.013, top - 0.018), (u + 0.013, top)])
            pen.rect(u - 0.018, 0.675, u + 0.018, 0.69)
        # Chains from above, and banners on the wall.
        for u in (0.33, 0.50, 0.67):
            end = rng.uniform(0.36, 0.48)
            v = 0.0
            while v < end:
                pen.ellipse(u, v, 0.0034, 0.006)
                v += 0.0102
            pen.ring(u, end + 0.012, 0.012, 0.0036)
        for u in (0.085, 0.19, 0.81, 0.915):
            cloth_pen.poly([(u - 0.016, 0.41), (u + 0.016, 0.41), (u + 0.016, 0.50), (u + 0.006, 0.485), (u, 0.515), (u - 0.007, 0.49), (u - 0.016, 0.505)])
        # Spikes along the ground.
        spikes, _ = art.ridge("spikes", 0.695, 0.022, cells=40.0, octaves=2, sharp=1.0)
        mask = np.maximum(art.mask_of(image), spikes)
        layer = solid(art, mask, mix(p["rock"], p["rock_light"], 0.45), scale(p["rock"], 0.8), 0.34, 0.74, "arena stone", 0.10)
        toward = np.sign(sun[0] - art.u)
        art.light(layer, (art.rim(mask, 0.004, 0.002, 0.4) * (toward < 0) + art.rim(mask, -0.004, 0.002, 0.4) * (toward > 0)) * mask, p["fire"], 0.5)
        art.put(layer, art.mask_of(cloth), mix(p["blood"], p["fire"], 0.25))
        art.shade(layer, art.mask_of(cloth) * smoothstep(0.40, 0.52, art.v), 0.4)
        haze(art, layer, p["deep"], 0.12, 0.73)
        return layer
    layer = art.blank()
    art.put(layer, fog(art, "red mist", 0.69, 0.17), p["blood"], 0.36)
    vignette(art, layer, p["black"], 0.42)
    return layer


# ---------------------------------------------------------------------------
# The eclipse: standing stones under a dark sun and its lights
# ---------------------------------------------------------------------------

ECLIPSE = {
    "black": (4, 6, 20),
    "deep": (10, 14, 50),
    "mid": (28, 32, 96),
    "aurora": (92, 232, 200),
    "violet": (172, 112, 255),
    "corona": (255, 238, 204),
    "rock": (6, 8, 28),
    "rock_light": (42, 46, 112),
}


def eclipse(layer_key: str, art: Art) -> np.ndarray:
    p = ECLIPSE
    sun = (0.63, 0.395)
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["black"]), (0.32, p["deep"]), (HORIZON, p["mid"]), (0.76, p["deep"]), (1.0, p["black"])]))
        stars(art, layer, 760, (224, 232, 255), HORIZON - 0.02)
        # The lights in the sky: curtains that hang, green below and violet above.
        folds = art.noise("folds", cells=16.0, octaves=3, stretch=0.12)
        wave = 0.40 + 0.07 * np.sin(art.u * 9.0 + 1.2) + 0.03 * np.sin(art.u * 23.0)
        curtain = np.clip(1.0 - np.abs(art.v - wave) / 0.14, 0.0, 1.0)
        lower = smoothstep(0.0, 0.5, (art.v - wave) / 0.14 + 0.5)
        art.light(layer, curtain * (0.35 + 0.65 * folds) * lower, p["aurora"], 0.50)
        art.light(layer, curtain * (0.35 + 0.65 * folds) * (1.0 - lower), p["violet"], 0.45)
        # The sun behind the moon: the corona, its long streams, one bead of light.
        art.light(layer, art.spot(*sun, 0.30, 2.6), p["corona"], 0.75)
        streams, pen = art.drawing()
        rng = art.rand("streams")
        for k in range(14):
            a = k * 360.0 / 14 + rng.uniform(-8, 8)
            pen.poly([sun, polar(*sun, rng.uniform(0.12, 0.24), a - 2.5), polar(*sun, rng.uniform(0.12, 0.24), a + 2.5)], rng.randint(120, 255))
        art.light(layer, art.mask_of(streams, blur=3.0), p["corona"], 0.5)
        art.light(layer, art.spot(*sun, 0.085, 2.0), (255, 255, 255), 0.95)
        disc, pen = art.drawing()
        pen.ellipse(*sun, 0.058)
        art.put(layer, art.mask_of(disc, blur=0.4), p["black"])
        bead = polar(*sun, 0.058, -38.0)
        art.light(layer, art.spot(*bead, 0.03, 2.5), (255, 255, 255), 1.0)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        mesa, line = art.ridge("mesa", HORIZON + 0.005, 0.03, cells=3.0, octaves=4)
        image, pen = art.drawing()
        slit, slit_pen = art.drawing()
        # Domes of an observatory, and dishes that look at the sun.
        for u, r in ((0.20, 0.055), (0.31, 0.034), (0.84, 0.045)):
            v = float(line[int(u * art.n)])
            pen.rect(u - r, v - r * 0.5, u + r, v + 0.02)
            pen.draw.pieslice([(u - r) * art.n, (v - r * 1.5) * art.n, (u + r) * art.n, (v + r * 0.5) * art.n], 180, 360, fill=255)
            slit_pen.rect(u + r * 0.2, v - r * 1.42, u + r * 0.36, v - r * 0.5)
        for u in (0.46, 0.55, 0.95):
            v = float(line[int(u * art.n)])
            pen.rect(u - 0.002, v - 0.05, u + 0.002, v + 0.01)
            pen.draw.pieslice([(u - 0.03) * art.n, (v - 0.085) * art.n, (u + 0.03) * art.n, (v - 0.025) * art.n], 300, 120, fill=255)
        mask = np.maximum(mesa, art.mask_of(image))
        layer = solid(art, mask, mix(p["rock_light"], p["mid"], 0.4), p["rock"], HORIZON - 0.12, HORIZON + 0.06, "mesa rock", 0.08)
        art.light(layer, art.rim(mask, 0.0, 0.004, 0.6) * mask, p["corona"], 0.30)
        art.put(layer, art.mask_of(slit, blur=0.5) * mask, p["aurora"], 0.8)
        art.put(layer, art.mask_of(slit, blur=6.0), p["aurora"], 0.3)
        haze(art, layer, p["mid"], 0.32, HORIZON + 0.05)
        return layer
    if layer_key == "near_background":
        rng = art.rand("stones")
        image, pen = art.drawing()
        glyphs, glyph_pen = art.drawing()
        ground, _ = art.ridge("ground", 0.69, 0.016, cells=5.0, octaves=4)
        # Standing stones, each with a line of signs that give light.
        for u, h, w, lean in ((0.07, 0.30, 0.030, 0.012), (0.20, 0.20, 0.024, -0.008), (0.37, 0.34, 0.034, 0.006), (0.74, 0.27, 0.030, -0.012), (0.90, 0.36, 0.036, 0.010)):
            foot = 0.70
            pen.poly([(u - w, foot), (u - w * 0.82 + lean, foot - h * 0.9), (u - w * 0.3 + lean, foot - h), (u + w * 0.6 + lean, foot - h * 0.96), (u + w * 0.9 + lean * 0.5, foot - h * 0.5), (u + w, foot)])
            for k in range(int(h / 0.035)):
                v = foot - 0.04 - k * 0.035
                cu = u + lean * (foot - v) / h
                kind = rng.randint(0, 2)
                if kind == 0:
                    glyph_pen.ring(cu, v, 0.007, 0.0016)
                elif kind == 1:
                    glyph_pen.line([(cu - 0.007, v + 0.006), (cu, v - 0.007), (cu + 0.007, v + 0.006)], 0.0016)
                else:
                    glyph_pen.line([(cu - 0.007, v), (cu + 0.007, v)], 0.0016)
                    glyph_pen.line([(cu, v - 0.007), (cu, v + 0.007)], 0.0016)
        # Pieces of stone that stay in the air.
        for _ in range(9):
            u, v, s = rng.uniform(0.42, 0.70), rng.uniform(0.34, 0.60), rng.uniform(0.008, 0.02)
            a = rng.uniform(0, 360)
            pen.poly([polar(u, v, s * rng.uniform(0.6, 1.0), a + k * 72) for k in range(5)])
        mask = np.maximum(ground, art.mask_of(image))
        layer = solid(art, mask, mix(p["rock"], p["rock_light"], 0.42), scale(p["rock"], 0.8), 0.32, 0.72, "stone", 0.10)
        art.light(layer, art.rim(mask, -0.003, 0.004, 0.4) * mask, p["corona"], 0.34)
        art.shade(layer, art.rim(mask, 0.005, -0.003, 1.2) * mask, 0.28)
        art.put(layer, art.mask_of(glyphs, blur=0.3) * mask, p["aurora"], 0.95)
        art.put(layer, art.mask_of(glyphs, blur=4.0), p["aurora"], 0.5)
        haze(art, layer, p["deep"], 0.10, 0.72)
        return layer
    layer = art.blank()
    art.put(layer, fog(art, "light mist", 0.69, 0.16), mix(p["mid"], p["aurora"], 0.35), 0.32)
    vignette(art, layer, p["black"], 0.38)
    return layer
