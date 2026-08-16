"""Create v014 with CCTV-facing controls and restrained press-train materials."""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_DIR = ROOT / "SourceAssets/PressTrains/Shared/StageDetail_v002"
MANIFEST = json.loads((SOURCE_DIR / "PRESS_TRAIN_STAGE_DETAIL_MANIFEST_v002.json").read_text(encoding="utf-8"))
AUDIT = json.loads((ROOT / "Saved/Audits/PressTrains/press_train_stage_detail_source_audit_v002.json").read_text(encoding="utf-8"))
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressTrainAStageDetailCandidate_v013"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressTrainACCTVMaterialCandidate_v014"
DEST = "/Game/LineBoss/Candidates/PressTrains/Shared/StageDetail_v002"
MAT_ROOT = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v014"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_cctv_material_build_v014.json"
if not str(AUDIT.get("status", "")).startswith("PASS"):
    raise RuntimeError("v002 corrected stage-detail source audit has not passed")
if MANIFEST.get("world_placement") != "TBC_NOT_INVENTED":
    raise RuntimeError("stage-detail source invented world placement")

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(TARGET_MAP):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET_MAP}")

# Import the corrected reusable geometry without changing v001 source or assets.
meshes = {}
for row in MANIFEST["assets"]:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE_DIR / row["file"]), "destination_path": DEST,
        "destination_name": row["asset"], "automated": True,
        "replace_existing": True, "replace_existing_settings": True, "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False, "import_materials": False,
        "import_textures": False, "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "generate_lightmap_u_vs": True, "auto_generate_collision": False,
        "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    asset_tools.import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
