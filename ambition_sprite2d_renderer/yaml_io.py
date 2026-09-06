"""Fast safe YAML I/O for renderer tooling.

PyYAML's C loader/dumper preserve the safe schema while avoiding the large
pure-Python parsing cost paid repeatedly during target discovery and generated
manifest emission. Wheels normally provide the C implementations; source-only
or minimal installations fall back to the standard safe classes.
"""

from __future__ import annotations

from typing import Any

import yaml

_SAFE_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
_SAFE_DUMPER = getattr(yaml, "CSafeDumper", yaml.SafeDumper)


def safe_load(stream: Any) -> Any:
    return yaml.load(stream, Loader=_SAFE_LOADER)


def safe_dump(data: Any, **kwargs: Any) -> str:
    return yaml.dump(data, Dumper=_SAFE_DUMPER, **kwargs)


__all__ = ["safe_dump", "safe_load"]
