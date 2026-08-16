"""Render MR01 dock v004 with the unobstructed full eight-tool evidence view."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not args:
        raise SystemExit("Output directory required")
    output = Path(args[0]).resolve()
    base = Path(__file__).with_name("render_mr01_service_dock_candidate_v003.py")
    spec = importlib.util.spec_from_file_location("lb_mr01_dock_v003_renderer", base)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {base}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    saved_argv = list(sys.argv)
    try:
        sys.argv = [str(base), "--", str(output)]
        module.main()
    finally:
        sys.argv = saved_argv
    for source in sorted(output.glob("*_v003.png")):
        source.replace(source.with_name(source.name.replace("_v003.png", "_v004.png")))


if __name__ == "__main__":
    main()
