// Chargen Studio: edits a character-generator spec and draws it through the
// local server (`chargen studio`). The server owns every rule: this page only
// lays out the spec's fields from `/api/schema` and shows what it draws.
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const svgUrl = (svg) => "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
  const SECTIONS = ["body", "face", "hair", "head", "palette", "outfit"];
  // The eight views: the five drawn yaws, then the three left ones as mirrors.
  const EIGHT = [["front", false], ["front_3q", false], ["side", false], ["back_3q", false], ["back", false], ["back_3q", true], ["side", true], ["front_3q", true]];
  let S = null;                 // the schema
  let A = null;                 // which knobs draw (`/api/applies`): by head species, and the REQUIRES rules
  let showAll = false;
  let game = null;              // a resident's `game` section: not drawn, written back to its YAML
  let spec = null;              // the current spec, as the server completed it
  let face = "neutral";
  let seq = 0, timer = 0;

  // ---- talking to the server -------------------------------------------------------
  async function api(path, body) {
    const res = await fetch(path, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || res.statusText);
    return data;
  }
  function status(text, err) {
    const el = $("status");
    el.textContent = text || "";
    el.classList.toggle("err", !!err);
  }
  async function busy(label, fn) {
    status(label + "…");
    const t0 = performance.now();
    try { const r = await fn(); status(`${label}: ${((performance.now() - t0) / 1000).toFixed(1)} s`); return r; }
    catch (e) { status(e.message, true); throw e; }
  }

  // ---- the spec ------------------------------------------------------------------------
  const get = (dotted) => dotted.split(".").reduce((o, k) => (o == null ? o : o[k]), spec);
  function set(dotted, value) {
    const keys = dotted.split("."), last = keys.pop();
    let o = spec;
    for (const k of keys) o = o[k] = o[k] || {};
    o[last] = value;
  }
  function remember() { try { localStorage.setItem("chargen-studio-spec", JSON.stringify(spec)); } catch (e) { /* no storage */ } }
  function recalled() { try { return JSON.parse(localStorage.getItem("chargen-studio-spec") || "null"); } catch (e) { return null; } }

  // A new base or seed draws every field anew; the family and species stay.
  async function regenerate(over) {
    game = null;
    const body = { base: spec ? spec.base : "average_female", seed: spec ? spec.seed : 0,
      family: spec ? spec.family || "standard" : "standard", head: { species: spec ? spec.head.species : "human" }, ...over };
    const name = spec && spec.name;
    spec = (await busy("generating", () => api("/api/generate", body))).spec;
    if (name && !/^Townsperson|^Townsfolk/.test(name)) spec.name = name;
    buildEditor(); draw();
  }

  // ---- the editor --------------------------------------------------------------------
  function kind(dotted) {
    if (S.bounds[dotted]) return "range";
    if (S.choices[dotted]) return "choice";
    if (S.colors.includes(dotted) || S.optional_colors.includes(dotted)) return "color";
    if (S.bools.includes(dotted)) return "bool";
    if (S.ints[dotted]) return "int";
    if (dotted === "outfit.accessories") return "accessories";
    if (dotted === "outfit.wardrobe") return "wardrobe";
    return "text";
  }
  const sweepable = (dotted) => !!(S.bounds[dotted] || S.choices[dotted]);
  const swatchFor = (dotted) => dotted === "palette.skin" ? S.palettes.skin : dotted === "palette.hair" ? Object.values(S.palettes.hair)
    : dotted === "palette.eyes" ? Object.values(S.palettes.eyes) : dotted === "outfit.shoe_color" ? S.palettes.leather.concat(S.palettes.cloth.slice(0, 6))
    : S.palettes.cloth.concat(Object.values(S.palettes.uniform));

  // A knob shows when it draws: its REQUIRES rule holds for this spec, and the
  // head's species draws it (measured; see chargen/applies.py).
  function requiresHold(dotted) {
    const rule = A && A.requires[dotted];
    if (!rule) return true;
    const [other, values] = rule, have = get(other);
    return other === "outfit.accessories" ? values.some((x) => (have || []).includes(x)) : values.includes(have);
  }
  function headDraws(dotted) {
    const row = A && A.species[spec.head.species];
    return !row || row.fields[dotted] !== false;
  }
  const visible = (dotted) => showAll || (requiresHold(dotted) && headDraws(dotted));
  function choicesFor(dotted) {
    const row = A && A.species[spec.head.species], all = S.choices[dotted];
    if (showAll || !row || !row.values[dotted]) return all;
    const kept = new Set(row.values[dotted]);
    return all.filter((c) => kept.has(c) || c === get(dotted));
  }
  function why(dotted) {
    if (!requiresHold(dotted)) { const [o, v] = A.requires[dotted]; return `needs ${o.split(".")[1]} ${v.length > 4 ? "set" : "= " + v.join(" / ")}`; }
    return `a ${spec.head.species} head draws nothing for it`;
  }

  function control(dotted) {
    const k = kind(dotted), name = dotted.split(".")[1], v = get(dotted);
    const hidden = !visible(dotted);
    if (hidden) return "";
    const sw = sweepable(dotted) ? `<button class="sw" data-sweep="${dotted}" type="button" title="sweep ${esc(name)}">⇶</button>` : "<span></span>";
    if (k === "range") {
      const [lo, hi] = S.bounds[dotted];
      return `<div class="field"><span class="k">${esc(name)}</span><input type="range" data-f="${dotted}" min="${lo}" max="${hi}" step="${(hi - lo) / 100}" value="${v}"><span class="v" data-v="${dotted}">${(+v).toFixed(dotted.endsWith("height_cm") ? 0 : 2)}</span>${sw}</div>`;
    }
    if (k === "choice") {
      return `<div class="field"><span class="k">${esc(name)}</span><select data-f="${dotted}">${choicesFor(dotted).map((c) => `<option${c === v ? " selected" : ""}>${esc(c)}</option>`).join("")}</select><span></span>${sw}</div>`;
    }
    if (k === "color") {
      const optional = S.optional_colors.includes(dotted);
      return `<div class="field color"><span class="k">${esc(name)}</span><input type="color" data-f="${dotted}" value="${v || "#888888"}"><span class="v">${optional ? `<label title="use the default"><input type="checkbox" data-auto="${dotted}"${v ? "" : " checked"}>auto</label>` : ""}</span><span></span></div>
        <div class="swatches">${swatchFor(dotted).map((c) => `<button type="button" style="background:${c}" data-swatch="${dotted}" data-c="${c}" title="${c}"></button>`).join("")}</div>`;
    }
    if (k === "bool") return `<div class="field"><span class="k">${esc(name)}</span><label><input type="checkbox" data-f="${dotted}"${v ? " checked" : ""}> yes</label><span></span><span></span></div>`;
    if (k === "int") { const [lo, hi] = S.ints[dotted]; return `<div class="field"><span class="k">${esc(name)}</span><input type="number" data-f="${dotted}" min="${lo}" max="${hi}" value="${v}"><span></span><span></span></div>`; }
    if (k === "accessories") return `<div class="k">accessories</div><div class="checks">${S.accessories.filter((a) => showAll || (v || []).includes(a) || headDraws("accessory:" + a)).map((a) => `<label><input type="checkbox" data-acc="${a}"${(v || []).includes(a) ? " checked" : ""}> ${esc(a)}</label>`).join("")}</div>`;
    if (k === "wardrobe") return `<div class="field"><span class="k">wardrobe</span><input type="text" data-f="${dotted}" value="${esc((v || []).join(", "))}" title="slot:kind alternates, comma separated"><span></span><span></span></div>`;
    return `<div class="field"><span class="k">${esc(name)}</span><input type="text" data-f="${dotted}" value="${esc(v)}"><span></span><span></span></div>`;
  }
  function buildEditor() {
    const open = new Set([...document.querySelectorAll(".editor details[open]")].map((d) => d.dataset.s));
    if (!open.size) ["body", "face"].forEach((s) => open.add(s));
    const sections = SECTIONS.map((sec) => {
      const names = Object.keys(spec[sec]).filter((n) => !(sec === "head" && n === "species"));
      const off = names.map((n) => `${sec}.${n}`).filter((d) => !visible(d));
      const note = off.length ? `<p class="hidden-note" title="${esc(off.map((d) => `${d.split(".")[1]}: ${why(d)}`).join("\n"))}">${off.length} hidden: ${esc(off.map((d) => d.split(".")[1]).join(", "))}</p>` : "";
      return `<details data-s="${sec}"${open.has(sec) ? " open" : ""}><summary>${sec}${off.length ? ` <span class="n">(${off.length} hidden)</span>` : ""}</summary>${names.map((n) => control(`${sec}.${n}`)).join("")}${note}</details>`;
    });
    const measuring = A && !A.ready ? `<p class="hidden-note">Measuring which knobs each head draws (a few minutes, once per version of the generator)…</p>` : "";
    $("editor").innerHTML = `<label class="showall"><input type="checkbox" id="showAll"${showAll ? " checked" : ""}> show every knob, even those that draw nothing here</label>${measuring}` + sections.join("");
  }
  function syncTop() {
    $("name").value = spec.name; $("base").value = spec.base; $("seed").value = spec.seed;
    $("family").value = spec.family || "standard"; $("species").value = spec.head.species;
  }
  function changed(dotted, value) {
    set(dotted, value);
    if (dotted === "head.species") delete spec.palette.skin;  // an animal's coat comes from its species
    // A choice can show or hide other knobs (an outer garment, a species).
    if (kind(dotted) !== "range" && kind(dotted) !== "color") buildEditor();
    schedule();
  }
  $("editor").addEventListener("input", (e) => {
    const t = e.target, f = t.dataset.f;
    if (f && t.type === "range") { $("editor").querySelector(`[data-v="${f}"]`).textContent = (+t.value).toFixed(f.endsWith("height_cm") ? 0 : 2); changed(f, +(+t.value).toFixed(3)); }
    else if (f && t.type === "color") { const auto = $("editor").querySelector(`[data-auto="${f}"]`); if (auto) auto.checked = false; changed(f, t.value); }
  });
  $("editor").addEventListener("change", (e) => {
    const t = e.target, f = t.dataset.f;
    if (t.id === "showAll") { showAll = t.checked; buildEditor(); return; }
    if (t.dataset.acc) { const list = new Set(get("outfit.accessories") || []); t.checked ? list.add(t.dataset.acc) : list.delete(t.dataset.acc); changed("outfit.accessories", S.accessories.filter((a) => list.has(a))); }
    else if (t.dataset.auto) { changed(t.dataset.auto, t.checked ? "" : $("editor").querySelector(`[data-f="${t.dataset.auto}"]`).value); }
    else if (!f || t.type === "range" || t.type === "color") return;
    else if (t.type === "checkbox") changed(f, t.checked);
    else if (t.type === "number") changed(f, parseInt(t.value, 10) || 0);
    else if (f === "outfit.wardrobe") changed(f, t.value.split(",").map((x) => x.trim()).filter(Boolean));
    else changed(f, t.value);
  });
  $("editor").addEventListener("click", (e) => {
    const sw = e.target.closest("[data-swatch]");
    if (sw) { $("editor").querySelector(`[data-f="${sw.dataset.swatch}"]`).value = sw.dataset.c; changed(sw.dataset.swatch, sw.dataset.c); return; }
    const sweep = e.target.closest("[data-sweep]");
    if (sweep) { $("sweepField").value = sweep.dataset.sweep; tab("sweep"); runSweep(); }
  });

  // ---- the eight views -----------------------------------------------------------------
  function schedule() { clearTimeout(timer); timer = setTimeout(draw, 250); }
  async function draw() {
    clearTimeout(timer);
    const mine = ++seq;
    $("views").classList.add("busy");
    syncTop(); remember();
    try {
      const res = await busy("drawing eight views", () => api("/api/views", { spec, face }));
      if (mine !== seq) return;
      const before = JSON.stringify(spec);
      spec = res.spec;
      if (JSON.stringify(spec) !== before) buildEditor();
      const label = Object.fromEntries(S.views.map((v) => [v.key, v.label]));
      $("views").innerHTML = EIGHT.map(([k, m]) => `<div class="tile"><div class="img"><img src="${svgUrl(res.views[k])}" alt="${esc(label[k])}"${m ? ' class="mirror"' : ""}></div>
        <div class="cap"><span>${esc(label[k])}${m ? " ⇋" : ""}</span><span>${m ? "mirrored" : `yaw ${S.views.find((v) => v.key === k).yaw}°`}</span></div></div>`).join("");
      syncTop(); remember(); writeYaml(); markPose();
    } catch (e) { /* the status line shows it */ } finally { if (mine === seq) $("views").classList.remove("busy"); }
  }

  // ---- sweeps, crowds, faces ---------------------------------------------------------
  function tiles(el, list, caption, current) {
    el.innerHTML = list.map((svg, i) => `<div class="tile${current === i ? " here" : ""}" data-i="${i}"><div class="img"><img src="${svgUrl(svg)}" alt=""></div><div class="cap"><span>${esc(caption(i))}</span></div></div>`).join("");
  }
  let swept = null;
  async function runSweep() {
    const field = $("sweepField").value;
    const res = await busy(`sweeping ${field}`, () => api("/api/sweep", { spec, field, view: $("sweepView").value, face }));
    swept = res;
    const cur = res.values.findIndex((v) => String(v) === String(field.includes(".") ? get(field) : spec[field]));
    tiles($("sweep"), res.tiles, (i) => res.values[i], cur);
  }
  $("sweep").addEventListener("click", (e) => {
    const t = e.target.closest("[data-i]"); if (!t || !swept) return;
    const v = swept.values[+t.dataset.i], f = swept.field;
    if (f === "base" || f === "seed") regenerate({ [f]: v });
    else { if (f === "family") spec.family = v; else changed(f, v); buildEditor(); draw(); }
    tab("views");
  });
  let crowd = null;
  async function runCrowd() {
    const body = { count: +$("crowdCount").value, seed: +$("crowdSeed").value, view: $("crowdView").value,
      bases: $("crowdBase").checked ? [spec.base] : null, family: $("crowdFamily").checked ? spec.family || "standard" : null,
      species: $("crowdSpecies").checked ? spec.head.species : null };
    crowd = await busy("drawing a crowd", () => api("/api/crowd", body));
    tiles($("crowd"), crowd.tiles, (i) => `${crowd.specs[i].base} · seed ${crowd.specs[i].seed}`);
  }
  $("crowd").addEventListener("click", (e) => {
    const t = e.target.closest("[data-i]"); if (!t || !crowd) return;
    const name = spec.name; spec = crowd.specs[+t.dataset.i]; spec.name = name; buildEditor(); draw(); tab("views");
  });
  let faces = null;
  async function runFaces() {
    faces = await busy("drawing every expression", () => api("/api/faces", { spec, view: $("faceView").value }));
    tiles($("faces"), faces.tiles, (i) => faces.faces[i], faces.faces.indexOf(face));
  }
  $("faces").addEventListener("click", (e) => {
    const t = e.target.closest("[data-i]"); if (!t || !faces) return;
    face = faces.faces[+t.dataset.i]; $("face").value = face; draw(); tab("views");
  });

  // ---- posing ------------------------------------------------------------------------
  let posedFor = null, anim = 0;
  function markPose() {
    const stale = posedFor !== null && posedFor !== JSON.stringify(spec);
    $("poseGo").textContent = posedFor === null ? "build the rig" : stale ? "rebuild the rig (the spec changed)" : "rig built";
    $("clip").disabled = posedFor === null || stale;
  }
  async function buildRig() {
    const res = await busy("building the rig (about 40 s the first time)", () => api("/api/clips", { spec }));
    posedFor = JSON.stringify(spec);
    $("clip").innerHTML = res.clips.map((c) => `<option value="${esc(c.name)}">${esc(c.name)} · ${c.frames} fr · ${esc(c.view)}</option>`).join("");
    markPose(); playClip();
  }
  async function playClip() {
    const clip = $("clip").value; if (!clip) return;
    const res = await busy(`posing ${clip}`, () => api("/api/pose", { spec: JSON.parse(posedFor), clip }));
    clearInterval(anim);
    let i = 0;
    $("poseStrip").innerHTML = res.frames.map((src, n) => `<img src="${src}" alt="frame ${n + 1}" data-n="${n}">`).join("");
    const show = () => { $("poseImg").src = res.frames[i]; i = (i + 1) % res.frames.length; };
    show();
    anim = setInterval(show, Math.max(30, (res.ms || 100) / +$("poseSpeed").value));
  }
  $("poseGo").addEventListener("click", buildRig);
  $("clip").addEventListener("change", playClip);
  $("poseSpeed").addEventListener("change", playClip);
  $("poseStrip").addEventListener("click", (e) => { const im = e.target.closest("img"); if (im) { clearInterval(anim); $("poseImg").src = im.src; } });

  // ---- YAML ----------------------------------------------------------------------------
  function yaml(v, indent = "") {
    if (Array.isArray(v)) return v.length ? v.map((x) => `\n${indent}- ${scalar(x)}`).join("") : " []";
    if (v && typeof v === "object") return Object.entries(v).map(([k, x]) => `\n${indent}${k}:${x && typeof x === "object" ? yaml(x, indent + "  ") : " " + scalar(x)}`).join("");
    return " " + scalar(v);
  }
  function scalar(x) {
    if (typeof x === "string") return /^[#'"!&*@`|>%{}\[\],:?-]|^\s|\s$|: |^(true|false|null|yes|no|on|off|~)$|^[\d.+-]+$/i.test(x) || x === "" ? JSON.stringify(x) : x;
    return JSON.stringify(x);
  }
  const yamlText = () => yaml(game ? { ...spec, game } : spec).replace(/^\n/, "") + "\n";
  function writeYaml() { if (document.activeElement !== $("yaml")) $("yaml").value = yamlText(); }
  // Reads JSON, or the plain YAML this page writes: maps by indent, and a key
  // whose block is "- item" lines is a list of scalars.
  function parseYaml(text) {
    try { return JSON.parse(text); } catch (e) { /* YAML */ }
    const lines = text.split("\n").filter((l) => l.trim() && !l.trim().startsWith("#"));
    let i = 0;
    function block(indent) {
      const out = {};
      while (i < lines.length) {
        const at = lines[i].search(/\S/), line = lines[i].trim();
        if (at < indent) break;
        const m = line.match(/^([\w]+):\s*(.*)$/);
        if (!m) throw new Error(`cannot read: ${line}`);
        i++;
        if (m[2] !== "") { out[m[1]] = val(m[2]); continue; }
        const next = lines[i] || "", deeper = next.search(/\S/) > at;
        if (deeper && next.trim().startsWith("- ")) {
          const list = [];
          while (i < lines.length && lines[i].search(/\S/) > at && lines[i].trim().startsWith("- ")) list.push(val(lines[i++].trim().slice(2)));
          out[m[1]] = list;
        } else out[m[1]] = deeper ? block(next.search(/\S/)) : {};
      }
      return out;
    }
    return block(0);
  }
  function val(s) {
    s = s.trim();
    if (s === "[]") return [];
    if (/^".*"$/.test(s)) return JSON.parse(s);
    if (/^'.*'$/.test(s)) return s.slice(1, -1);
    if (/^(true|false)$/.test(s)) return s === "true";
    if (/^-?\d+(\.\d+)?$/.test(s)) return +s;
    return s;
  }
  $("yamlApply").addEventListener("click", () => {
    try { const d = parseYaml($("yaml").value); game = d.game || null; delete d.game; spec = d; buildEditor(); draw(); } catch (e) { status(e.message, true); }
  });
  function slug(s) { return String(s || "character").toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, ""); }
  $("copy").addEventListener("click", async () => {
    const text = yamlText();
    try { await navigator.clipboard.writeText(text); status("YAML copied"); } catch (e) { $("yaml").value = text; tab("yaml"); $("yaml").select(); status("select-all and copy from the YAML tab"); }
  });
  $("download").addEventListener("click", () => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([yamlText()], { type: "text/yaml" }));
    a.download = `${slug(spec.name)}.chargen.yaml`; a.click(); URL.revokeObjectURL(a.href);
  });

  // ---- the top bar and tabs ----------------------------------------------------------
  function tab(name) {
    document.querySelectorAll("#tabs [data-tab]").forEach((b) => b.classList.toggle("on", b.dataset.tab === name));
    document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("on", t.id === "tab-" + name));
    if (name === "yaml") $("yaml").value = yamlText();
  }
  $("tabs").addEventListener("click", (e) => { const b = e.target.closest("[data-tab]"); if (b) tab(b.dataset.tab); });
  $("name").addEventListener("change", () => { spec.name = $("name").value; remember(); writeYaml(); });
  $("base").addEventListener("change", () => regenerate({ base: $("base").value }));
  $("seed").addEventListener("change", () => regenerate({ seed: Math.max(0, parseInt($("seed").value, 10) || 0) }));
  $("seedDown").addEventListener("click", () => regenerate({ seed: Math.max(0, spec.seed - 1) }));
  $("seedUp").addEventListener("click", () => regenerate({ seed: spec.seed + 1 }));
  // A random character: base, seed, family and species all drawn at random.
  const pick = (list) => list[Math.floor(Math.random() * list.length)];
  $("reroll").addEventListener("click", () => regenerate({
    base: pick(Object.keys(S.bases)), seed: Math.floor(Math.random() * 100000),
    family: pick(Object.keys(S.families)), head: { species: pick(S.choices["head.species"]) } }));
  $("family").addEventListener("change", () => { spec.family = $("family").value; draw(); });
  $("species").addEventListener("change", () => changed("head.species", $("species").value));
  $("face").addEventListener("change", () => { face = $("face").value; draw(); });
  $("zoom").addEventListener("input", (e) => $("views").style.setProperty("--tile", e.target.value + "px"));
  $("open").addEventListener("change", async () => {
    const path = $("open").value; if (!path) return;
    ({ spec, game } = await busy("opening " + path, () => api("/api/example", { path })));
    $("open").value = ""; buildEditor(); draw(); tab("views");
  });
  $("sweepGo").addEventListener("click", runSweep);
  $("crowdGo").addEventListener("click", runCrowd);
  $("facesGo").addEventListener("click", runFaces);
  $("theme").addEventListener("click", () => {
    const root = document.documentElement;
    const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("chargen-studio-theme", root.dataset.theme); } catch (e) { /* ignore */ }
  });
  try { const t = localStorage.getItem("chargen-studio-theme"); if (t) document.documentElement.dataset.theme = t; } catch (e) { /* ignore */ }

  // ---- start ---------------------------------------------------------------------------
  (async function start() {
    S = await api("/api/schema");
    // Which knobs draw: measured by the server, maybe still measuring.
    const poll = async () => {
      const was = A && A.ready;
      A = await api("/api/applies");
      if (spec && A.ready && !was) buildEditor();  // once, when the measure lands
      if (!A.ready) setTimeout(poll, 5000);
    };
    await poll();
    const opts = (list, label) => list.map((k) => `<option value="${esc(k)}">${esc(label ? label(k) : k)}</option>`).join("");
    $("base").innerHTML = opts(Object.keys(S.bases), (k) => S.bases[k]);
    $("family").innerHTML = opts(Object.keys(S.families));
    $("species").innerHTML = opts(S.choices["head.species"]);
    $("face").innerHTML = opts(S.faces);
    const viewOpts = opts(S.views.map((v) => v.key), (k) => S.views.find((v) => v.key === k).label);
    ["faceView", "sweepView", "crowdView"].forEach((id) => { $(id).innerHTML = viewOpts; $(id).value = "front_3q"; });
    $("sweepField").innerHTML = opts(["base", "seed", "family", ...Object.keys(S.choices), ...Object.keys(S.bounds)]);
    $("sweepField").value = "hair.style";
    api("/api/examples").then((list) => { $("open").innerHTML += list.map((x) => `<option value="${esc(x.path)}">${esc(x.path)}</option>`).join(""); });
    // A link can name what to show: #open=<spec path>, #sweep=<field>,
    // #crowd, #faces, #pose=<clip>, #yaml.
    const want = new URLSearchParams(location.hash.slice(1));
    const saved = recalled();
    if (want.get("open")) { ({ spec, game } = await api("/api/example", { path: want.get("open") })); buildEditor(); await draw(); }
    else if (saved) { spec = saved; buildEditor(); await draw(); } else { spec = null; await regenerate({}); }
    if (want.has("sweep")) { if (want.get("sweep")) $("sweepField").value = want.get("sweep"); tab("sweep"); await runSweep(); }
    else if (want.has("crowd")) { tab("crowd"); await runCrowd(); }
    else if (want.has("faces")) { tab("faces"); await runFaces(); }
    else if (want.has("yaml")) tab("yaml");
    else if (want.has("pose")) { tab("pose"); await buildRig(); if (want.get("pose")) { $("clip").value = want.get("pose"); await playClip(); } }
  })().catch((e) => status(e.message, true));
})();
