"""Test a fail-closed validation collision policy on one PR-004 candidate mesh."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


REPO = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUTPUT = REPO / "Saved/Audits/unreal_5_8_complex_as_simple_collision_test.json"
MESH_PATH = (
    "/Game/LineBoss/Stations/Press/PR004/Candidate_v002/PoweredCradle_v001/"
    "SM_LB_PR004_PoweredCradle_Static_v001"
)

mesh = unreal.load_asset(MESH_PATH)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError(f"Missing test mesh: {MESH_PATH}")

body_setup = mesh.get_editor_property("body_setup")
before = str(body_setup.get_editor_property("collision_trace_flag"))
body_setup.set_editor_property(
    "collision_trace_flag",
    unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE,
)
body_setup.modify()
mesh.modify()
unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
after = str(body_setup.get_editor_property("collision_trace_flag"))

result = {
    "$schema": "line-boss/audit/unreal-complex-as-simple-collision-test/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "engine_version": str(unreal.SystemLibrary.get_engine_version()),
    "mesh": MESH_PATH,
    "before": before,
    "after": after,
    "pass": "USE_COMPLEX_AS_SIMPLE" in after.upper(),
    "scope": "Candidate validation only; release collision remains a separate gate.",
}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_COMPLEX_COLLISION_TEST {result['pass']} {OUTPUT}")
