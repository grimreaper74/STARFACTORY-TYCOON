"""Read-only identity/bounds audit for the v270 MR01 side-by-side evidence."""
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v270"
OUT = Path(unreal.Paths.project_saved_dir()).resolve() / "Audits/SupportRobots/press_shop_mr01_modular_dock_comparison_identity_v271.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"failed to load {MAP}")

records = []
for actor in actors.get_all_level_actors():
    loc = actor.get_actor_location()
    if not (-6900 <= loc.x <= -4700 and 4850 <= loc.y <= 5450 and -50 <= loc.z <= 500):
        continue
    origin, extent = actor.get_actor_bounds(False, False)
    meshes = []
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.static_mesh
        if mesh:
            local_bounds = mesh.get_bounds()
            meshes.append({
                "component": component.get_name(),
                "mesh": mesh.get_path_name(),
                "visible": component.is_visible(),
                "mesh_local_bounds_origin_cm": [round(local_bounds.origin.x, 3), round(local_bounds.origin.y, 3), round(local_bounds.origin.z, 3)],
                "mesh_local_bounds_extent_cm": [round(local_bounds.box_extent.x, 3), round(local_bounds.box_extent.y, 3), round(local_bounds.box_extent.z, 3)],
                "relative_location_cm": [round(component.relative_location.x, 3), round(component.relative_location.y, 3), round(component.relative_location.z, 3)]
            })
    records.append({
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_path_name(),
        "location_cm": [round(loc.x, 3), round(loc.y, 3), round(loc.z, 3)],
        "bounds_origin_cm": [round(origin.x, 3), round(origin.y, 3), round(origin.z, 3)],
        "bounds_extent_cm": [round(extent.x, 3), round(extent.y, 3), round(extent.z, 3)],
        "meshes": meshes,
        "tags": sorted(str(tag) for tag in actor.tags)
    })

records.sort(key=lambda item: (item["location_cm"][0], item["label"]))
targets = {record["label"]: record for record in records if record["label"] in {"LB-DOCK-MR01-01", "LB-DOCK-MR01-02"}}
if set(targets) != {"LB-DOCK-MR01-01", "LB-DOCK-MR01-02"}:
    raise RuntimeError(f"missing comparison targets: {sorted(targets)}")
payload = {
    "$schema": "cairnwell/audit/press-shop-mr01-modular-dock-comparison-identity-v271/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__READ_ONLY_ACTOR_IDENTITY_AND_BOUNDS__VISUAL_JUDGEMENT_STILL_REQUIRED",
    "map": MAP,
    "replacement": targets["LB-DOCK-MR01-01"],
    "retained_control": targets["LB-DOCK-MR01-02"],
    "nearby_room_actors": records,
    "promotion_authorized": False
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_MR01_DOCK_COMPARISON_IDENTITY_V271_PASS {OUT}")
