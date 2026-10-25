"""Chargen Studio: the page's vocabulary comes from the generator's own
tables, a sweep walks every value of a field, and the server draws a spec
in its views and refuses a file outside the renderer's data."""

from __future__ import annotations

import json
import threading
import urllib.request

import pytest

from ambition_sprite2d_renderer.chargen import spec as S
from ambition_sprite2d_renderer.chargen import studio


def test_the_schema_is_the_generators_own():
    sc = studio.schema()
    assert set(sc["bases"]) == set(S.BASES)
    assert sc["choices"]["hair.style"] == list(S.HAIR_STYLES)
    assert sc["bounds"]["body.height_cm"] == list(S.BOUNDS["body.height_cm"])
    assert [v["key"] for v in sc["views"]] == ["front", "front_3q", "side", "back_3q", "back"]


def test_a_sweep_walks_every_value_and_keeps_the_rest():
    assert studio.sweep_values("face.nose") == list(S.NOSES)
    lo, hi = S.BOUNDS["body.age"]
    assert studio.sweep_values("body.age")[0] == lo and studio.sweep_values("body.age")[-1] == hi
    spec = S.generate("slim_female", 3).to_dict()
    swept = studio._swept(spec, "face.nose", "hooked")
    assert swept["face"]["nose"] == "hooked" and swept["hair"] == spec["hair"]
    gator = studio._swept(spec, "head.species", "alligator")
    assert "skin" not in gator["palette"]  # an animal's coat comes from its species
    assert studio.complete(gator).head.species == "alligator"


def test_an_example_must_be_a_spec_under_the_renderers_data():
    assert any(x["path"].endswith(".chargen.yaml") for x in studio.examples())
    with pytest.raises(ValueError):
        studio.load_example("../../../../pyproject.toml")


def test_the_server_draws_a_spec_in_its_five_views():
    st = studio.Studio(jobs=2)
    server = studio.ThreadingHTTPServer(("127.0.0.1", 0), studio._handler(st))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}"
        body = json.dumps({"spec": {"base": "average_male", "seed": 1}}).encode()
        req = urllib.request.Request(url + "/api/views", data=body, headers={"Content-Type": "application/json"})
        got = json.loads(urllib.request.urlopen(req, timeout=120).read())
        assert set(got["views"]) == {"front", "front_3q", "side", "back_3q", "back"}
        assert all(svg.lstrip().startswith("<?xml") and "<svg" in svg for svg in got["views"].values())
        assert got["spec"]["base"] == "average_male"
        assert b"Chargen Studio" in urllib.request.urlopen(url + "/", timeout=10).read()
    finally:
        server.shutdown()
        st.draw.shutdown()
        st.pose.shutdown()
