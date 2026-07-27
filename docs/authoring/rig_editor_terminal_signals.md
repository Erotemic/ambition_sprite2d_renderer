# Terminal signals for the rig editor

The Qt event loop is periodically awakened by a small Python-backed timer so
CPython can dispatch terminal signals while the editor is otherwise idle in
native Qt code.

Running:

```bash
uv run --extra gui python -m ambition_sprite2d_renderer.gui path/to/file.rig.json
```

can therefore be stopped with terminal `Ctrl+C`. `SIGINT` exits with status 130
and `SIGTERM` exits with status 143. The handler asks Qt to leave the event loop
cleanly rather than terminating the process in the middle of widget teardown.
