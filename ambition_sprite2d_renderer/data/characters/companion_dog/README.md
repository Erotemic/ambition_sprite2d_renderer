# Companion dog

Edit `companion_dog_side.svg` to change the dog's shapes and colors. Each visible
part is an Inkscape layer with a `data-rig-part` name. Keep the group IDs and
part names when you edit the art. The rig uses these IDs to load each part.

Edit `../../targets/characters/rigged/companion_dog/companion_dog_side.rig.json`
to change joint positions or motion. Render and inspect the target with:

```bash
uv run ambition-sprite2d-renderer sheet companion_dog
uv run ambition-sprite2d-renderer audit-poses companion_dog
```
