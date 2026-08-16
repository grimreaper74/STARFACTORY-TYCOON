"""Create an isolated same-height comparison of the old merged press and untouched high-res press."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import unreal

root = Path(unreal.Paths.project_dir()).resolve()
map_path = "/Game/LineBoss/Developer/Validation/Maps/LB_PressGeometryComparison_v958"
old_path = "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v015/TexturedModules/Station/SM_CA_MW_PressStation_S02_S06_Textured_v015/StaticMeshes/SM_CA_M_red_v015.SM_CA_M_red_v015"
high_path = "/Game/LineBoss/Developer/Validation/BlenderApproved_v957/S03WalkerHighResolution/Cairnwell_S03_Walker_HighResolution_v957/StaticMeshes/Cairnwell_S0_solution_v957.Cairnwell_S0_solution_v957"
protected = root / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
expected = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
output = root / "Saved/Audits/PressTrains/press_geometry_comparison_map_v958.json"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sha = lambda: hashlib.sha256(protected.read_bytes()).hexdigest().upper()
if sha() != expected or library.does_asset_exist(map_path):
    raise RuntimeError("protected/fresh invariant")
old_mesh = unreal.load_asset(old_path)
high_mesh = unreal.load_asset(high_path)
if not isinstance(old_mesh, unreal.StaticMesh) or not isinstance(high_mesh, unreal.StaticMesh):
    raise RuntimeError("comparison meshes missing")
if not levels.new_level(map_path):
    raise RuntimeError("new level failed")

cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, -25))
floor.set_actor_label("LB_PRESS_COMPARISON_FLOOR_v958")
floor.static_mesh_component.set_static_mesh(cube)
floor.set_actor_scale3d(unreal.Vector(18, 24, 0.5))

def place(label, mesh, y, target_height):
    box = mesh.get_bounding_box()
    source_height = box.max.z - box.min.z
    scale = target_height / source_height
    z = -box.min.z * scale
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, y, z))
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    return actor, scale

old_actor, old_scale = place("LB_OLD_MERGED_PRESS_REJECT_v958", old_mesh, -650, 820)
high_actor, high_scale = place("LB_HIGHRES_APPROVED_PRESS_v958", high_mesh, 650, 820)
for location, intensity, radius in [
    (unreal.Vector(-800, -1000, 1100), 18000, 2400),
    (unreal.Vector(900, 1000, 900), 16000, 2200),
    (unreal.Vector(-100, 0, 1400), 12000, 2000),
]:
    light = actors.spawn_actor_from_class(unreal.PointLight, location)
    component = light.get_component_by_class(unreal.PointLightComponent)
    component.set_editor_property("intensity", intensity)
    component.set_editor_property("attenuation_radius", radius)
sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 800))
sky.get_component_by_class(unreal.SkyLightComponent).set_editor_property("intensity", 1.2)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level() or sha() != expected:
    raise RuntimeError("save/protected invariant")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps({
    "revision": "v958",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__ISOLATED_SAME_HEIGHT_COMPARISON__VISUAL_REVIEW_REQUIRED",
    "map": map_path,
    "old_rejected_mesh": old_path,
    "approved_highres_mesh": high_path,
    "target_height_cm": 820,
    "old_scale": old_scale,
    "highres_scale": high_scale,
    "protected_sha256": sha(),
    "meshy_credits_used_by_codex": 0,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_PRESS_GEOMETRY_COMPARISON_V958_PASS")
