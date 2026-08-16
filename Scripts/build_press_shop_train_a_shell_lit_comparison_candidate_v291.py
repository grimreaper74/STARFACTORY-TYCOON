"""Fresh direct-v288 Train A shell comparison with local readability calibration."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288"
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainAShellLitComparisonCandidate_v291"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAShellLitComparisonCandidate_v291.umap"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_train_a_shell_lit_comparison_build_v291.json"
MAT_DIR = "/Game/LineBoss/Candidates/PressTrains/TrainA/PresentationShell_v291/Materials"
ASSET = "/Game/LineBoss/Candidates/PressTrains/TrainA/PresentationShell_v035/SM_CA_MW_PTA_PresentationShell_v014"

PALETTE = {
    "green": ("M_CA_MW_PTA_ShellGreen_v291", (0.040, 0.145, 0.105), 0.26, 0.52, 0.34),
    "charcoal": ("M_CA_MW_PTA_ShellGraphite_v291", (0.095, 0.115, 0.125), 0.34, 0.56, 0.32),
    "dark_steel": ("M_CA_MW_PTA_ShellDarkSteel_v291", (0.145, 0.165, 0.175), 0.62, 0.42, 0.40),
    "worked_steel": ("M_CA_MW_PTA_ShellWorkedSteel_v291", (0.225, 0.245, 0.255), 0.70, 0.36, 0.42),
    "yellow": ("M_CA_MW_PTA_ShellSafetyYellow_v291", (0.72, 0.36, 0.012), 0.16, 0.48, 0.34),
}
CAMERAS = [
    ("LB_V291_CAM_TrainAOperatorClear", (5200, -3350, 600), (4200, -4500, 450), 50),
    ("LB_V291_CAM_TrainAFabricationClose", (3300, -3350, 560), (4100, -4500, 455), 47),
    ("LB_V291_CAM_TrainAOverviewClear", (7000, -3450, 920), (4200, -4450, 500), 55),
]
LIGHTS = [(2500, -4550, 1050), (4000, -4550, 1050), (5500, -4550, 1050)]

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()

def material(spec):
    name, colour, metallic, roughness, specular = spec
    path = f"{MAT_DIR}/{name}"
    if lib.does_asset_exist(path):
        raise RuntimeError(f"refusing to overwrite {path}")
    result = tools.create_asset(name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    base = mel.create_material_expression(result, unreal.MaterialExpressionConstant3Vector, -420, -100)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    for value, prop, y in ((metallic, unreal.MaterialProperty.MP_METALLIC, 40), (roughness, unreal.MaterialProperty.MP_ROUGHNESS, 145), (specular, unreal.MaterialProperty.MP_SPECULAR, 250)):
        node = mel.create_material_expression(result, unreal.MaterialExpressionConstant, -420, y)
        node.set_editor_property("r", value)
        mel.connect_material_property(node, "", prop)
    errors = [str(x) for x in mel.recompile_material(result)]
    if errors:
        raise RuntimeError(f"material compile {path}: {errors}")
    lib.save_loaded_asset(result, only_if_is_dirty=False)
    return result

if lib.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("refusing to overwrite v291 evidence")
base_hash = sha(BASE_FILE)
mesh = lib.load_asset(ASSET)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError(ASSET)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("fresh direct-v288 child failed")

materials = {key: material(spec) for key, spec in PALETTE.items()}
before = api.get_all_level_actors()
train_before = [a for a in before if "LB.PressTrain.Installed.TRAIN_A" in {str(t) for t in a.tags}]
shell = api.spawn_actor_from_object(mesh, unreal.Vector(1600, -4300, 0), unreal.Rotator(0, -90, 0), False)
shell.set_actor_label("LB_V291_PTA_PRESENTATION_SHELL_V014")
shell.set_actor_scale3d(unreal.Vector(100, -100, 100))
shell.tags = [unreal.Name(x) for x in ("LB.PressTrain.PresentationShell.TrainA.v014", "LB.PressTrain.TrainA", "LB.Asset.Candidate.v291", "LB.Asset.CandidateNotPromoted", "LB.Collision.NoCollision", "LB.Integration.InheritedHallComparisonOnly")]
component = shell.static_mesh_component
bindings = []
failures = []
for index, slot in enumerate(mesh.get_editor_property("static_materials")):
    name = str(slot.material_slot_name).lower()
    key = "green" if "green" in name else "yellow" if "yellow" in name else "worked_steel" if "workedsteel" in name else "dark_steel" if "dark" in name else "charcoal" if "charcoal" in name else None
    if key is None:
        failures.append(f"unmapped shell slot {index}:{name}")
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
    label = f"LB_V291_LIGHT_TrainA_TaskFill_{index:02d}"
    light.set_actor_label(label)
    light.point_light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    light.point_light_component.set_editor_properties({"intensity": 760.0, "attenuation_radius": 1050.0, "source_radius": 55.0, "light_color": unreal.Color(205, 218, 228, 255), "cast_shadows": False})
    light.tags = [unreal.Name("LB.Lighting.IndustrialLED.TrainATaskFill"), unreal.Name("LB.Lighting.PreviewOnly.NoLuxAuthority"), unreal.Name("LB.Asset.Candidate.v291"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    light_labels.append(label)

camera_labels = []
for label, location, target, fov in CAMERAS:
    camera = api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    camera.set_actor_label(label)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
    camera.camera_component.set_editor_properties({"field_of_view": float(fov), "aspect_ratio": 16 / 9, "constrain_aspect_ratio": True})
    camera.tags = [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.TrainAShell.v291"), unreal.Name("LB.Asset.Candidate.v291"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    camera_labels.append(label)

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

payload = {
    "$schema": "cairnwell/audit/press-shop-train-a-shell-lit-comparison-build-v291/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FRESH_DIRECT_V288_TRAIN_A_LIT_COMPARISON__VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V291_NOT_A_PARENT",
    "base": BASE, "map": MAP, "base_sha256": base_hash,
    "map_sha256": sha(MAP_FILE) if MAP_FILE.exists() else None,
    "shell_asset": ASSET, "shell_transform": {"location_cm": [1600, -4300, 0], "rotation_pyr": [0, -90, 0], "scale": [100, -100, 100]},
    "material_bindings": bindings, "added_lights": light_labels, "added_cameras": camera_labels,
    "measured_column_lines_cm": {"x_pitch": [2000, 4000, 6000, 8000], "y": [-5250, -3750]},
    "installed_train_a_actor_count_before": len(train_before), "installed_train_a_actor_count_after": len(train_after),
    "unchanged_contracts": ["protected v288", "installed Train A actors", "moving authorities", "collision", "navigation", "runtime", "audio", "save authority"],
    "promotion_authorized": False, "failures": failures,
  }
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
