"""Create a fresh v288 child with train-only presentation calibration.

The protected v288 runtime parent is never edited.  This successor changes no
geometry, transform, collision, navigation, station authority, motion binding
or gameplay state.  It adds calibrated train materials, local evidence lights
and fixed inspection cameras for a new visual gate.
"""

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288"
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainPresentationCandidate_v289"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainPresentationCandidate_v289.umap"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_train_presentation_build_v289.json"
MAT_DIR = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v289"

SOURCES = {
    "graphite": "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v236/M_CA_MW_PT_ReadableGraphiteCharcoal_v236.M_CA_MW_PT_ReadableGraphiteCharcoal_v236",
    "worked_steel": "/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyRobotFamily_v017/Materials/M_CA_MW_PTA_WorkedSteel_AssemblyStudyRobotFamily_v017.M_CA_MW_PTA_WorkedSteel_AssemblyStudyRobotFamily_v017",
    "green": "/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyRobotFamily_v017/Materials/M_CA_MW_PTA_Green_AssemblyStudyRobotFamily_v017.M_CA_MW_PTA_Green_AssemblyStudyRobotFamily_v017",
}

CALIBRATIONS = {
    "graphite": {
        "name": "M_CA_MW_PT_InstalledGraphite_v289",
        "color": (0.19, 0.22, 0.25), "metallic": 0.34, "roughness": 0.50, "specular": 0.32,
    },
    "worked_steel": {
        "name": "M_CA_MW_PT_InstalledWorkedSteel_v289",
        "color": (0.34, 0.37, 0.40), "metallic": 0.68, "roughness": 0.34, "specular": 0.42,
    },
    "green": {
        "name": "M_CA_MW_PT_InstalledCairnwellGreen_v289",
        "color": (0.035, 0.20, 0.135), "metallic": 0.24, "roughness": 0.48, "specular": 0.30,
    },
}

CAMERAS = [
    ("LB_V289_CAM_TrainAOperator", (7200.0, -5450.0, 520.0), (4700.0, -4300.0, 360.0), 52.0),
    ("LB_V289_CAM_TrainBOperator", (7200.0, -3750.0, 520.0), (4700.0, -2600.0, 360.0), 52.0),
    ("LB_V289_CAM_TrainCDService", (7250.0, 2200.0, 600.0), (4750.0, -50.0, 380.0), 55.0),
    ("LB_V289_CAM_FourTrainDiagonal", (9000.0, -5850.0, 1120.0), (4800.0, -1700.0, 420.0), 58.0),
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


def create_material(spec):
    path = f"{MAT_DIR}/{spec['name']}"
    if library.does_asset_exist(path):
        raise RuntimeError(f"refusing to overwrite preserved material {path}")
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        spec["name"], MAT_DIR, unreal.Material, unreal.MaterialFactoryNew()
    )
    if material is None:
        raise RuntimeError(f"could not create {path}")
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -480, -100)
    base.set_editor_property("constant", unreal.LinearColor(*spec["color"], 1.0))
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    for value, target, y_value in (
        (spec["metallic"], unreal.MaterialProperty.MP_METALLIC, 40),
        (spec["roughness"], unreal.MaterialProperty.MP_ROUGHNESS, 150),
        (spec["specular"], unreal.MaterialProperty.MP_SPECULAR, 260),
    ):
        node = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -480, y_value)
        node.set_editor_property("r", value)
        mel.connect_material_property(node, "", target)
    compile_errors = [str(value) for value in mel.recompile_material(material)]
    if compile_errors:
        raise RuntimeError(f"material compile error {path}: {compile_errors}")
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
base_hash_before = sha256(BASE_FILE)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

materials = {key: create_material(spec) for key, spec in CALIBRATIONS.items()}
source_to_key = {value: key for key, value in SOURCES.items()}
override_counts = Counter()
override_counts_by_train = {key: Counter() for key in "ABCD"}

