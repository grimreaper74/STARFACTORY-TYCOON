"""Audit the actual PR-004 candidate material and post-process render state."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


REPO = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v002"
OUT = REPO / "Saved/Audits/pr004_candidate_v002_render_state.json"
MATERIALS = (
    "/Game/LineBoss/Stations/Press/PR004/Candidate_v002/Materials/MI_LB_PR004_SafetyYellow",
    "/Game/LineBoss/Stations/Press/PR004/Candidate_v002/Materials/MI_LB_PR004_MachineDark",
    "/Game/LineBoss/Stations/Press/PR004/Candidate_v002/Materials/MI_LB_PR004_CoilPackaging",
    "/Game/LineBoss/Stations/Press/PR004/Candidate_v002/Materials/MI_LB_PR004_WarningRed",
)
MESHES = (
    "/Game/LineBoss/Stations/Press/PR004/Candidate_v002/PoweredCradle_v001/SM_LB_PR004_PoweredCradle_Static_v001",
    "/Game/LineBoss/Stations/Press/PR004/Candidate_v002/Robot_v002/SM_LB_PR004_Robot_J2_v002",
    "/Game/LineBoss/Stations/Press/PR004/Candidate_v002/ProcessContext_v001/SM_LB_MasterCoil_Candidate_v003",
)

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

material_api = [name for name in dir(unreal.MaterialEditingLibrary) if "parameter" in name.lower()]
material_records = []
for path in MATERIALS:
    material = unreal.load_asset(path)
    record = {"path": path, "exists": material is not None}
    if material is not None:
        for method_name, key in (
            ("get_material_instance_vector_parameter_value", "base_color"),
            ("get_material_instance_scalar_parameter_value", "metallic"),
        ):
            method = getattr(unreal.MaterialEditingLibrary, method_name, None)
            if method is not None:
                try:
                    parameter = "BaseColor" if key == "base_color" else "Metallic"
                    value = method(material, parameter)
                    record[key] = str(value)
                except Exception as exc:
                    record[key + "_error"] = str(exc)
        record["vector_parameter_values"] = [str(value) for value in material.get_editor_property("vector_parameter_values")]
        record["scalar_parameter_values"] = [str(value) for value in material.get_editor_property("scalar_parameter_values")]
    material_records.append(record)

actor_records = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if not (label.startswith("LB_PR004_Validation") or label == "LB_PR004_FixedExposure"):
        continue
    record = {
        "label": label,
        "class": actor.get_class().get_name(),
        "location": list(actor.get_actor_location().to_tuple()),
        "rotation": str(actor.get_actor_rotation()),
    }
    if label == "LB_PR004_FixedExposure":
        settings = actor.get_editor_property("settings")
        for prop in (
            "auto_exposure_method",
            "auto_exposure_min_brightness",
            "auto_exposure_max_brightness",
            "auto_exposure_bias",
            "color_saturation",
            "film_slope",
            "film_toe",
            "film_shoulder",
        ):
            try:
                record[prop] = str(settings.get_editor_property(prop))
            except Exception as exc:
                record[prop + "_error"] = str(exc)
    actor_records.append(record)

mesh_records = []
for path in MESHES:
    mesh = unreal.load_asset(path)
    record = {"path": path, "exists": isinstance(mesh, unreal.StaticMesh)}
    if isinstance(mesh, unreal.StaticMesh):
        record["materials"] = []
        for index, slot in enumerate(mesh.get_editor_property("static_materials")):
            material = slot.get_editor_property("material_interface")
            record["materials"].append({
                "index": index,
                "slot": str(slot.get_editor_property("material_slot_name")),
                "path": material.get_path_name() if material is not None else None,
                "name": material.get_name() if material is not None else None,
            })
    mesh_records.append(record)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "line-boss/audit/pr004-render-state/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "map": MAP,
    "material_api": material_api,
    "materials": material_records,
    "meshes": mesh_records,
    "render_actors": actor_records,
    "promotion": "FORBIDDEN",
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_RENDER_STATE_AUDIT={OUT}")
