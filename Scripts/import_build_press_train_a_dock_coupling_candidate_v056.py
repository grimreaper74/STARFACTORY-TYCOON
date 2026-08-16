"""Build isolated Train A v056 from retained v053.

The candidate combines the warning-clean CrownEndpointPresentation_v003 source
with five stage-local engaged dock-coupling assemblies. It deliberately does
not use the rejected v055 installed-bay experiment as a parent.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
adapter = Path(__file__).with_name("import_replace_press_train_a_crown_endpoint_candidate_v054.py")
code = adapter.read_text(encoding="utf-8")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressTrainAEndpointMaterialStateCandidate_v054",
    "/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v056",
)
code = code.replace("press_train_a_endpoint_material_state_v054", "press_train_a_dock_coupling_evidence_v056")
code = code.replace("endpoint-material-state-v054", "dock-coupling-evidence-v056")
code = code.replace("LB.Asset.Candidate.v054", "LB.Asset.Candidate.v056")
code = code.replace("PRESS_TRAIN_A_V054", "PRESS_TRAIN_A_V056")
code = code.replace("V054", "V056").replace("v054", "v056")
exec(compile(code, str(adapter) + "::v056", "exec"), globals(), globals())

SOURCE = ROOT / "SourceAssets/PressTrains/Shared/DockCouplingEvidence_v001"
MANIFEST = json.loads((SOURCE / "PRESS_TRAIN_DOCK_COUPLING_EVIDENCE_MANIFEST_v001.json").read_text(encoding="utf-8"))
SOURCE_AUDIT = json.loads((ROOT / "Saved/Audits/PressTrains/press_train_dock_coupling_evidence_source_audit_v001.json").read_text(encoding="utf-8"))
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v056"
DEST = "/Game/LineBoss/Candidates/PressTrains/Shared/DockCouplingEvidence_v001"
MAT25 = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v025"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_dock_coupling_evidence_v056.json"

if not str(SOURCE_AUDIT.get("status", "")).startswith("PASS"):
    raise RuntimeError("dock coupling source audit has not passed")
if MANIFEST.get("world_placement") != "TBC_NOT_INVENTED":
    raise RuntimeError("dock coupling source invented world placement")

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

row = MANIFEST["assets"][0]
task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(SOURCE / row["file"]),
    "destination_path": DEST,
    "destination_name": row["asset"],
    "automated": True,
    "replace_existing": True,
    "replace_existing_settings": True,
    "save": True,
})
options = unreal.FbxImportUI()
options.set_editor_properties({
    "import_mesh": True,
    "import_as_skeletal": False,
    "import_materials": False,
    "import_textures": False,
    "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
})
data = options.get_editor_property("static_mesh_import_data")
data.set_editor_properties({
    "combine_meshes": True,
    "convert_scene": True,
    "convert_scene_unit": True,
    "generate_lightmap_u_vs": True,
    "auto_generate_collision": False,
    "remove_degenerates": True,
})
task.set_editor_property("options", options)
tools.import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
mesh = library.load_asset(f"{DEST}/{row['asset']}")
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("dock coupling static mesh import missing")

material_paths = {
    "CA_MW_FoundryCharcoal": f"{MAT25}/M_CA_MW_PT_FoundryCharcoalLayered_v025",
    "CA_MW_CairnwellGreen": f"{MAT25}/M_CA_MW_PT_CairnwellGreenLayered_v025",
    "CA_MW_SafetyYellow": f"{MAT25}/M_CA_MW_PT_SafetyYellowLayered_v025",
    "CA_MW_ServiceGrey": f"{MAT25}/M_CA_MW_PT_ServiceGreyLayered_v025",
    "CA_MW_WorkedSteel": f"{MAT25}/M_CA_MW_PT_WorkedSteelLayered_v025",
    "CA_MW_DarkRubber": f"{MAT25}/M_CA_MW_PT_DarkRubberLayered_v025",
    "CA_MW_TrainAAccent": f"{MAT25}/M_CA_MW_PT_TrainAAccentLayered_v025",
    "CA_MW_StateGreen": f"{MAT25}/M_CA_MW_PT_StateGreenRestrained_v025",
    "CA_MW_LabelWhite": f"{MAT25}/M_CA_MW_PT_LabelWhiteLayered_v025",
}
materials = {name: library.load_asset(path) for name, path in material_paths.items()}
missing_materials = [name for name, material in materials.items() if material is None]
if missing_materials:
    raise RuntimeError(f"dock coupling material mappings missing: {missing_materials}")

carts = {}
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    for stage in ("S02", "S03", "S04", "S05", "S06"):
        if f"LB.PressTrain.ReleaseDetail.{stage}.DieCart" in tags:
            if stage in carts:
                raise RuntimeError(f"duplicate release cart semantic for {stage}")
            carts[stage] = actor
if sorted(carts) != ["S02", "S03", "S04", "S05", "S06"]:
    raise RuntimeError(f"expected release carts S02-S06, found {sorted(carts)}")

created = []
for stage, cart in sorted(carts.items()):
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(), unreal.Rotator())
    actor.set_actor_label(f"CA_MW_PTA_{stage}_DockCouplingEngaged_v056")
    actor.set_actor_transform(cart.get_actor_transform(), False, True)
    actor.tags = [
        unreal.Name("LB.PressTrain.TrainA.Isolated"),
        unreal.Name("LB.Asset.Candidate.v056"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Authority.WorldPlacement.TBC_NOT_INVENTED"),
        unreal.Name("LB.PressTrain.Fixed.DockCouplingEvidence"),
        unreal.Name(f"LB.PressTrain.DockCoupling.{stage}.Engaged"),
        unreal.Name("LB.Collision.NoCollision.Presentation"),
    ]
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    for index, slot in enumerate(row["material_slots"]):
        component.set_material(index, materials[slot])
    created.append({
        "stage": stage,
        "actor": actor.get_actor_label(),
        "cart": cart.get_actor_label(),
        "transform": str(actor.get_actor_transform()),
    })

failures = []
scope = [actor for actor in actors_api.get_all_level_actors()
         if "LB.PressTrain.TrainA.Isolated" in [str(tag) for tag in actor.tags]]
if len(created) != 5:
    failures.append(f"expected five coupling actors, found {len(created)}")
if len(scope) != 185:
    failures.append(f"expected 185 scoped actors, found {len(scope)}")
if not levels.save_current_level():
    failures.append("could not save v056 dock coupling candidate")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

report = {
    "$schema": "cairnwell/audit/press-train-a-dock-coupling-evidence-v056/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V056_WARNING_CLEAN_ENDPOINTS_AND_STAGE_LOCAL_ENGAGED_DOCK_COUPLINGS__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V056_DOCK_COUPLING_EVIDENCE__NOT_PROMOTED"
    ),
    "source_map": "/Game/LineBoss/Maps/LB_PressTrainADieChangeLightingCalibrationCandidate_v053",
    "map": TARGET_MAP,
    "asset_root": DEST,
    "couplings": created,
    "scope_actor_count": len(scope),
    "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False,
    "accepted_pr010_map_changed": False,
    "failures": failures,
    "promotion_authorized": False,
    "press_shop_complete": False,
}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
