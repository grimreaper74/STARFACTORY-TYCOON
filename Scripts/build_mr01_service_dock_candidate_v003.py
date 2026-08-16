"""Build MR01 dock v003 by relinking v002 variant detail to RP01 core v002."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import bpy


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 2:
        raise SystemExit("Usage: -- shared_core_v002.blend output_v003.blend")
    shared = Path(args[0]).resolve()
    output = Path(args[1]).resolve()
    base_script = Path(__file__).with_name("build_mr01_service_dock_candidate_v002.py")
    spec = importlib.util.spec_from_file_location("lb_mr01_dock_v002_builder", base_script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {base_script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    saved_argv = list(sys.argv)
    try:
        sys.argv = [str(base_script), "--", str(shared), str(output)]
        module.main()
    finally:
        sys.argv = saved_argv
    root = bpy.data.objects["ROOT_LB_MR01_SERVICE_DOCK_V002"]
    root.name = "ROOT_LB_MR01_SERVICE_DOCK_V003"
    root["lb_status"] = "FABRICATED_SHARED_CORE_SOURCE_CANDIDATE_NOT_PROMOTED"
    root["lb_shared_core_candidate"] = "RP01_DOCK_CORE_V002"
    bpy.context.scene["lb_candidate"] = "MR01_SERVICE_DOCK_V003"
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    print(f"Saved MR01 v003 {output}")


if __name__ == "__main__":
    main()
