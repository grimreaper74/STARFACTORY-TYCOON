"""Build a fresh v374 child with semantic PBR overrides on the four train aggregates.

The imported aggregate meshes deliberately remain immutable.  Their 306 FBX
material slots are overridden per component so repeated imported copies resolve
to the retained Press Shop material library.  Geometry, transforms, collision,
navigation and runtime authority are unchanged.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_WideSpanTrussCandidate_v374"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_WideSpanTrussCandidate_v374.umap"
BASE_SHA = "DDB934BEB76EE377E5E19B36D24C92888AEDC08946774EDC2998FEC58CA06F81"
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainPBRNormalizationCandidate_v383"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainPBRNormalizationCandidate_v383.umap"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_train_pbr_normalization_build_v383.json"
MAT_DIR = "/Game/LineBoss/Candidates/PressTrains/InstalledPBR_v383"

MATERIALS = {
    "green": "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_LayeredCairnwellGreen_v086",
    "graphite": "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_LayeredFoundryCharcoal_v086",
    "steel": "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_MachinedSteel_v086",
    "blank_steel": "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_OiledBlankSteel_v086",
    "yellow": "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_LayeredSafetyYellow_v086",
    "service_grey": "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_LayeredServiceGrey_v086",
    "rubber": "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_Rubber_v086",
    "glass": "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_SensorGlass_v086",
    "white": "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_LabelWhite_v086",
    "screen": "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_HMIScreenOnline_v086",
    "red": "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_EStopRed_v086",
    "blue": "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_DriveBlue_v086",
    "amber": "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_AmberSafetyActive_v086",
}

def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()

def semantic(name):
    value = name.lower()
    if any(token in value for token in ("glass", "lens")):
        return "glass"
    if any(token in value for token in ("screen", "hmi")):
        return "screen"
    if any(token in value for token in ("safetyred", "estop", "redactive")):
        return "red"
    if any(token in value for token in ("vacuumcupblue", "driveblue", "trainablue")):
        return "blue"
    if any(token in value for token in ("amber", "jointorange")):
        return "amber"
    if "copperservice" in value:
        return "copper"
    if any(token in value for token in ("identitywhite", "inspectionwhite", "labelwhite")):
        return "white"
    if any(token in value for token in ("blanksteel", "oiledblank")):
        return "blank_steel"
    if any(token in value for token in ("rubber", "tyre", "tire")):
        return "rubber"
    if any(token in value for token in ("safetyyellow", "processyellow", "assemblyyellow")):
        return "yellow"
    if any(token in value for token in ("cairnwellgreen", "assemblygreen", "identitygreen", "mainstructuregreen")):
        return "green"
    if any(token in value for token in ("machinedsteel", "workedsteel", "transfersteel", "panelsteel")):
        return "steel"
    if any(token in value for token in ("electricalgrey", "servicepanel", "servicegrey")):
        return "service_grey"
    if any(token in value for token in ("charcoal", "graphite", "darkmachined", "robotbody")):
        return "graphite"
    return None

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if sha(BASE_FILE) != BASE_SHA:
    raise RuntimeError("protected v374 base drift")
if library.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("refusing to overwrite preserved v382")
resolved = {key: library.load_asset(path) for key, path in MATERIALS.items()}
missing_assets = [key for key, value in resolved.items() if not isinstance(value, unreal.MaterialInterface)]
if missing_assets:
    raise RuntimeError(f"missing retained material assets: {missing_assets}")
mel = unreal.MaterialEditingLibrary
copper_name = "M_CA_MW_PT_ServiceCopper_v383"
copper_path = f"{MAT_DIR}/{copper_name}"
if library.does_asset_exist(copper_path):
    raise RuntimeError(f"refusing to overwrite {copper_path}")
copper = unreal.AssetToolsHelpers.get_asset_tools().create_asset(copper_name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
if copper is None:
    raise RuntimeError("could not create isolated copper service material")
base_colour = mel.create_material_expression(copper, unreal.MaterialExpressionConstant3Vector, -400, -80)
base_colour.set_editor_property("constant", unreal.LinearColor(0.36, 0.105, 0.035, 1.0))
mel.connect_material_property(base_colour, "", unreal.MaterialProperty.MP_BASE_COLOR)
for value, prop, y in ((0.82, unreal.MaterialProperty.MP_METALLIC, 60), (0.36, unreal.MaterialProperty.MP_ROUGHNESS, 170), (0.42, unreal.MaterialProperty.MP_SPECULAR, 280)):
    node = mel.create_material_expression(copper, unreal.MaterialExpressionConstant, -400, y)
    node.set_editor_property("r", value)
    mel.connect_material_property(node, "", prop)
compile_errors = [str(value) for value in mel.recompile_material(copper)]
if compile_errors:
    raise RuntimeError(f"copper material compile failure: {compile_errors}")
library.save_loaded_asset(copper, only_if_is_dirty=False)
resolved["copper"] = copper
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("fresh v374 child failed")

records = []
totals = Counter()
for actor in actors_api.get_all_level_actors():
    tags = {str(tag) for tag in actor.tags}
    if not any("LB.PressTrain.Train" in tag and ("ProDetail" in tag or "PRO_DETAIL" in tag) for tag in tags):
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh = component.static_mesh if component else None
    if not isinstance(mesh, unreal.StaticMesh) or component.get_num_materials() != 306:
        continue
    counts = Counter()
    unmapped = []
    for index in range(component.get_num_materials()):
        current = component.get_material(index)
        current_name = current.get_name() if current else ""
        key = semantic(current_name)
        if key is None:
            unmapped.append({"slot": index, "material": current_name})
            continue
        component.set_material(index, resolved[key])
        counts[key] += 1
        totals[key] += 1
    records.append({
        "actor": actor.get_actor_label(),
        "mesh": mesh.get_path_name(),
        "slot_count": component.get_num_materials(),
        "semantic_override_counts": dict(counts),
        "unmapped": unmapped,
        "collision": str(component.get_collision_enabled()),
        "nav_affecting": bool(component.get_editor_property("can_ever_affect_navigation")),
    })

failures = []
if len(records) != 4:
    failures.append(f"expected four aggregate train visuals, found {len(records)}")
if any(record["unmapped"] for record in records):
    failures.append("one or more imported material families were not mapped")
if sum(totals.values()) != 4 * 306:
    failures.append(f"override count {sum(totals.values())} != 1224")
if not levels.save_current_level():
    failures.append("could not save v382")
if sha(BASE_FILE) != BASE_SHA:
    failures.append("protected v374 changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-train-pbr-normalization-build-v383/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FOUR_TRAIN_SEMANTIC_PBR_OVERRIDE_CANDIDATE__VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V383_NOT_A_PARENT",
    "base": BASE,
    "base_sha256": BASE_SHA,
    "map": MAP,
    "map_sha256": sha(MAP_FILE) if MAP_FILE.exists() else None,
    "retained_material_library": MATERIALS,
    "isolated_service_copper_material": copper_path,
    "train_records": records,
    "semantic_override_totals": dict(totals),
    "unchanged_contracts": ["source meshes", "geometry", "transforms", "collision", "navigation", "runtime authority", "production state", "save authority"],
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
