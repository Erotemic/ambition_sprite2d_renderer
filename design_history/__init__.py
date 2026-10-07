"""A viewing aid for how Ambition's characters looked over time.

⛔ NOT PART OF THE RENDERER. Nothing under ``ambition_sprite2d_renderer`` imports
this package, and this package never copies old drawing code into the tree. An
old design is a commit id in ``lineages.yaml``. Its pixels are made on demand by
running THAT COMMIT'S OWN code in a scratch worktree outside the repository, and
they land in an ignored cache. So a retired design cannot become an authority:
there is no file to import, edit or "just fix".

See ``README.md``.
"""
