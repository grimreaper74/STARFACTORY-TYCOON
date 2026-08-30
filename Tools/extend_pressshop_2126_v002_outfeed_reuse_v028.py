"""Add a verified existing conveyor-to-inspection outfeed to the candidate only."""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_outfeed_reuse_v028.json"
TAG = unreal.Name("LB.PressShop.2126.v002.OutfeedReuse.v028")
SOURCES = {
    "powered_conveyor": ("/Game/LineBoss/Developer/Validation/PressTrains/CompleteTrainA_v662/Supports/SM_CA_MW_PTA_S06S07_PoweredConveyor_SupportAsset_06_v661", (8000.0, 0.0, 122.02), 0.0),
    "inspection_unload": ("/Game/LineBoss/Developer/Validation/PressTrains/CompleteTrainA_v662/Supports/SM_CA_MW_PTA_S07_InspectUnload_SupportAsset_11_v661", (12900.0, 0.0, 301.37), 0.0),
    "panel_stillage": ("/Game/LineBoss/Developer/Validation/PressTrains/CompleteTrainA_v662/Supports/SM_CA_MW_PTA_S07_FlatPanelStillage_SupportAsset_05_v661", (16900.0, 1500.0, 55.81), 0.0),
}


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def source_uasset(path):
    relative = path.removeprefix("/Game/").replace("/", "\\") + ".uasset"
    return PROJECT / "Content" / relative


def spawn(label, asset, location, yaw):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw))
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Could not spawn " + label)
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(asset)
    actor.static_mesh_component.set_visibility(True, True)
    actor.static_mesh_component.set_render_in_main_pass(True)
    actor.tags = [TAG, unreal.Name("LB.Reused.VerifiedPressSupport"), unreal.Name("LB.Process.Outfeed")]
    return actor


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
before = digest(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate map")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("v028 outfeed reuse already applied")

placed, source_hashes = [], {}
for role, (path, location, yaw) in SOURCES.items():
    asset = unreal.load_asset(path)
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError("Verified support asset missing: " + path)
    disk_path = source_uasset(path)
    if not disk_path.is_file():
        raise RuntimeError("Source package not found on disk: " + str(disk_path))
    before_asset = digest(disk_path)
    label = "S07 | reused " + role.replace("_", " ")
    actor = spawn(label, asset, location, yaw)
    after_asset = digest(disk_path)
    if before_asset != after_asset:
        raise RuntimeError("Source support asset changed while placing: " + path)
    placed.append({"role": role, "actor": actor.get_actor_label(), "asset": path, "location_cm": list(location), "yaw": yaw})
    source_hashes[path] = before_asset

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate map")
after = digest(PROTECTED)
if before != after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__VERIFIED_OUTFEED_SUPPORT_REUSED",
    "candidate_map": MAP,
    "source_assets_modified": False,
    "placed": placed,
    "source_uasset_sha256": source_hashes,
    "new_machine_geometry": 0,
    "roof_created": False,
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_OUTFEED_REUSE_V028_PASS")
