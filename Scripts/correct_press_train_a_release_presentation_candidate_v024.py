"""Create v024: layered materials, restrained states and balanced evidence cameras."""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAReleaseDetailCandidate_v023"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAReleasePresentationCandidate_v024"
MAT_ROOT = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v024"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_release_presentation_v024.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v024 from v023: {TARGET}")


def layered_surface(name, colour_a, colour_b, metallic, rough_a, rough_b, scale):
    path = f"{MAT_ROOT}/{name}"
    material = library.load_asset(path) if library.does_asset_exist(path) else asset_tools.create_asset(
        name, MAT_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(path)
    mel.delete_all_material_expressions(material)
    noise = mel.create_material_expression(material, unreal.MaterialExpressionNoise, -520, 120)
    noise.set_editor_properties({
        "scale": scale, "quality": 2, "levels": 3, "level_scale": 2.15,
        "output_min": 0.12, "output_max": 0.88, "turbulence": True,
    })
    base_a = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -520, -220)
    base_a.set_editor_property("constant", unreal.LinearColor(*colour_a, 1.0))
    base_b = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -520, -120)
    base_b.set_editor_property("constant", unreal.LinearColor(*colour_b, 1.0))
    base_lerp = mel.create_material_expression(material, unreal.MaterialExpressionLinearInterpolate, -220, -160)
    mel.connect_material_expressions(base_a, "", base_lerp, "A")
    mel.connect_material_expressions(base_b, "", base_lerp, "B")
    mel.connect_material_expressions(noise, "", base_lerp, "Alpha")
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -220, 20)
    metal.set_editor_property("r", metallic)
    rough_a_node = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -520, 280)
    rough_a_node.set_editor_property("r", rough_a)
    rough_b_node = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -520, 370)
    rough_b_node.set_editor_property("r", rough_b)
    rough_lerp = mel.create_material_expression(material, unreal.MaterialExpressionLinearInterpolate, -220, 320)
    mel.connect_material_expressions(rough_a_node, "", rough_lerp, "A")
    mel.connect_material_expressions(rough_b_node, "", rough_lerp, "B")
    mel.connect_material_expressions(noise, "", rough_lerp, "Alpha")
    mel.connect_material_property(base_lerp, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(rough_lerp, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def state_surface(name, colour, emissive):
    path = f"{MAT_ROOT}/{name}"
    material = library.load_asset(path) if library.does_asset_exist(path) else asset_tools.create_asset(
        name, MAT_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(path)
    mel.delete_all_material_expressions(material)
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -300, -80)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    emit = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -300, 40)
    emit.set_editor_property("constant", unreal.LinearColor(*emissive, 1.0))
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -300, 145)
    rough.set_editor_property("r", 0.36)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(emit, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


materials = {
    "frame": layered_surface("M_CA_MW_PT_FoundryCharcoalLayered_v024", (0.018, 0.024, 0.026), (0.046, 0.054, 0.056), 0.48, 0.46, 0.67, 0.010),
    "green": layered_surface("M_CA_MW_PT_CairnwellGreenLayered_v024", (0.012, 0.055, 0.038), (0.025, 0.125, 0.085), 0.28, 0.43, 0.62, 0.009),
    "yellow": layered_surface("M_CA_MW_PT_SafetyYellowLayered_v024", (0.30, 0.105, 0.002), (0.62, 0.285, 0.008), 0.20, 0.42, 0.62, 0.013),
    "grey": layered_surface("M_CA_MW_PT_ServiceGreyLayered_v024", (0.075, 0.090, 0.094), (0.145, 0.165, 0.170), 0.40, 0.45, 0.64, 0.008),
    "steel": layered_surface("M_CA_MW_PT_WorkedSteelLayered_v024", (0.12, 0.135, 0.145), (0.27, 0.295, 0.305), 0.90, 0.30, 0.48, 0.015),
    "blue": layered_surface("M_CA_MW_PT_TrainAAccentLayered_v024", (0.010, 0.055, 0.105), (0.025, 0.150, 0.310), 0.27, 0.40, 0.58, 0.010),
    "rubber": layered_surface("M_CA_MW_PT_DarkRubberLayered_v024", (0.005, 0.007, 0.008), (0.018, 0.022, 0.023), 0.02, 0.76, 0.90, 0.020),
    "label": layered_surface("M_CA_MW_PT_LabelWhiteLayered_v024", (0.30, 0.35, 0.34), (0.58, 0.64, 0.62), 0.14, 0.36, 0.52, 0.015),
    "state_green": state_surface("M_CA_MW_PT_StateGreenRestrained_v024", (0.005, 0.12, 0.025), (0.0, 0.12, 0.025)),
    "state_amber": state_surface("M_CA_MW_PT_StateAmberRestrained_v024", (0.24, 0.050, 0.001), (0.22, 0.040, 0.001)),
    "state_red": state_surface("M_CA_MW_PT_StateRedRestrained_v024", (0.20, 0.004, 0.002), (0.17, 0.003, 0.001)),
    "state_blue": state_surface("M_CA_MW_PT_StateBlueRestrained_v024", (0.006, 0.055, 0.20), (0.006, 0.045, 0.17)),
}


def role_for(slot_name):
    value = slot_name.upper().replace("-", "_")
    for token, role in (
        ("STATEAMBER", "state_amber"), ("STATERED", "state_red"),
        ("STATEBLUE", "state_blue"), ("STATEGREEN", "state_green"),
        ("LABELWHITE", "label"), ("DARKRUBBER", "rubber"),
        ("TRAINAACCENT", "blue"), ("WORKEDSTEEL", "steel"),
        ("SERVICEGREY", "grey"), ("SAFETYYELLOW", "yellow"),
        ("CAIRNWELLGREEN", "green"), ("FOUNDRYCHARCOAL", "frame"),
    ):
        if token in value:
            return role
    return None


overrides = Counter()
removed_text = []
camera_values = {}
light_values = Counter()
scope_count = 0
for actor in list(actors_api.get_all_level_actors()):
    actor_tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" not in actor_tags:
        continue
    if "LB.PressTrain.ReleaseDetail.Text" in actor_tags:
        removed_text.append(actor.get_actor_label())
        actors_api.destroy_actor(actor)
        continue
    scope_count += 1
    if "LB.Asset.Candidate.v024" not in actor_tags:
        actor_tags.append("LB.Asset.Candidate.v024")
        actor.set_editor_property("tags", [unreal.Name(tag) for tag in actor_tags])
    if isinstance(actor, unreal.StaticMeshActor) and "LB.Validation.Environment" not in actor_tags:
        mesh = actor.static_mesh_component.static_mesh
        if mesh is not None:
            for slot_index, slot in enumerate(mesh.get_editor_property("static_materials")):
                slot_name = str(slot.get_editor_property("imported_material_slot_name") or slot.get_editor_property("material_slot_name"))
                role = role_for(slot_name)
                if role:
                    actor.static_mesh_component.set_material(slot_index, materials[role])
                    overrides[role] += 1
    if isinstance(actor, unreal.CameraActor) and "LB.Camera.Fixed" in actor_tags:
        bias = 0.78 if actor.get_actor_label() == "CA_MW_PTA_CAM_DieChangeService" else 0.88
        settings = actor.camera_component.get_editor_property("post_process_settings")
        settings.set_editor_properties({
            "override_auto_exposure_method": True,
            "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
            "override_auto_exposure_min_brightness": True,
            "override_auto_exposure_max_brightness": True,
            "auto_exposure_min_brightness": 1.0,
            "auto_exposure_max_brightness": 1.0,
            "override_auto_exposure_bias": True,
            "auto_exposure_bias": bias,
        })
        actor.camera_component.set_editor_property("post_process_settings", settings)
        actor.camera_component.set_editor_property("post_process_blend_weight", 1.0)
        camera_values[actor.get_actor_label()] = bias
    label = actor.get_actor_label()
    if label.startswith("CA_MW_PTA_") and label.endswith("_DieChangeEvidenceLight"):
        actor.get_editor_property("rect_light_component").set_editor_property("intensity", 155.0)
        light_values["service_rect_155"] += 1
    elif label.startswith("CA_MW_PTA_") and label.endswith("_DieChangeDockFill"):
        actor.get_editor_property("point_light_component").set_editor_property("intensity", 125.0)
        light_values["service_point_125"] += 1

service_camera = next(actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == "CA_MW_PTA_CAM_DieChangeService")
service_location = unreal.Vector(1950.0, 2250.0, 540.0)
service_target = unreal.Vector(450.0, 2250.0, 145.0)
service_camera.set_actor_location(service_location, False, False)
service_camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(service_location, service_target), False)
service_camera.camera_component.set_editor_property("field_of_view", 94.0)

