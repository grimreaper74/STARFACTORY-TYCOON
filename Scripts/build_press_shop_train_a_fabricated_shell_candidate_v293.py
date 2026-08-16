"""Place v015 fabricated shell into one fresh direct-v288 comparison child."""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288"
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellCandidate_v293"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellCandidate_v293.umap"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_train_a_fabricated_shell_build_v293.json"
ASSET = "/Game/LineBoss/Candidates/PressTrains/TrainA/FabricatedShell_v040/SM_CA_MW_PTA_PresentationShell_v015"
CAMERAS = [
    ("LB_V293_CAM_TrainAOperator", (7000, -3350, 820), (4300, -4300, 500), 54),
    ("LB_V293_CAM_TrainAFabrication", (6200, -3375, 650), (4800, -4300, 500), 50),
    ("LB_V293_CAM_TrainAOverview", (8500, -3200, 1500), (3800, -4300, 480), 57),
]
LIGHTS = [(2450, -4300, 1325), (3900, -4300, 1325), (5350, -4300, 1325)]
lib = unreal.EditorAssetLibrary; levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""): digest.update(chunk)
    return digest.hexdigest().upper()
if lib.does_asset_exist(MAP) or OUT.exists(): raise RuntimeError("refusing to overwrite v293")
base_hash = sha(BASE_FILE); mesh = lib.load_asset(ASSET)
if not isinstance(mesh, unreal.StaticMesh): raise RuntimeError(ASSET)
if not levels.new_level_from_template(MAP, BASE): raise RuntimeError("fresh direct-v288 child failed")
before = api.get_all_level_actors(); train_before = [a for a in before if "LB.PressTrain.Installed.TRAIN_A" in {str(t) for t in a.tags}]
rotation = unreal.Rotator(); rotation.set_editor_properties({"pitch": 0.0, "yaw": 90.0, "roll": 0.0})
shell = api.spawn_actor_from_object(mesh, unreal.Vector(1600, -4738, 0), rotation, False); shell.set_actor_label("LB_V293_PTA_FABRICATED_SHELL_V015"); shell.set_actor_scale3d(unreal.Vector(100, 100, 100))
shell.tags = [unreal.Name(x) for x in ("LB.PressTrain.PresentationShell.TrainA.v015", "LB.PressTrain.TrainA", "LB.Asset.Candidate.v293", "LB.Asset.CandidateNotPromoted", "LB.Collision.NoCollision", "LB.Integration.InheritedHallComparisonOnly")]
component = shell.static_mesh_component; component.set_collision_profile_name(unreal.Name("NoCollision"), True); component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); component.set_editor_property("generate_overlap_events", False); component.set_editor_property("can_ever_affect_navigation", False)
lights = []
for index, location in enumerate(LIGHTS, 1):
    light = api.spawn_actor_from_class(unreal.PointLight, unreal.Vector(*location), unreal.Rotator()); label = f"LB_V293_LIGHT_TrainA_TaskFill_{index:02d}"; light.set_actor_label(label)
    light.point_light_component.set_mobility(unreal.ComponentMobility.MOVABLE); light.point_light_component.set_editor_properties({"intensity": 520.0, "attenuation_radius": 1050.0, "source_radius": 55.0, "light_color": unreal.Color(205, 218, 228, 255), "cast_shadows": False})
    light.tags = [unreal.Name("LB.Lighting.IndustrialLED.TrainATaskFill"), unreal.Name("LB.Lighting.PreviewOnly.NoLuxAuthority"), unreal.Name("LB.Asset.Candidate.v293"), unreal.Name("LB.Asset.CandidateNotPromoted")]; lights.append(label)
cameras = []
for label, location, target, fov in CAMERAS:
    camera = api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator()); camera.set_actor_label(label); camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False); camera.camera_component.set_editor_properties({"field_of_view": float(fov), "aspect_ratio": 16/9, "constrain_aspect_ratio": True}); camera.tags = [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.TrainAShell.v293"), unreal.Name("LB.Asset.Candidate.v293"), unreal.Name("LB.Asset.CandidateNotPromoted")]; cameras.append(label)
origin, extent = shell.get_actor_bounds(False, False); bounds = {"min_cm": [origin.x-extent.x, origin.y-extent.y, origin.z-extent.z], "max_cm": [origin.x+extent.x, origin.y+extent.y, origin.z+extent.z], "size_cm": [extent.x*2, extent.y*2, extent.z*2]}
after = api.get_all_level_actors(); train_after = [a for a in after if "LB.PressTrain.Installed.TRAIN_A" in {str(t) for t in a.tags}]
failures = []
if len(train_before) != 338 or len(train_after) != 338: failures.append(f"installed Train A changed {len(train_before)}->{len(train_after)}")
if not (2000 <= bounds["min_cm"][0] <= 2020 and 5595 <= bounds["max_cm"][0] <= 5620): failures.append(f"X envelope invalid {bounds}")
if not (-4355 <= bounds["min_cm"][1] <= -4340 and -4255 <= bounds["max_cm"][1] <= -4240): failures.append(f"Y envelope invalid {bounds}")
if not (1030 <= bounds["max_cm"][2] <= 1080): failures.append(f"Z envelope invalid {bounds}")
if str(component.get_collision_profile_name()) != "NoCollision" or component.get_editor_property("can_ever_affect_navigation"): failures.append("collision/navigation invalid")
if not levels.save_current_level(): failures.append("save failed")
if sha(BASE_FILE) != base_hash: failures.append("protected v288 changed")
payload = {"$schema": "cairnwell/audit/press-shop-train-a-fabricated-shell-build-v293/v1", "generated_utc": datetime.now(timezone.utc).isoformat(), "status": "PASS__V015_FABRICATED_SHELL_IN_FRESH_DIRECT_V288_CHILD__VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V293_NOT_A_PARENT", "base": BASE, "map": MAP, "base_sha256": base_hash, "map_sha256": sha(MAP_FILE) if MAP_FILE.exists() else None, "shell_asset": ASSET, "shell_transform": {"location_cm": [1600, -4738, 0], "rotation": {"pitch": 0, "yaw": 90, "roll": 0}, "scale": [100, 100, 100]}, "shell_world_bounds": bounds, "material_slots": [str(x.material_slot_name) for x in mesh.get_editor_property("static_materials")], "added_lights": lights, "added_cameras": cameras, "installed_train_a_actor_count_before": len(train_before), "installed_train_a_actor_count_after": len(train_after), "promotion_authorized": False, "failures": failures}
OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8"); print(json.dumps(payload, indent=2))
if failures: raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
