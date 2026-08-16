"""Build a fresh direct-v288 Train A shell candidate with explicit axis validation."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288"
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainAShellAxisCorrectedCandidate_v292"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAShellAxisCorrectedCandidate_v292.umap"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_train_a_shell_axis_corrected_build_v292.json"
ASSET = "/Game/LineBoss/Candidates/PressTrains/TrainA/PresentationShell_v035/SM_CA_MW_PTA_PresentationShell_v014"
SRC_MAT = "/Game/LineBoss/Candidates/PressTrains/TrainA/PresentationShell_v291/Materials"
DST_MAT = "/Game/LineBoss/Candidates/PressTrains/TrainA/PresentationShell_v292/Materials"
MATERIALS = {
    "green": "M_CA_MW_PTA_ShellGreen",
    "charcoal": "M_CA_MW_PTA_ShellGraphite",
    "worked_steel": "M_CA_MW_PTA_ShellWorkedSteel",
    "dark_steel": "M_CA_MW_PTA_ShellDarkSteel",
    "yellow": "M_CA_MW_PTA_ShellSafetyYellow",
}
CAMERAS = [
    ("LB_V292_CAM_TrainAOperatorClear", (5200, -3350, 650), (4000, -4300, 500), 52),
    ("LB_V292_CAM_TrainAFabricationClose", (3350, -3380, 580), (3900, -4300, 480), 48),
    ("LB_V292_CAM_TrainAOverviewClear", (7000, -3425, 1050), (3850, -4300, 510), 56),
]
LIGHTS = [(2450, -4300, 1300), (3900, -4300, 1300), (5350, -4300, 1300)]

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()

if lib.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("refusing to overwrite v292")
base_hash = sha(BASE_FILE)
mesh = lib.load_asset(ASSET)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError(ASSET)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("fresh direct-v288 child failed")

materials = {}
for key, stem in MATERIALS.items():
    source = f"{SRC_MAT}/{stem}_v291"
    target = f"{DST_MAT}/{stem}_v292"
    copied = lib.duplicate_asset(source, target)
    if not isinstance(copied, unreal.MaterialInterface):
        raise RuntimeError(f"material duplicate failed {source}")
    materials[key] = copied

before = api.get_all_level_actors()
train_before = [a for a in before if "LB.PressTrain.Installed.TRAIN_A" in {str(t) for t in a.tags}]
rotation = unreal.Rotator()
rotation.set_editor_properties({"pitch": 0.0, "yaw": 90.0, "roll": 0.0})
shell = api.spawn_actor_from_object(mesh, unreal.Vector(1600, -4735, 0), rotation, False)
shell.set_actor_label("LB_V292_PTA_PRESENTATION_SHELL_V014")
shell.set_actor_scale3d(unreal.Vector(100, 100, 100))
shell.tags = [unreal.Name(x) for x in ("LB.PressTrain.PresentationShell.TrainA.v014", "LB.PressTrain.TrainA", "LB.Asset.Candidate.v292", "LB.Asset.CandidateNotPromoted", "LB.Collision.NoCollision", "LB.Integration.InheritedHallComparisonOnly")]
component = shell.static_mesh_component
bindings = []
failures = []
for index, slot in enumerate(mesh.get_editor_property("static_materials")):
    name = str(slot.material_slot_name).lower()
    key = "green" if "green" in name else "yellow" if "yellow" in name else "worked_steel" if "workedsteel" in name else "dark_steel" if "dark" in name else "charcoal" if "charcoal" in name else None
    if key is None:
        failures.append(f"unmapped slot {index}:{name}")
        continue
    component.set_material(index, materials[key])
    bindings.append({"index": index, "slot": str(slot.material_slot_name), "material": materials[key].get_path_name()})
component.set_collision_profile_name(unreal.Name("NoCollision"), True)
component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
component.set_editor_property("generate_overlap_events", False)
component.set_editor_property("can_ever_affect_navigation", False)

light_labels = []
for index, location in enumerate(LIGHTS, 1):
    light = api.spawn_actor_from_class(unreal.PointLight, unreal.Vector(*location), unreal.Rotator())
    label = f"LB_V292_LIGHT_TrainA_TaskFill_{index:02d}"
    light.set_actor_label(label)
    light.point_light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    light.point_light_component.set_editor_properties({"intensity": 600.0, "attenuation_radius": 1050.0, "source_radius": 55.0, "light_color": unreal.Color(205, 218, 228, 255), "cast_shadows": False})
    light.tags = [unreal.Name("LB.Lighting.IndustrialLED.TrainATaskFill"), unreal.Name("LB.Lighting.PreviewOnly.NoLuxAuthority"), unreal.Name("LB.Asset.Candidate.v292"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    light_labels.append(label)

camera_labels = []
for label, location, target, fov in CAMERAS:
    camera = api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    camera.set_actor_label(label)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
    camera.camera_component.set_editor_properties({"field_of_view": float(fov), "aspect_ratio": 16 / 9, "constrain_aspect_ratio": True})
    camera.tags = [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.TrainAShell.v292"), unreal.Name("LB.Asset.Candidate.v292"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    camera_labels.append(label)

origin, extent = shell.get_actor_bounds(False, False)
bounds = {"origin_cm": [origin.x, origin.y, origin.z], "extent_cm": [extent.x, extent.y, extent.z], "min_cm": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z], "max_cm": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z]}
# Required whole-shop fit: S02-S06 longitudinal X envelope, narrow Y footprint centered on Train A, full-height upright shell.
if not (1900 <= bounds["min_cm"][0] <= 2050 and 5550 <= bounds["max_cm"][0] <= 5700):
    failures.append(f"longitudinal X envelope invalid {bounds['min_cm'][0]}..{bounds['max_cm'][0]}")
if not (-4380 <= bounds["min_cm"][1] <= -4320 and -4280 <= bounds["max_cm"][1] <= -4220):
    failures.append(f"Train A Y envelope invalid {bounds['min_cm'][1]}..{bounds['max_cm'][1]}")
if not (1000 <= bounds["max_cm"][2] <= 1100 and 0 <= bounds["min_cm"][2] <= 50):
    failures.append(f"upright Z envelope invalid {bounds['min_cm'][2]}..{bounds['max_cm'][2]}")
after = api.get_all_level_actors()
train_after = [a for a in after if "LB.PressTrain.Installed.TRAIN_A" in {str(t) for t in a.tags}]
if len(train_before) != 338 or len(train_after) != 338:
    failures.append(f"installed Train A contract changed {len(train_before)}->{len(train_after)}")
if len(bindings) != 5:
    failures.append(f"material bindings {len(bindings)}/5")
if str(component.get_collision_profile_name()) != "NoCollision" or component.get_editor_property("can_ever_affect_navigation"):
    failures.append("shell collision/navigation contract invalid")
if not levels.save_current_level():
    failures.append("save failed")
if sha(BASE_FILE) != base_hash:
    failures.append("protected v288 changed")

payload = {"$schema": "cairnwell/audit/press-shop-train-a-shell-axis-corrected-build-v292/v1", "generated_utc": datetime.now(timezone.utc).isoformat(), "status": "PASS__AXIS_CORRECTED_UPRIGHT_TRAIN_A_SHELL__VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V292_NOT_A_PARENT", "base": BASE, "map": MAP, "base_sha256": base_hash, "map_sha256": sha(MAP_FILE) if MAP_FILE.exists() else None, "shell_asset": ASSET, "shell_transform": {"location_cm": [1600, -4735, 0], "rotation": {"pitch": 0, "yaw": 90, "roll": 0}, "scale": [100, 100, 100]}, "shell_world_bounds": bounds, "material_bindings": bindings, "added_lights": light_labels, "added_cameras": camera_labels, "installed_train_a_actor_count_before": len(train_before), "installed_train_a_actor_count_after": len(train_after), "promotion_authorized": False, "failures": failures}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
