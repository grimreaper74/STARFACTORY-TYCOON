"""Compare retained Train A actor distribution with the imported shell's actual Unreal bounds."""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainAShellLitComparisonCandidate_v291"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_train_a_shell_axis_v291.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

rows = []
shell = None
for actor in api.get_all_level_actors():
    tags = {str(t) for t in actor.tags}
    if actor.get_actor_label() == "LB_V291_PTA_PRESENTATION_SHELL_V014":
        shell = actor
    if "LB.PressTrain.Installed.TRAIN_A" in tags:
        loc = actor.get_actor_location()
        origin, extent = actor.get_actor_bounds(False, False)
        rows.append({"label": actor.get_actor_label(), "location_cm": [round(loc.x, 2), round(loc.y, 2), round(loc.z, 2)], "bounds_origin_cm": [round(origin.x, 2), round(origin.y, 2), round(origin.z, 2)], "bounds_extent_cm": [round(extent.x, 2), round(extent.y, 2), round(extent.z, 2)]})
if shell is None:
    raise RuntimeError("shell missing")
origin, extent = shell.get_actor_bounds(False, False)
mesh = shell.static_mesh_component.static_mesh
box = mesh.get_bounding_box()
payload = {
    "map": MAP,
    "retained_train_actor_count": len(rows),
    "retained_location_range_cm": {"x": [min(r["location_cm"][0] for r in rows), max(r["location_cm"][0] for r in rows)], "y": [min(r["location_cm"][1] for r in rows), max(r["location_cm"][1] for r in rows)], "z": [min(r["location_cm"][2] for r in rows), max(r["location_cm"][2] for r in rows)]},
    "shell_world_bounds": {"origin_cm": [origin.x, origin.y, origin.z], "extent_cm": [extent.x, extent.y, extent.z]},
    "mesh_local_bounds_unscaled": {"min": [box.min.x, box.min.y, box.min.z], "max": [box.max.x, box.max.y, box.max.z]},
    "representative_retained_actors": sorted(rows, key=lambda r: (r["location_cm"][0], r["location_cm"][1], r["label"]))[:80],
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
unreal.SystemLibrary.quit_editor()
