"""Create v019 with final restrained task-lens and local-light output."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainATaskFixtureCandidate_v018"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAServiceReadabilityCandidate_v019"
MAT_ROOT = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v019"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_service_readability_v019.json"
library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v019 from v018: {TARGET}")

path = f"{MAT_ROOT}/M_CA_MW_PT_TaskLens_v019"
material = library.load_asset(path) if library.does_asset_exist(path) else asset_tools.create_asset(
    "M_CA_MW_PT_TaskLens_v019", MAT_ROOT, unreal.Material, unreal.MaterialFactoryNew())
if material is None:
    raise RuntimeError(path)
mel.delete_all_material_expressions(material)
base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -320, -90)
base.set_editor_property("constant", unreal.LinearColor(0.045, 0.055, 0.052, 1.0))
rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -320, 25)
rough.set_editor_property("r", 0.52)
emit = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -320, 125)
emit.set_editor_property("constant", unreal.LinearColor(0.003, 0.006, 0.004, 1.0))
mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
mel.connect_material_property(emit, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.recompile_material(material)
library.save_loaded_asset(material, only_if_is_dirty=False)

light_count = 0
fixture_count = 0
scope_count = 0
for actor in actors_api.get_all_level_actors():
    actor_tags = [str(tag) for tag in actor.tags]
    if "LB.Validation.LocalTaskLighting" in actor_tags:
        component = actor.get_editor_property("rect_light_component")
        component.set_editor_property("intensity", 25.0)
        component.set_editor_property("attenuation_radius", 300.0)
        light_count += 1
    if isinstance(actor, unreal.StaticMeshActor) and any(tag.endswith("TaskFixture") for tag in actor_tags):
        mesh = actor.static_mesh_component.static_mesh
        for slot_index, slot in enumerate(mesh.get_editor_property("static_materials")):
            slot_name = str(slot.get_editor_property("imported_material_slot_name") or slot.get_editor_property("material_slot_name"))
            if "TASKWHITE" in slot_name.upper():
                actor.static_mesh_component.set_material(slot_index, material)
        fixture_count += 1
    if "LB.PressTrain.TrainA.Isolated" in actor_tags:
        scope_count += 1
        if "LB.Asset.Candidate.v019" not in actor_tags:
            actor_tags.append("LB.Asset.Candidate.v019")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in actor_tags])

failures = []
if light_count != 7 or fixture_count != 7:
    failures.append(f"fixture cardinality mismatch lights={light_count} meshes={fixture_count}")
if not levels.save_current_level():
    failures.append("could not save v019 service-readability candidate")
library.save_directory(MAT_ROOT, only_if_is_dirty=False, recursive=True)
report = {
    "$schema": "cairnwell/audit/press-train-a-service-readability-v019/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V019_INSTALLED_SERVICE_PRESERVED_AND_TASK_FIXTURE_HOTSPOT_RESTRAINED__EARLY_DRAW_CAMERA_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V019_SERVICE_READABILITY__NOT_PROMOTED",
    "source_map": SOURCE, "map": TARGET, "local_task_light_count": light_count,
    "local_task_light_intensity": 25.0, "fixture_lens_count": fixture_count,
    "scope_actor_count": scope_count, "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False, "accepted_pr010_map_changed": False,
    "failures": failures, "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
