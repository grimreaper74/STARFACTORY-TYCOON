"""Render MR01 v003 and add an unobstructed front-on open-tool-rack view."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import bpy


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not args:
        raise SystemExit("Output directory required")
    output = Path(args[0]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    base_script = Path(__file__).with_name("render_mr01_service_dock_candidate_v001.py")
    spec = importlib.util.spec_from_file_location("lb_mr01_dock_base_renderer", base_script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {base_script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Reference envelopes are audit geometry, not visual product geometry. Keep
    # them in the source file but exclude them from beauty/evidence renders.
    for obj in bpy.data.objects:
        if obj.name.startswith("REF_"):
            obj.hide_render = True
    saved_argv = list(sys.argv)
    try:
        sys.argv = [str(base_script), "--", str(output)]
        module.main()
    finally:
        sys.argv = saved_argv
    for source in sorted(output.glob("*_v001.png")):
        source.replace(source.with_name(source.name.replace("_v001.png", "_v003.png")))

    # Base renderer leaves all authorised service pivots in their open evidence
    # state. The rack opens toward -Y into the service bay. Use a square-on
    # service-approach view wide enough to show the complete 2 x 4 rack.
    camera = bpy.data.objects["CAM_MR01_DockReview"]
    camera.location = (0.925, -1.0, 0.78)
    camera.data.lens = 36.0
    module.look_at(camera, (0.925, 1.66, 0.78))
    scene = bpy.context.scene
    scene.render.filepath = str(output / "07_mr01_dock_tool_rack_front_open_v003.png")
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {scene.render.filepath}")


if __name__ == "__main__":
    main()