for row in MANIFEST["assets"]:
    mesh = library.load_asset(f"{DEST}/{row['asset']}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"v002 stage-detail import missing: {row['asset']}")
    meshes[row["asset"]] = mesh

if not levels.new_level_from_template(TARGET_MAP, SOURCE_MAP):
    raise RuntimeError(f"Could not create v014 from preserved v013: {TARGET_MAP}")


def surface(name, colour, metallic, roughness, emissive=None):
    path = f"{MAT_ROOT}/{name}"
    material = library.load_asset(path) if library.does_asset_exist(path) else asset_tools.create_asset(
        name, MAT_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(f"Could not create {path}")
    mel.delete_all_material_expressions(material)
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -350, -120)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -350, 15)
    metal.set_editor_property("r", metallic)
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -350, 105)
    rough.set_editor_property("r", roughness)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    if emissive is not None:
        emit = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -350, 205)
        emit.set_editor_property("constant", unreal.LinearColor(*emissive, 1.0))
        mel.connect_material_property(emit, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


materials = {
    "frame": surface("M_CA_MW_PT_FoundryCharcoal_v014", (0.010, 0.014, 0.015), 0.42, 0.64),
    "green": surface("M_CA_MW_PT_CairnwellGreen_v014", (0.008, 0.045, 0.032), 0.30, 0.62),
    "yellow": surface("M_CA_MW_PT_SafetyYellow_v014", (0.36, 0.145, 0.002), 0.24, 0.56),
    "grey": surface("M_CA_MW_PT_ServiceGrey_v014", (0.065, 0.078, 0.080), 0.38, 0.64),
    "steel": surface("M_CA_MW_PT_WorkedSteel_v014", (0.16, 0.18, 0.19), 0.90, 0.42),
    "blue": surface("M_CA_MW_PT_TrainAAccent_v014", (0.010, 0.055, 0.105), 0.30, 0.55),
    "glass": surface("M_CA_MW_PT_InspectionGlass_v014", (0.003, 0.018, 0.020), 0.08, 0.26, (0.0, 0.012, 0.014)),
    "screen": surface("M_CA_MW_PT_HMIScreen_v014", (0.002, 0.016, 0.010), 0.02, 0.25, (0.0, 0.20, 0.065)),
    "state": surface("M_CA_MW_PT_StateGreen_v014", (0.003, 0.035, 0.008), 0.02, 0.30, (0.0, 0.42, 0.055)),
    "red": surface("M_CA_MW_PT_EStopRed_v014", (0.36, 0.003, 0.002), 0.10, 0.42),
}


def role_for(slot_name):
    value = slot_name.upper().replace("-", "_")
    for token, role in (
        ("HMISCREEN", "screen"), ("STATEGREEN", "state"), ("ESTOPRED", "red"),
        ("INSPECTIONGLASS", "glass"), ("TRAINAACCENT", "blue"),
        ("WORKEDSTEEL", "steel"), ("SERVICEGREY", "grey"),
        ("SAFETYYELLOW", "yellow"), ("CAIRNWELLGREEN", "green"),
        ("FOUNDRYCHARCOAL", "frame"),
    ):
        if token in value:
            return role
    return "frame"


asset_for_label = {
    "CA_MW_PTA_S01_DestackDetail": "SM_CA_MW_PT_S01DestackDetail_v002",
    "CA_MW_PTA_S07_UnloadInspectDetail": "SM_CA_MW_PT_S07UnloadInspectDetail_v002",
    "CA_MW_PTA_S04_ProcessServiceDetail": "SM_CA_MW_PT_MidTrainProcessService_v002",
    "CA_MW_PTA_S05_ProcessServiceDetail": "SM_CA_MW_PT_MidTrainProcessService_v002",
}
for index in range(1, 8):
    asset_for_label[f"CA_MW_PTA_S{index:02d}_StageServicePack"] = "SM_CA_MW_PT_StageServicePack_v002"

swapped = []
override_counts = Counter()
unknown_slots = []
scope_count = 0
authority_repairs = 0
for actor in actors_api.get_all_level_actors():
    actor_tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" not in actor_tags:
        continue
    scope_count += 1
    if "LB.Authority.WorldPlacement.TBCNotInvented" not in actor_tags:
        actor_tags.append("LB.Authority.WorldPlacement.TBCNotInvented")
        authority_repairs += 1
    if "LB.Asset.Candidate.v014" not in actor_tags:
        actor_tags.append("LB.Asset.Candidate.v014")
    actor.set_editor_property("tags", [unreal.Name(tag) for tag in actor_tags])
    if not isinstance(actor, unreal.StaticMeshActor) or "LB.Validation.Environment" in actor_tags:
        continue
    label = actor.get_actor_label()
    if label in asset_for_label:
        actor.static_mesh_component.set_static_mesh(meshes[asset_for_label[label]])
        swapped.append(label)
    mesh = actor.static_mesh_component.static_mesh
    if mesh is None:
        continue
    for slot_index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(slot.get_editor_property("imported_material_slot_name") or slot.get_editor_property("material_slot_name"))
        role = role_for(slot_name)
        if role == "frame" and "FOUNDRYCHARCOAL" not in slot_name.upper():
            unknown_slots.append({"actor": label, "slot": slot_name, "fallback": role})
        actor.static_mesh_component.set_material(slot_index, materials[role])
        override_counts[role] += 1

failures = []
if len(swapped) != 11:
    failures.append(f"expected 11 v002 mesh swaps, found {len(swapped)}")
if authority_repairs != 7:
    failures.append(f"expected seven inherited authority-tag repairs, found {authority_repairs}")
if not levels.save_current_level():
    failures.append("could not save v014 CCTV/material candidate")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
library.save_directory(MAT_ROOT, only_if_is_dirty=False, recursive=True)
report = {
    "$schema": "cairnwell/audit/press-train-a-cctv-material-build-v014/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V014_CCTV_FACING_CONTROLS_RESTRAINED_MATERIALS_AND_TBC_AUTHORITY_REPAIRED__STATIC_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V014_CCTV_MATERIAL_BUILD__NOT_PROMOTED",
    "source_map": SOURCE_MAP, "map": TARGET_MAP,
    "swapped_stage_detail_count": len(swapped), "swapped_actors": swapped,
    "scoped_actor_count": scope_count, "authority_tag_repairs": authority_repairs,
    "material_override_counts": dict(override_counts), "unknown_slot_fallbacks": unknown_slots,
    "world_placement": "TBC_NOT_INVENTED", "production_map_changed": False,
    "accepted_pr010_map_changed": False, "failures": failures,
    "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
