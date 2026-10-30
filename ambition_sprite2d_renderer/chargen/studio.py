"""Chargen Studio: a local page to make characters with the character
generator and see how far its parameters reach.

    python -m ambition_sprite2d_renderer.chargen studio [--port 8765] [--jobs 5]

The page edits a spec (every field of ``spec.py``, from its schema tables) and
draws it in all eight views: the five the generator draws and the three it
mirrors. A sweep draws one character at every value of one field; a crowd
draws many seeds of one base; a pose builds the character's rigs once and
plays its clips. Nothing is written into the repository: specs are copied or
downloaded from the page, and the rigs of a posed character are cached under
the renderer's ``.cache/chargen_studio``. The editor shows only the knobs
that draw for the character's head and the rest of its spec (``applies.py``),
measured once per version of the drawing code.

The server is the standard library's; drawing runs on a pool of processes
(at most six, the repository's limit), because one view takes about a second.
"""

from __future__ import annotations

import base64
import concurrent.futures
import hashlib
import io
import json
import mimetypes
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

WEB = Path(__file__).resolve().parent / "studio_web"
RENDERER = Path(__file__).resolve().parents[2]
DATA = RENDERER / "ambition_sprite2d_renderer" / "data"
CACHE = RENDERER / ".cache" / "chargen_studio"
MAX_JOBS = 6


# ---- what the page edits -------------------------------------------------------------


def schema() -> Dict[str, Any]:
    """The vocabulary of a spec, from the generator's own tables."""
    from . import spec as S
    from .face import FACES
    from .family import FAMILIES
    from .geometry import VIEWS
    from .overlay import available

    return {
        "bases": {k: b.display_name for k, b in S.BASES.items()},
        "families": {k: f.description for k, f in FAMILIES.items()},
        "overlays": available(),
        "bounds": {k: list(v) for k, v in S.BOUNDS.items()},
        "choices": {k: list(v) for k, v in S.CHOICES.items()},
        "colors": list(S.COLORS),
        "optional_colors": list(S.OPTIONAL_COLORS),
        "accessories": list(S.ACCESSORIES),
        "bools": ["outfit.tucked", "outfit.outer_open"],
        "ints": {"hair.ornaments": [0, 6]},
        "faces": list(FACES),
        "views": [{"key": v.key, "label": v.label, "yaw": v.yaw} for v in VIEWS],
        "palettes": {"skin": list(S.SKIN_TONES), "hair": S.HAIR_COLORS, "eyes": S.EYE_COLORS, "cloth": list(S.CLOTH),
                     "leather": list(S.LEATHER), "uniform": S.UNIFORM},
    }


def complete(data: Mapping[str, Any]):
    """A full, valid spec from what the page sent (fields left out are drawn
    from its base and seed)."""
    from .spec import complete as _complete

    return _complete(data)


def generate(body: Mapping[str, Any]):
    """A new character of ``body["base"]`` and ``body["seed"]``, keeping the
    family and the head (species) the page asks for."""
    from .spec import generate as _generate

    over = {k: body[k] for k in ("family", "head") if body.get(k)}
    return _generate(body.get("base"), int(body.get("seed", 0)), over or None)


def examples() -> List[Dict[str, str]]:
    """The character-generator specs in the renderer's data, to open."""
    out = []
    for path in sorted(DATA.rglob("*.chargen.yaml")) + sorted(DATA.rglob("*.chargen.json")):
        out.append({"name": path.name.split(".chargen.")[0], "path": str(path.relative_to(DATA))})
    return out


def load_example(rel: str) -> Dict[str, Any]:
    """``{"spec", "game"}`` of a spec under the renderer's data. A resident's
    file carries a ``game`` section (its catalog id, its clips) that is not
    part of the drawing: it is set aside, and the page writes it back."""
    path = (DATA / rel).resolve()
    if DATA.resolve() not in path.parents or not path.name.endswith((".chargen.yaml", ".chargen.json")):
        raise ValueError(f"not a spec under the renderer's data: {rel}")
    text = path.read_text(encoding="utf8")
    if path.name.endswith(".yaml"):
        import yaml

        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    game = data.pop("game", None)
    return {"spec": complete(data).to_dict(), "game": game}


# ---- drawing (in worker processes) ---------------------------------------------------


def _view_svg(spec_dict: Mapping[str, Any], view_key: str, face: Optional[str]) -> str:
    from .face import face_channels
    from .geometry import VIEW_BY_KEY
    from .rig import view_svg

    spec = complete(spec_dict)
    state = face_channels(face) if face and face != "neutral" else None
    return view_svg(spec, VIEW_BY_KEY[view_key], state=state)


