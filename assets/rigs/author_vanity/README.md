# Author vanity-card rig

This directory is intentionally outside
`ambition_sprite2d_renderer/targets/characters/rigged/`. The `author` figure is
not a game actor and must not be auto-registered as a sprite target. It exists
only to produce smoother vanity-card animation.

The editable vector source is:

- `assets/author-rig-labels-joints.svg`

Rebind the SVG after moving joints or editing part membership:

```bash
uv run python scripts/build_author_vanity_rig.py build
```

Open the generated paper-doll rig in the GUI:

```bash
uv run --extra gui python -m ambition_sprite2d_renderer.gui \
    assets/rigs/author_vanity/author_vanity.rig.json
```

Render validation strips or GIF previews:

```bash
uv run python scripts/build_author_vanity_rig.py validate
uv run python scripts/build_author_vanity_rig.py preview
```

The initial clip vocabulary is deliberately small and card-specific:
`vanity_idle`, `vanity_wave`, and `vanity_receive`.
