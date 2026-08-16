"""Read-only inventory for the next crane fabrication/lighting pass."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneVisualCandidate_v030"
GIRDER = ("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/"
          "SM_LB_Crane_BridgeGirder_4500_v001")
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_crane_v030_fabrication_inputs.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

mesh = unreal.load_asset(GIRDER)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError(f"Missing {GIRDER}")
box = mesh.get_bounding_box()
mesh_slots = []
for index, slot in enumerate(mesh.get_editor_property("static_materials")):
    material = slot.get_editor_property("material_interface")
    mesh_slots.append({
        "index": index,
        "slot": str(slot.get_editor_property("imported_material_slot_name")
                    or slot.get_editor_property("material_slot_name")),
        "material": material.get_path_name() if material else None,
    })

rows = []
columns = []
lights = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    location = actor.get_actor_location()
    if ("Crane" in label or "Bridge" in label or "Trolley" in label
            or "Hoist" in label or "CHook" in label or "Reeving" in label):
        row = {
            "actor": label,
            "class": actor.get_class().get_name(),
            "location_cm": [location.x, location.y, location.z],
            "rotation": list(actor.get_actor_rotation().to_tuple()),
            "scale": list(actor.get_actor_scale3d().to_tuple()),
            "tags": [str(tag) for tag in actor.tags],
            "components": [],
        }
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            component_mesh = component.get_editor_property("static_mesh")
            row["components"].append({
                "name": component.get_name(),
                "mesh": component_mesh.get_path_name() if component_mesh else None,
                "materials": [
                    component.get_material(index).get_path_name()
                    if component.get_material(index) else None
                    for index in range(component.get_num_materials())
                ],
            })
        rows.append(row)
    if ("Column" in label or "Post" in label) and 600.0 <= location.z <= 1200.0:
        columns.append({
            "actor": label,
            "location_cm": [location.x, location.y, location.z],
            "class": actor.get_class().get_name(),
        })
    light = actor.get_component_by_class(unreal.LightComponent)
    if light is not None and -12000.0 <= location.x <= -2000.0 and -6500.0 <= location.y <= 1200.0:
        lights.append({
            "actor": label,
            "class": actor.get_class().get_name(),
            "location_cm": [location.x, location.y, location.z],
            "intensity": float(light.get_editor_property("intensity")),
            "visible": bool(light.get_editor_property("visible")),
        })

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-crane-v030-fabrication-inputs/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "map": MAP,
    "girder_mesh": {
        "asset": mesh.get_path_name(),
        "bounds_cm": [box.max.x-box.min.x, box.max.y-box.min.y, box.max.z-box.min.z],
        "material_slots": mesh_slots,
    },
    "crane_actor_count": len(rows),
    "crane_actors": sorted(rows, key=lambda row: row["actor"]),
    "candidate_column_count": len(columns),
    "columns": sorted(columns, key=lambda row: (row["location_cm"][0], row["location_cm"][1])),
    "local_light_count": len(lights),
    "lights": sorted(lights, key=lambda row: row["actor"]),
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_CRANE_V030_FABRICATION_INPUTS_PASS actors={len(rows)} columns={len(columns)} lights={len(lights)}")
unreal.SystemLibrary.quit_editor()