def _swept(spec_dict: Mapping[str, Any], dotted: str, value: Any) -> Dict[str, Any]:
    d = json.loads(json.dumps(spec_dict))
    if dotted in ("base", "seed", "family"):
        d[dotted] = value
        if dotted in ("base", "seed"):
            # Another base or seed draws every field anew, except what the
            # sweep keeps: the family and the species.
            d = {"base": d["base"], "seed": d["seed"], "family": d.get("family", "standard"),
                 "head": {"species": (d.get("head") or {}).get("species", "human")}}
        return d
    section, name = dotted.split(".")
    d.setdefault(section, {})[name] = value
    if dotted == "head.species" and "palette" in d:
        d["palette"].pop("skin", None)  # an animal's coat comes from its species
    return d


def sweep_values(dotted: str, steps: int = 7) -> List[Any]:
    from . import spec as S
    from .family import FAMILIES

    if dotted == "base":
        return sorted(S.BASES)
    if dotted == "family":
        return list(FAMILIES)
    if dotted == "seed":
        return list(range(steps))
    if dotted in S.CHOICES:
        return list(S.CHOICES[dotted])
    if dotted in S.BOUNDS:
        lo, hi = S.BOUNDS[dotted]
        return [round(lo + (hi - lo) * i / (steps - 1), 3) for i in range(steps)]
    raise ValueError(f"cannot sweep {dotted!r}")


# ---- posing (one worker that keeps the rigs it built) --------------------------------

_POSED: Dict[str, Any] = {}


def spec_key(spec_dict: Mapping[str, Any]) -> str:
    return hashlib.sha1(json.dumps(complete(spec_dict).to_dict(), sort_keys=True).encode()).hexdigest()[:16]


def _rigged(spec_dict: Mapping[str, Any]):
    from .rig import find_rigs, write_character
    from .sheets import RiggedCharacter

    key = spec_key(spec_dict)
    if key not in _POSED:
        out = CACHE / key
        if not (out / "done").exists():
            write_character(complete(spec_dict), out)
            (out / "done").write_text("")
        rigs = find_rigs(out)
        some = json.loads(next(iter(rigs.values())).read_text())
        _POSED.clear()  # one posed character at a time: rigs are large
        _POSED[key] = RiggedCharacter(rigs, list(some["clips"]))
    return _POSED[key]


def _clips(spec_dict: Mapping[str, Any]) -> List[Dict[str, Any]]:
    rc = _rigged(spec_dict)
    return [{"name": n, "frames": f, "ms": ms, "view": rc.views.get(n, "side")} for n, f, ms in rc.rows()]


def _pose_frames(spec_dict: Mapping[str, Any], clip: str) -> Dict[str, Any]:
    rc = _rigged(spec_dict)
    counts = {n: (f, ms) for n, f, ms in rc.rows()}
    frames, ms = counts[clip]
    images = [rc.render_frame(clip, i, frames) for i in range(frames)]
    box = None
    for im in images:
        b = im.getbbox()
        if b:
            box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    out = []
    for im in images:
        if box:
            im = im.crop((box[0] - 4, box[1] - 4, box[2] + 4, box[3] + 4))
        buf = io.BytesIO()
        im.save(buf, "PNG")
        out.append("data:image/png;base64," + base64.b64encode(buf.getvalue()).decode())
    return {"clip": clip, "ms": ms, "frames": out}


# ---- the server -------------------------------------------------------------------------


def applies_cache() -> Path:
    from .applies import version

    return CACHE / f"applies-{version()}.json"


def measure_applies(jobs: int = MAX_JOBS, log=print) -> Dict[str, Any]:
    """Measure which knobs every head species draws (``applies.py``) and
    cache it for this version of the drawing code."""
    from .applies import measure
    from .spec import SPECIES

    path = applies_cache()
    if path.is_file():
        return json.loads(path.read_text())
    log(f"measuring which knobs each head draws ({len(SPECIES)} species, {min(jobs, MAX_JOBS)} processes)...")
    with concurrent.futures.ProcessPoolExecutor(max_workers=min(jobs, MAX_JOBS)) as pool:
        table = measure(SPECIES, lambda fn, items: pool.map(fn, items, chunksize=4))
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(".partial")
    partial.write_text(json.dumps(table))
    partial.replace(path)
    log(f"knobs measured: {path}")
    return table


