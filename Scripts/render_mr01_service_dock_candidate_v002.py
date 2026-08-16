"""Render v002 through the unchanged deterministic v001 review rig."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not args:
        raise SystemExit("Output directory required")
    output = Path(args[0]).resolve()
    script = Path(__file__).with_name("render_mr01_service_dock_candidate_v001.py")
    spec = importlib.util.spec_from_file_location("lb_mr01_dock_v001_renderer", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load renderer: {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    saved_argv = list(sys.argv)
    try:
        sys.argv = [str(script), "--", str(output)]
        module.main()
    finally:
        sys.argv = saved_argv
    for source in sorted(output.glob("*_v001.png")):
        target = source.with_name(source.name.replace("_v001.png", "_v002.png"))
        source.replace(target)
        print(f"Renamed {target}")


if __name__ == "__main__":
    main()
