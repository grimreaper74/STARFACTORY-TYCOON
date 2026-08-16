"""Create v036 with exact inherited stage/crown material calibration."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAFacadeMaterialCandidate_v035"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAInheritedFrameMaterialCandidate_v036"
MAT_ROOT = "/Game/LineBoss/Candidates/PressTrains/Shared/EnclosedFacadeMaterials_v035"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_inherited_frame_material_v036.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v036 from v035: {TARGET}")

materials = {
    "CA_MW_ServiceGrey": library.load_asset(f"{MAT_ROOT}/M_CA_MW_PT_EnclosureGreyLayered_v035"),
    "CA_MW_CairnwellGreen": library.load_asset(f"{MAT_ROOT}/M_CA_MW_PT_EnclosureGreenLayered_v035"),
}
if any(material is None for material in materials.values()):
    raise RuntimeError(f"missing retained facade material assets: {materials}")

target_labels = {
    "CA_MW_PTA_S01_DESTACK__LOAD", "CA_MW_PTA_S02_DRAW_PRESS",
    "CA_MW_PTA_S03_SECONDARY_FORM", "CA_MW_PTA_S04_TRIM_PRESS",
    "CA_MW_PTA_S05_PIERCE_PRESS", "CA_MW_PTA_S06_FINAL_RESTRIKE",
    "CA_MW_PTA_S07_UNLOAD__INSPECT",
    *{f"CA_MW_PTA_S{index:02d}_CrownDriveDress" for index in range(2, 7)},
}
reassigned = []
found = []
for actor in actors_api.get_all_level_actors():
    if actor.get_actor_label() not in target_labels:
        continue
    found.append(actor.get_actor_label())
    component = actor.static_mesh_component
    for index, slot_name in enumerate(component.get_material_slot_names()):
        slot = str(slot_name)
        if slot in materials:
            component.set_material(index, materials[slot])
            reassigned.append({
                "actor": actor.get_actor_label(), "slot_index": index,
                "slot": slot, "material": materials[slot].get_path_name(),
            })

scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in tags:
        scope_count += 1
        if "LB.Asset.Candidate.v036" not in tags:
            tags.append("LB.Asset.Candidate.v036")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if set(found) != target_labels or len(reassigned) != 24 or scope_count != 169:
    failures.append(
        f"cardinality mismatch actors={len(found)}/12 reassigned={len(reassigned)}/24 scope={scope_count}/169")
if not levels.save_current_level():
    failures.append("could not save v036 inherited-frame-material candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-inherited-frame-material-v036/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V036_EXACT_SEVEN_STAGE_SHELLS_AND_FIVE_CROWN_PACKS_DARK_INDUSTRIAL_MATERIAL_CALIBRATION__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V036_INHERITED_FRAME_MATERIAL__NOT_PROMOTED"),
    "source_map": SOURCE, "map": TARGET, "material_root": MAT_ROOT,
    "target_actors": sorted(found), "reassigned_slots": reassigned,
    "scope_actor_count": scope_count, "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False, "accepted_pr010_map_changed": False,
    "failures": failures, "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
