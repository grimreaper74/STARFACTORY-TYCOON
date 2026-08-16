"""Build a fresh direct-v295 Train A material-readability candidate.

This replaces only the presentation shell mesh, applies isolated Train A visual
materials and adds fixed evidence cameras. Runtime, geometry transforms,
collision, navigation and production authority remain inherited and untouched.
"""

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295"
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainAMaterialReadabilityCandidate_v299"
SHELL_ASSET = "/Game/LineBoss/Candidates/PressTrains/TrainA/FabricatedShell_v041/SM_CA_MW_PTA_PresentationShell_v016"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAMaterialReadabilityCandidate_v299.umap"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_train_a_material_readability_build_v299.json"
MAT_DIR = "/Game/LineBoss/Candidates/PressTrains/TrainA/InstalledReadability_v299"

SOURCE_MATERIALS = {
    "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v236/M_CA_MW_PT_ReadableGraphiteCharcoal_v236.M_CA_MW_PT_ReadableGraphiteCharcoal_v236": "graphite",
    "/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyRobotFamily_v017/Materials/M_CA_MW_PTA_WorkedSteel_AssemblyStudyRobotFamily_v017.M_CA_MW_PTA_WorkedSteel_AssemblyStudyRobotFamily_v017": "worked_steel",
    "/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyRobotFamily_v017/Materials/M_CA_MW_PTA_Green_AssemblyStudyRobotFamily_v017.M_CA_MW_PTA_Green_AssemblyStudyRobotFamily_v017": "green",
}

SPECS = {
    "graphite": ("M_CA_MW_PTA_InstalledGraphite_v299", (0.095, 0.115, 0.135), 0.10, 0.70, 0.24),
    "worked_steel": ("M_CA_MW_PTA_InstalledWorkedSteel_v299", (0.22, 0.245, 0.27), 0.32, 0.60, 0.30),
    "green": ("M_CA_MW_PTA_InstalledGreen_v299", (0.025, 0.12, 0.078), 0.08, 0.68, 0.24),
    "shell_green": ("M_CA_MW_PTA_ShellGreen_v299", (0.035, 0.145, 0.095), 0.08, 0.66, 0.24),
    "shell_graphite": ("M_CA_MW_PTA_ShellGraphite_v299", (0.11, 0.13, 0.145), 0.10, 0.70, 0.24),
    "shell_dark": ("M_CA_MW_PTA_ShellDarkMachined_v299", (0.16, 0.18, 0.20), 0.22, 0.64, 0.28),
    "shell_steel": ("M_CA_MW_PTA_ShellMachinedSteel_v299", (0.235, 0.26, 0.285), 0.35, 0.58, 0.30),
    "shell_yellow": ("M_CA_MW_PTA_ShellSafetyYellow_v299", (0.46, 0.22, 0.012), 0.05, 0.62, 0.22),
}

CAMERAS = [
    ("LB_V299_CAM_TrainAOperatorClear", (6285.0, -5390.0, 505.0), (4380.0, -4700.0, 430.0), 55.0),
    ("LB_V299_CAM_TrainAFabricationClear", (5960.0, -5260.0, 615.0), (4210.0, -4705.0, 520.0), 58.0),
    ("LB_V299_CAM_TrainAOverviewClear", (7040.0, -5525.0, 1180.0), (4300.0, -4540.0, 455.0), 61.0),
]

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
mel = unreal.MaterialEditingLibrary


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def create_material(key):
    name, colour, metallic, roughness, specular = SPECS[key]
    path = f"{MAT_DIR}/{name}"
    if library.does_asset_exist(path):
        raise RuntimeError(f"refusing to overwrite {path}")
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(f"could not create {path}")
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -480, -100)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    for value, prop, y in (
        (metallic, unreal.MaterialProperty.MP_METALLIC, 40),
        (roughness, unreal.MaterialProperty.MP_ROUGHNESS, 150),
        (specular, unreal.MaterialProperty.MP_SPECULAR, 260),
    ):
        node = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -480, y)
        node.set_editor_property("r", value)
        mel.connect_material_property(node, "", prop)
    errors = [str(value) for value in mel.recompile_material(material)]
    if errors:
        raise RuntimeError(f"material compile failure {path}: {errors}")
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


if library.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("refusing to overwrite preserved v299")
shell_mesh = library.load_asset(SHELL_ASSET)
if not isinstance(shell_mesh, unreal.StaticMesh):
    raise RuntimeError(f"missing shell {SHELL_ASSET}")
base_hash = sha256(BASE_FILE)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("fresh direct-v295 child failed")

materials = {key: create_material(key) for key in SPECS}
actors = actors_api.get_all_level_actors()
shell = next((actor for actor in actors if actor.get_actor_label() == "LB_V295_PTA_FABRICATED_SHELL_V015"), None)
if shell is None:
    raise RuntimeError("v295 shell actor missing")
