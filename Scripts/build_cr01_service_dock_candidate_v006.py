"""Build CR01 dock v006 by relinking v005 cleaning detail to RP01 core v002."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import bpy


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 2:
        raise SystemExit("Usage: -- shared_core_v002.blend output_v006.blend")
    shared = Path(args[0]).resolve()
    output = Path(args[1]).resolve()
    base_script = Path(__file__).with_name("build_cr01_service_dock_candidate_v005.py")
    spec = importlib.util.spec_from_file_location("lb_cr01_dock_v005_builder", base_script)
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
    root = bpy.data.objects["ROOT_LB_CR01_SERVICE_DOCK_V005"]
    root.name = "ROOT_LB_CR01_SERVICE_DOCK_V006"
    root["lb_status"] = "FABRICATED_SHARED_CORE_SOURCE_CANDIDATE_NOT_PROMOTED"
    root["lb_shared_core_candidate"] = "RP01_DOCK_CORE_V002"
    bpy.context.scene["lb_candidate"] = "LB_CR01_Dock_Candidate_v006"
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    print(f"Saved CR01 v006 {output}")


if __name__ == "__main__":
    main()
