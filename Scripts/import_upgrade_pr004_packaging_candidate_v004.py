"""Upgrade only PR-004's packaged-coil family from v003 to v004 in Unreal.

This avoids needlessly reparsing the already-proven high-density cradle and
robot FBXs.  It imports 43 independently gated v004 packaging modules, copies
the quarantined v003 validation map, replaces its v003 packaging actors and
saves a new v004 map.  No permanent map or promoted asset is touched.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MANIFEST_PATH = ROOT / "SourceAssets/PR004/PackagingRig_v004/pr004_packaging_rig_candidate_v004_manifest.json"
SOURCE_AUDIT_PATH = ROOT / "Saved/Audits/pr004_packaging_rig_candidate_v004_independent_fbx_uv_audit.json"
FAILED_FULL_IMPORT_LOG = ROOT / "Saved/Logs/PR004_Candidate_v004_Import_Execute.log"
AUDIT_PATH = ROOT / "Saved/Audits/pr004_unreal_import_candidate_v004.json"
DESTINATION = "/Game/LineBoss/Stations/Press/PR004/Candidate_v004/PackagingRig_v004"
SOURCE_MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v003"
DEST_MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v004"
FAMILY = "packaging_v004"

manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
source_audit = json.loads(SOURCE_AUDIT_PATH.read_text(encoding="utf-8"))
if manifest.get("status") != "CANDIDATE_NOT_PROMOTED" or manifest.get("version") != "v004":
    raise RuntimeError("PackagingRig v004 manifest is not a quarantined v004 candidate")
if source_audit.get("technical_pass") is not True or "GATE_PASS" not in source_audit.get("status", ""):
    raise RuntimeError("Independent PackagingRig v004 source gate has not passed")
if len(manifest.get("modules", [])) != 43:
    raise RuntimeError("PackagingRig v004 module count is not 43")
if "ONEDRIVE" in str(ROOT).upper() or any("ONEDRIVE" in module["fbx"].upper() for module in manifest["modules"]):
    raise RuntimeError("Candidate source or project resolved inside OneDrive")

assets = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
tasks = []
for module in manifest["modules"]:
    path = Path(module["fbx"])
    if not path.is_file():
        raise RuntimeError(f"Missing v004 FBX: {path}")
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(path), "destination_path": DESTINATION,
        "destination_name": module["name"], "automated": True,
        "replace_existing": True, "replace_existing_settings": True, "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False,
        "import_materials": False, "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    static_data = options.get_editor_property("static_mesh_import_data")
    static_data.set_editor_properties({
        "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "force_front_x_axis": False, "generate_lightmap_u_vs": False,
        "auto_generate_collision": False, "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    tasks.append(task)

all_packaging_assets_exist = all(
    assets.does_asset_exist(f"{DESTINATION}/{module['name']}") for module in manifest["modules"]
)
if all_packaging_assets_exist:
    unreal.log("LINE_BOSS_PR004_V004_PACKAGING_IMPORT_REUSE 43/43 assets already present from gated first stage")
else:
    for index, task in enumerate(tasks, 1):
        unreal.log(f"LINE_BOSS_PR004_V004_PACKAGING_IMPORT {index}/43 {task.get_editor_property('filename')}")
        tools.import_asset_tasks([task])
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

def material_key(module, slot_name):
    low = (module["name"] + " " + slot_name).lower()
    if "barecoil" in low or "wound" in low or "bore" in low:
        return "CoilSteel"
    if "band" in low or "buckle" in low:
        return "BandSteel"
    if "compactedplastic" in low:
        return "CompactedFilm"
    if "wrap" in low:
        return "DullGreyWrap"
    if "edgeprotector" in low or "formedfibre" in low or "protector" in low:
        return "EdgeProtector"
    if "identitylabel" in low or "label" in low or "ink" in low:
        return "IdentityLabel"
    if "rfid" in low:
        return "MachineDark"
    return "MachineDark"

imported_assets = []
meshes = {}
for module in manifest["modules"]:
    path = f"{DESTINATION}/{module['name']}"
    mesh = assets.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Imported v004 mesh missing: {path}")
    body_setup = mesh.get_editor_property("body_setup")
    if body_setup is None:
        raise RuntimeError(f"Imported v004 mesh lacks BodySetup: {path}")
    body_setup.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    body_setup.modify()
    mesh.modify()
    assignments = []
    for slot in mesh.get_editor_property("static_materials"):
        slot_name = str(slot.get_editor_property("imported_material_slot_name") or slot.get_editor_property("material_slot_name"))
        assignments.append({"slot": slot_name, "material_key": material_key(module, slot_name)})
    assets.save_loaded_asset(mesh, only_if_is_dirty=False)
    meshes[module["name"]] = mesh
    imported_assets.append({
        "family": FAMILY, "module_id": module["asset_id"], "asset": mesh.get_path_name(),
        "source_fbx": module["fbx"],
        "collision_policy": str(body_setup.get_editor_property("collision_trace_flag")),
        "collision_gate": "VALIDATION_COMPLEX_AS_SIMPLE__RELEASE_UCX_OR_PRIMITIVES_REQUIRED",
        "source_material_slot_count": len(assignments),
        "consolidated_material_instance_count": len({item["material_key"] for item in assignments}),
        "opaque_material_assignments": assignments,
    })
assets.save_directory(DESTINATION, only_if_is_dirty=False, recursive=True)

source_map_file = ROOT / "Content/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v003.umap"
dest_map_file = ROOT / "Content/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v004.umap"
if not source_map_file.is_file():
    raise RuntimeError(f"Source v003 validation map missing: {SOURCE_MAP}")
if not dest_map_file.is_file():
    if not assets.duplicate_asset(SOURCE_MAP, DEST_MAP):
        raise RuntimeError(f"Could not duplicate v003 validation map to {DEST_MAP}")
    if not assets.save_asset(DEST_MAP, only_if_is_dirty=False):
        raise RuntimeError(f"Could not persist duplicated v004 validation map {DEST_MAP}")
    # Loading a freshly duplicated UWorld in the same UE 5.8 commandlet
    # process retains a standalone world reference and trips EditorServer's
    # world-leak assertion.  Stage the durable map copy and resume in a clean
    # process; normal reruns skip this branch.
    unreal.log("LINE_BOSS_PR004_V004_MAP_COPY_STAGED__RERUN_FOR_ACTOR_REPLACEMENT")
    raise SystemExit(0)

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(DEST_MAP):
    raise RuntimeError(f"Could not load copied v004 validation map {DEST_MAP}")

removed = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    tags = {str(tag) for tag in actor.get_editor_property("tags")}
    if "LB.SourceFamily.packaging_v003" in tags or "_packaging_v003_" in label:
        removed.append(label)
        actors.destroy_actor(actor)
if len(removed) != 43:
    raise RuntimeError(f"Expected to replace 43 v003 packaging actors, removed {len(removed)}")

candidate_tag = unreal.Name("LB.PR004.ImportCandidate.Candidate_v004")
actor_records = []
spawned = []
bare_actor = None
for module in manifest["modules"]:
    # Each single-object FBX retains and bakes the Blender object transform;
    # all modular meshes therefore share the packaged-coil assembly origin in
    # Unreal.  Applying manifest rest_location_m again double-offsets radial
    # shell, face-wrap, band and protector modules.
    location = unreal.Vector(-280.0, 120.0, 130.5)
    roll, pitch, yaw = [float(value) for value in module["rest_rotation_deg"]]
    rotation = unreal.Rotator(roll=roll, pitch=pitch, yaw=yaw - 90.0)
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    actor.set_actor_label(f"LB_PR004_{FAMILY}_{module['asset_id']}")
    actor.static_mesh_component.set_static_mesh(meshes[module["name"]])
    is_mover = bool(module.get("custom_properties", {}).get("packaging_child")) or module["category"] in {
        "wrap_runtime", "wrap_waste_state", "band_runtime", "band_waste_state"
    }
    actor.static_mesh_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE if is_mover else unreal.ComponentMobility.STATIC)
    initially_visible = not (
        module["category"] in {"wrap_runtime", "wrap_waste_state", "band_runtime", "band_waste_state"}
        or "capturedtail" in module["name"].lower()
    )
    actor.static_mesh_component.set_editor_properties({"visible": initially_visible, "hidden_in_game": not initially_visible})
    actor.set_editor_property("tags", [candidate_tag, unreal.Name("LB.Asset.Candidate.NotPromoted"),
                                       unreal.Name("LB.Station.PR004"), unreal.Name("LB.SourceFamily.packaging_v004")])
    spawned.append(actor)
    if module["category"] == "bare":
        bare_actor = actor
    actor_records.append({
        "family": FAMILY, "module_id": module["asset_id"], "actor": actor.get_actor_label(),
        "location_cm": list(location.to_tuple()), "rotation_deg": [roll, pitch, yaw - 90.0],
        "mobility": "MOVABLE" if is_mover else "STATIC", "initially_visible": initially_visible,
    })

if bare_actor is None:
    raise RuntimeError("v004 packaged-coil root actor was not spawned")
attachments = []
for actor in spawned:
    if actor == bare_actor:
        continue
    actor.attach_to_actor(bare_actor, unreal.Name(""), unreal.AttachmentRule.KEEP_WORLD,
                          unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
    attachments.append({"child": actor.get_actor_label(), "parent": bare_actor.get_actor_label(), "attached": True})

if not levels.save_current_level():
    raise RuntimeError("Could not save v004 packaging-upgrade validation map")

payload = {
    "$schema": "line-boss/audit/pr004-unreal-packaging-upgrade-candidate-v004/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "UNREAL_IMPORT_CANDIDATE_NOT_PROMOTED",
    "strategy": "REUSE_PROVEN_V003_CELL__REPLACE_ONLY_PACKAGING_V004",
    "source_map": SOURCE_MAP, "validation_map": DEST_MAP,
    "destination_root": "/Game/LineBoss/Stations/Press/PR004/Candidate_v004",
    "packaging_destination": DESTINATION,
    "source_full_clone_attempt": {
        "status": "ABORTED_INTERCHANGE_ASSERTION_ON_REUSED_CRADLE__NO_MAP_CREATED",
        "log": str(FAILED_FULL_IMPORT_LOG),
        "new_packaging_implicated": False,
    },
    "imported_asset_count": len(imported_assets), "imported_assets": imported_assets,
    "removed_v003_packaging_actor_count": len(removed), "assembled_actor_count": len(actor_records),
    "assembled_actors": actor_records, "attachments": attachments,
    "collision_policy": "CANDIDATE_COMPLEX_AS_SIMPLE__RELEASE_COLLISION_PENDING",
    "visual_gate": "PENDING_PBR_AND_FRESH_FIXED_CAMERA_REVIEW",
    "promotion_authorized": False,
}
AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
AUDIT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_V004_PACKAGING_UPGRADE_PASS meshes=43 actors=43 map={DEST_MAP} audit={AUDIT_PATH}")