for actor in actors_api.get_all_level_actors():
    tags = {str(tag) for tag in actor.tags}
    train_tag = next((tag for tag in tags if tag.startswith("LB.PressTrain.Installed.TRAIN_")), None)
    if train_tag is None:
        continue
    train_id = train_tag.rsplit("_", 1)[-1]
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None or component.static_mesh is None:
        continue
    for slot_index in range(component.get_num_materials()):
        current = component.get_material(slot_index)
        current_path = current.get_path_name() if current else ""
        key = source_to_key.get(current_path)
        if key is None:
            continue
        component.set_material(slot_index, materials[key])
        override_counts[key] += 1
        if train_id in override_counts_by_train:
            override_counts_by_train[train_id][key] += 1

lights = []
for row_id, y_value in enumerate((-4300.0, -2600.0, -900.0, 800.0), 1):
    for bay_id, x_value in enumerate((2600.0, 4400.0, 6200.0), 1):
        light = actors_api.spawn_actor_from_class(
            unreal.PointLight, unreal.Vector(x_value, y_value, 1450.0), unreal.Rotator()
        )
        if light is None:
            raise RuntimeError(f"could not spawn train light {row_id}:{bay_id}")
        label = f"LB_V289_TRAIN_TASK_FILL_{row_id:02d}_{bay_id:02d}"
        light.set_actor_label(label)
        component = light.point_light_component
        component.set_mobility(unreal.ComponentMobility.MOVABLE)
        component.set_editor_properties({
            "intensity": 480.0,
            "attenuation_radius": 1250.0,
            "source_radius": 40.0,
            "light_color": unreal.Color(202, 216, 226, 255),
            "cast_shadows": False,
        })
        light.tags = [
            unreal.Name("LB.Lighting.IndustrialLED.TrainTaskFill"),
            unreal.Name("LB.Lighting.PreviewOnly.NoLuxAuthority"),
            unreal.Name("LB.Asset.Candidate.v289"),
            unreal.Name("LB.Asset.CandidateNotPromoted"),
        ]
        lights.append(label)

cameras = []
for label, location, target, fov in CAMERAS:
    camera = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    if camera is None:
        raise RuntimeError(f"could not spawn {label}")
    camera.set_actor_label(label)
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False
    )
    camera.camera_component.set_editor_properties({
        "field_of_view": fov,
        "aspect_ratio": 16.0 / 9.0,
        "constrain_aspect_ratio": True,
    })
    camera.tags = [
        unreal.Name("LB.Camera.Validation"),
        unreal.Name("LB.Camera.Fixed.TrainPresentation.v289"),
        unreal.Name("LB.Asset.Candidate.v289"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]
    cameras.append(label)

failures = []
expected = {"graphite": 489, "worked_steel": 574, "green": 279}
if dict(override_counts) != expected:
    failures.append(f"material override mismatch expected={expected} actual={dict(override_counts)}")
if any(sum(counter.values()) <= 0 for counter in override_counts_by_train.values()):
    failures.append(f"not all trains recalibrated: {override_counts_by_train}")
if len(lights) != 12:
    failures.append(f"expected 12 train lights, created {len(lights)}")
if len(cameras) != 4:
    failures.append(f"expected 4 cameras, created {len(cameras)}")
if not levels.save_current_level():
    failures.append("could not save v289")
base_hash_after = sha256(BASE_FILE)
if base_hash_before != base_hash_after:
    failures.append("protected v288 parent changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-train-presentation-build-v289/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__TRAIN_PRESENTATION_SUCCESSOR_BUILT__VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "base_sha256_before": base_hash_before,
    "base_sha256_after": base_hash_after,
    "map_sha256": sha256(MAP_FILE) if MAP_FILE.exists() else None,
    "material_overrides": dict(override_counts),
    "material_overrides_by_train": {key: dict(value) for key, value in override_counts_by_train.items()},
    "calibrations": CALIBRATIONS,
    "added_lights": lights,
    "added_cameras": cameras,
    "unchanged_contracts": [
        "geometry", "transforms", "collision", "navigation", "station authority",
        "runtime motion bindings", "control-room orchestration", "save authority",
    ],
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.log("LINE_BOSS_PRESS_SHOP_TRAIN_PRESENTATION_V289_BUILD_PASS")
unreal.SystemLibrary.quit_editor()