if not shell.static_mesh_component.set_static_mesh(shell_mesh):
    raise RuntimeError("v016 shell assignment failed")

slot_keys = []
for index, slot in enumerate(shell_mesh.get_editor_property("static_materials")):
    slot_name = str(slot.material_slot_name).lower()
    if "safetyyellow" in slot_name:
        key = "shell_yellow"
    elif "darkmachined" in slot_name:
        key = "shell_dark"
    elif "machinedsteel" in slot_name:
        key = "shell_steel"
    elif "graphite" in slot_name:
        key = "shell_graphite"
    elif "green" in slot_name:
        key = "shell_green"
    else:
        raise RuntimeError(f"unmapped shell slot {slot_name}")
    shell.static_mesh_component.set_material(index, materials[key])
    slot_keys.append(key)
shell.set_actor_label("LB_V299_PTA_SEGMENTED_MIDTONE_SHELL")
shell.tags = [unreal.Name("LB.Asset.Candidate.v299") if str(tag) == "LB.Asset.Candidate.v295" else tag for tag in shell.tags]
shell.tags = [unreal.Name("LB.PressTrain.PresentationShell.TrainA.v016.v299Materials") if str(tag).startswith("LB.PressTrain.PresentationShell.TrainA") else tag for tag in shell.tags]
shell.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"), True)
shell.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
shell.static_mesh_component.set_editor_property("generate_overlap_events", False)
shell.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)

override_counts = Counter()
train_actor_count = 0
for actor in actors_api.get_all_level_actors():
    if "LB.PressTrain.Installed.TRAIN_A" not in {str(tag) for tag in actor.tags}:
        continue
    train_actor_count += 1
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None or component.static_mesh is None:
        continue
    for index in range(component.get_num_materials()):
        current = component.get_material(index)
        key = SOURCE_MATERIALS.get(current.get_path_name() if current else "")
        if key:
            component.set_material(index, materials[key])
            override_counts[key] += 1

camera_labels = []
for label, location, target, fov in CAMERAS:
    camera = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    if camera is None:
        raise RuntimeError(f"could not spawn {label}")
    camera.set_actor_label(label)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
    camera.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
    camera.tags = [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.TrainA.v299"), unreal.Name("LB.Asset.Candidate.v299"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    camera_labels.append(label)

origin, extent = shell.get_actor_bounds(False, False)
bounds = {"min_cm": [origin.x-extent.x, origin.y-extent.y, origin.z-extent.z], "max_cm": [origin.x+extent.x, origin.y+extent.y, origin.z+extent.z]}
failures = []
if train_actor_count != 338:
    failures.append(f"installed Train A actor contract changed: {train_actor_count}")
if sum(override_counts.values()) < 250:
    failures.append(f"too few inherited Train A material overrides: {dict(override_counts)}")
if len(slot_keys) != 5 or len(set(slot_keys)) != 5:
    failures.append(f"shell slot mapping invalid: {slot_keys}")
if len(camera_labels) != 3:
    failures.append(f"camera contract invalid: {camera_labels}")
if str(shell.static_mesh_component.get_collision_profile_name()) != "NoCollision" or shell.static_mesh_component.get_editor_property("can_ever_affect_navigation"):
    failures.append("shell collision/navigation contract changed")
if not (2000 <= bounds["min_cm"][0] <= 2020 and 5595 <= bounds["max_cm"][0] <= 5620 and -4800 <= bounds["min_cm"][1] <= -4780 and -4710 <= bounds["max_cm"][1] <= -4690):
    failures.append(f"shell operator-face envelope changed: {bounds}")
if not levels.save_current_level():
    failures.append("could not save v299")
if sha256(BASE_FILE) != base_hash:
    failures.append("protected v295 changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-train-a-material-readability-build-v299/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__TRAIN_A_ISOLATED_MIDTONE_READABILITY_CANDIDATE__VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V299_NOT_A_PARENT",
    "base": BASE,
    "map": MAP,
    "base_sha256": base_hash,
    "map_sha256": sha256(MAP_FILE) if MAP_FILE.exists() else None,
    "shell_asset": SHELL_ASSET,
    "shell_world_bounds": bounds,
    "train_a_actor_count": train_actor_count,
    "inherited_material_overrides": dict(override_counts),
    "shell_material_keys": slot_keys,
    "evidence_cameras": camera_labels,
    "unchanged_contracts": ["runtime actors", "transforms", "collision", "navigation", "station authority", "motion bindings", "control-room orchestration", "save authority"],
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.log("LINE_BOSS_PRESS_SHOP_TRAIN_A_MATERIAL_READABILITY_V299_BUILD_PASS")
unreal.SystemLibrary.quit_editor()
