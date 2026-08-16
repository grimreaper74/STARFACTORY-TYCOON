"""Repair v004 version metadata without rebuilding the heavy source scene.

Blender 5.2 can intermittently crash while applying hundreds of guard-panel
modifiers in the full generator.  The already-audited geometry is preserved:
this script opens the saved source blend, stamps coherent v004 IDs, then
cleanly re-imports and re-exports each existing FBX one at a time with the same
export settings.  A subsequent independent audit remains mandatory.
"""

from __future__ import annotations

import json
from pathlib import Path

import bpy


REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "SourceAssets/PR004/FilmDewrapSpindle_v004"
BLEND = ROOT / "LB_PR004_FilmDewrapSpindle_Candidate_v004.blend"
MANIFEST = ROOT / "pr004_film_dewrap_spindle_candidate_v004_manifest.json"


def stamp(obj) -> None:
    asset_id = obj.get("line_boss_asset_id")
    if isinstance(asset_id, str):
        obj["line_boss_asset_id"] = asset_id.replace("-v002", "-v004").replace("-v003", "-v004")
    obj["candidate_iteration"] = "v004"


manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
expected_names = {module["object"] for module in manifest["modules"]}
source_objects = [obj for obj in bpy.data.objects if obj.name in expected_names]
if len(source_objects) != len(expected_names):
    raise RuntimeError(
        f"Source blend does not contain all manifest modules: found={len(source_objects)} expected={len(expected_names)}"
    )
for obj in source_objects:
    stamp(obj)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))

for module in manifest["modules"]:
    path = Path(module["fbx"])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(path), use_custom_props=True)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if len(meshes) != 1 or meshes[0].name != module["object"]:
        raise RuntimeError(f"Unexpected clean import for {path}: {[obj.name for obj in meshes]}")
    obj = meshes[0]
    stamp(obj)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=str(path),
        use_selection=True,
        object_types={"MESH"},
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Y",
        axis_up="Z",
        use_mesh_modifiers=True,
        bake_space_transform=False,
        add_leaf_bones=False,
        path_mode="AUTO",
        mesh_smooth_type="FACE",
        use_custom_props=True,
    )
    module["custom_properties"] = {
        key: obj[key]
        for key in obj.keys()
        if key != "_RNA_UI" and isinstance(obj[key], (str, int, float, bool))
    }

manifest["$schema"] = "line-boss/source/pr004-film-dewrap-spindle/v4"
manifest["version"] = "v004"
manifest["visual_gate_context"] = (
    "v002 and v003 failed visual review; v004 remains unpromoted pending Unreal material, motion and fixed-camera gates"
)
MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": "V004_METADATA_REPAIRED_REAUDIT_REQUIRED", "modules": len(manifest["modules"])}))