failures = []
if len(removed_text) != 12:
    failures.append(f"expected 12 temporary release-detail text actors removed, found {len(removed_text)}")
if scope_count != 133:
    failures.append(f"expected 133 retained scoped actors, found {scope_count}")
if len(camera_values) != 4:
    failures.append(f"expected four fixed-camera exposure overrides, found {len(camera_values)}")
if light_values.get("service_rect_155") != 5 or light_values.get("service_point_125") != 5:
    failures.append(f"service-light count mismatch: {dict(light_values)}")
if not overrides:
    failures.append("no layered material overrides were applied")
if not levels.save_current_level():
    failures.append("could not save v024 release-presentation candidate")
library.save_directory(MAT_ROOT, only_if_is_dirty=False, recursive=True)
report = {
    "$schema": "cairnwell/audit/press-train-a-release-presentation-v024/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V024_LAYERED_MATERIALS_RESTRAINED_STATES_CLEAN_LABEL_HIERARCHY_AND_BALANCED_SERVICE_CAMERA__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V024_RELEASE_PRESENTATION__NOT_PROMOTED"),
    "source_map": SOURCE, "map": TARGET,
    "layered_material_override_counts": dict(overrides),
    "temporary_release_text_removed": removed_text,
    "fixed_camera_exposure_bias": camera_values,
    "service_camera_location_cm": [1950.0, 2250.0, 540.0],
    "service_camera_target_cm": [450.0, 2250.0, 145.0],
    "service_camera_fov_deg": 94.0, "service_light_values": dict(light_values),
    "scope_actor_count": scope_count, "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False, "accepted_pr010_map_changed": False,
    "failures": failures, "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