class Studio:
    def __init__(self, jobs: int, *, measure: bool = True) -> None:
        jobs = max(2, min(jobs, MAX_JOBS))
        self.applies: Optional[Dict[str, Any]] = None
        cached = applies_cache()
        if cached.is_file() or not measure:
            self.applies = json.loads(cached.read_text()) if cached.is_file() else {}
            measuring = 0
        else:
            # Measured on processes of their own, so drawing never waits behind it.
            measuring = 2 if jobs >= 5 else 1
            threading.Thread(target=self._measure, args=(measuring,), daemon=True).start()
        self.draw = concurrent.futures.ProcessPoolExecutor(max_workers=max(1, jobs - 1 - measuring))
        self.pose = concurrent.futures.ProcessPoolExecutor(max_workers=1)

    def _measure(self, jobs: int) -> None:
        try:
            self.applies = measure_applies(jobs)
        except Exception as ex:  # noqa: BLE001 - the page then shows every knob
            print(f"could not measure the knobs: {type(ex).__name__}: {ex}", flush=True)
            self.applies = {}

    def applies_state(self) -> Dict[str, Any]:
        from .applies import REQUIRES

        return {"ready": self.applies is not None, "species": self.applies or {},
                "requires": {k: [o, list(v)] for k, (o, v) in REQUIRES.items()}}

    def views(self, body: Mapping[str, Any]) -> Dict[str, Any]:
        spec = complete(body["spec"])  # raises on an invalid spec, before any drawing
        face = body.get("face")
        keys = [v["key"] for v in schema()["views"]]
        futures = {k: self.draw.submit(_view_svg, body["spec"], k, face) for k in keys}
        return {"spec": spec.to_dict(), "views": {k: f.result() for k, f in futures.items()}}

    def tiles(self, specs: List[Dict[str, Any]], view: str, face: Optional[str] = None) -> List[str]:
        return [f.result() for f in [self.draw.submit(_view_svg, s, view, face) for s in specs]]

    def sweep(self, body: Mapping[str, Any]) -> Dict[str, Any]:
        values = sweep_values(body["field"])
        specs = [_swept(body["spec"], body["field"], v) for v in values]
        return {"field": body["field"], "values": values, "tiles": self.tiles(specs, body.get("view", "front_3q"), body.get("face"))}

    def crowd(self, body: Mapping[str, Any]) -> Dict[str, Any]:
        from .spec import crowd

        over = body.get("bases") or None
        specs = [s.to_dict() for s in crowd(int(body.get("count", 12)), int(body.get("seed", 0)), over,
                                            species=body.get("species") or None, family=body.get("family") or None)]
        return {"specs": specs, "tiles": self.tiles(specs, body.get("view", "front_3q"))}

    def faces(self, body: Mapping[str, Any]) -> Dict[str, Any]:
        names = schema()["faces"]
        return {"faces": names, "tiles": [f.result() for f in [self.draw.submit(_view_svg, body["spec"], body.get("view", "front_3q"), n)
                                                              for n in names]]}

    def clips(self, body: Mapping[str, Any]) -> Dict[str, Any]:
        return {"key": spec_key(body["spec"]), "clips": self.pose.submit(_clips, body["spec"]).result()}

    def posed(self, body: Mapping[str, Any]) -> Dict[str, Any]:
        return self.pose.submit(_pose_frames, body["spec"], body["clip"]).result()


def _handler(studio: Studio):
    routes = {
        "/api/views": studio.views,
        "/api/sweep": studio.sweep,
        "/api/crowd": studio.crowd,
        "/api/faces": studio.faces,
        "/api/clips": studio.clips,
        "/api/pose": studio.posed,
        "/api/generate": lambda b: {"spec": generate(b).to_dict()},
        "/api/complete": lambda b: {"spec": complete(b["spec"]).to_dict()},
        "/api/example": lambda b: load_example(b["path"]),
    }

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # quiet: one line per request is noise
            pass

        def _send(self, status, body: bytes, kind: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path == "/api/schema":
                return self._send(HTTPStatus.OK, json.dumps(schema()).encode(), "application/json")
            if path == "/api/examples":
                return self._send(HTTPStatus.OK, json.dumps(examples()).encode(), "application/json")
            if path == "/api/applies":
                return self._send(HTTPStatus.OK, json.dumps(studio.applies_state()).encode(), "application/json")
            name = "index.html" if path in ("/", "") else path.lstrip("/")
            file = (WEB / name).resolve()
            if WEB.resolve() not in file.parents or not file.is_file():
                return self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain")
            self._send(HTTPStatus.OK, file.read_bytes(), mimetypes.guess_type(file.name)[0] or "application/octet-stream")

        def do_POST(self):
            route = routes.get(self.path)
            if route is None:
                return self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain")
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
                result = route(body)
                self._send(HTTPStatus.OK, json.dumps(result).encode(), "application/json")
            except Exception as ex:  # noqa: BLE001 - the page shows the error and stays usable
                self._send(HTTPStatus.BAD_REQUEST, json.dumps({"error": f"{type(ex).__name__}: {ex}"}).encode(), "application/json")

    return Handler


def serve(port: int = 8765, jobs: int = 6, host: str = "127.0.0.1", open_browser: bool = False) -> None:
    studio = Studio(jobs)
    server = ThreadingHTTPServer((host, port), _handler(studio))
    url = f"http://{host}:{port}/"
    print(f"Chargen Studio: {url}  (drawing on {studio.draw._max_workers} processes; Ctrl-C stops)", flush=True)
    if open_browser:
        import webbrowser

        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        studio.draw.shutdown(cancel_futures=True)
        studio.pose.shutdown(cancel_futures=True)
