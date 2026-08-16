"""Populate authoritative Press Shop support anchors as an isolated v249 child.

This is a presentation candidate. EST-P anchor placement remains TBC and no
engineering capacity, certification or runtime authority is invented.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v249"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v250"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_support_areas_build_v250.json"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v249.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v250.umap"

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

ASSETS = {
    "cabinet": "/Game/LineBoss/IndustrialKit/PressShop/FrontEndDressing/SM_LB_ServiceCabinet_1800_v001",
    "bench": "/Game/LineBoss/IndustrialKit/PressShop/FrontEndDressing/SM_LB_PackagingPrepBench_2400_v001",
    "bin": "/Game/LineBoss/IndustrialKit/PressShop/FrontEndDressing/SM_LB_PackagingRecoveryBin_v001",
    "mast": "/Game/LineBoss/IndustrialKit/PressShop/FrontEndDressing/SM_LB_InspectionMast_3000_v001",
    "bollard": "/Game/LineBoss/IndustrialKit/PressShop/FrontEndDressing/SM_LB_SafetyBollard_1000_v001",
    "estop": "/Game/LineBoss/IndustrialKit/PressShop/FrontEndDressing/SM_LB_EStopPedestal_1300_v001",
    "cart": "/Game/LineBoss/Vendor/FactoryEnvironment/Logistics/Meshes/SM_PalletCart",
    "stillage": "/Game/LineBoss/Vendor/FactoryEnvironment/Logistics/Meshes/SM_PalletCart_PalletBox_open",
    "pallet": "/Game/LineBoss/Vendor/FactoryEnvironment/Logistics/Meshes/SM_PlasticPallet01",
    "crate": "/Game/LineBoss/Vendor/FactoryEnvironment/Logistics/Meshes/SM_AssemblyLineCrate01",
}

ANCHORS = {
    "PR041_TRIM_SCRAP_BALER_TBC": (-8800.0, 4200.0),
    "MAINT_WORKSHOP_TBC": (-5800.0, 4500.0),
    "UTIL_MONITORING_TBC": (-900.0, 4500.0),
    "QLAB_METROLOGY_TBC": (4100.0, 4500.0),
    "PR039_FIRST_OFF_SCAN_TBC": (9900.0, -4600.0),
    "PR040_QUARANTINE_TBC": (9900.0, -3200.0),
    "PR042_DIE_SERVICES_TBC": (7800.0, -2000.0),
    "PR043_STILLAGE_MARSHALLING_TBC": (9900.0, -800.0),
    "PR044_DISPATCH_HANDOFF_TBC": (9900.0, 2000.0),
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


loaded = {}
failures = []
for name, path in ASSETS.items():
    asset = library.load_asset(path)
    if not isinstance(asset, unreal.StaticMesh):
        failures.append(f"missing static mesh {name}: {path}")
    loaded[name] = asset
if failures:
    raise RuntimeError("; ".join(failures))

if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
parent_hash_before = sha256(BASE_FILE)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

added = []


def mesh(area, role, mesh_name, x, y, z, yaw=0.0, scale=(1.0, 1.0, 1.0)):
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(x, y, z), unreal.Rotator(0.0, 0.0, yaw))
    if actor is None:
        failures.append(f"spawn failed {area}/{role}")
        return None
    label = f"LB_WHOLE_V250_{area}_{role}_{len(added)+1:03d}"
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    component = actor.static_mesh_component
    component.set_static_mesh(loaded[mesh_name])
    component.set_mobility(unreal.ComponentMobility.STATIC)
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    component.set_collision_profile_name(unreal.Name("BlockAll"))
    actor.tags = [
        unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.SupportArea.AuthoritativeAnchor.EST-P"),
        unreal.Name(f"LB.SupportArea.{area}"),
        unreal.Name(f"LB.SupportArea.Role.{role}"),
        unreal.Name("LB.Placement.TBC"),
    ]
    added.append({"label": label, "area": area, "role": role, "mesh": mesh_name,
                  "location_cm": [x, y, z], "yaw_deg": yaw})
    return actor


# PR-041: visible segregation/recovery only; a rated baler is not claimed.
x, y = ANCHORS["PR041_TRIM_SCRAP_BALER_TBC"]
for i, dy in enumerate((-320.0, 0.0, 320.0), 1):
    mesh("PR041", f"ScrapRecoveryBin{i}", "bin", x, y + dy, 0.0, 90.0)
mesh("PR041", "SafetyEStop", "estop", x + 260.0, y, 0.0, 90.0)
for dy in (-520.0, 520.0):
    mesh("PR041", "ProtectiveBollard", "bollard", x + 230.0, y + dy, 0.0)

# Maintenance workshop: service benches, cabinets and material carts.
x, y = ANCHORS["MAINT_WORKSHOP_TBC"]
for i, dx in enumerate((-500.0, 0.0, 500.0), 1):
    mesh("MAINT", f"ServiceCabinet{i}", "cabinet", x + dx, y + 390.0, 0.0, 180.0)
for i, dx in enumerate((-330.0, 330.0), 1):
    mesh("MAINT", f"ServiceBench{i}", "bench", x + dx, y - 120.0, 0.0)
mesh("MAINT", "ToolingCart", "cart", x - 480.0, y - 500.0, 63.5, 90.0)
mesh("MAINT", "PartsStillage", "stillage", x + 480.0, y - 500.0, 59.0, 90.0)

# Utilities monitoring point: presentation cabinets only, no invented ratings.
x, y = ANCHORS["UTIL_MONITORING_TBC"]
for i, dx in enumerate((-600.0, -200.0, 200.0, 600.0), 1):
    mesh("UTIL", f"MonitoringCabinet{i}", "cabinet", x + dx, y + 250.0, 0.0, 180.0)
mesh("UTIL", "LocalEStop", "estop", x, y - 240.0, 0.0, 180.0)

# Quality lab: first-pass visual metrology bay using existing inspection assets.
x, y = ANCHORS["QLAB_METROLOGY_TBC"]
mesh("QLAB", "InspectionMast", "mast", x, y + 120.0, 0.0, 180.0)
mesh("QLAB", "MetrologyBench", "bench", x - 420.0, y - 180.0, 0.0)
mesh("QLAB", "ReviewCabinet", "cabinet", x + 440.0, y - 180.0, 0.0, 180.0)
for dx in (-650.0, 650.0):
    mesh("QLAB", "ProtectiveBollard", "bollard", x + dx, y - 500.0, 0.0)

# End-of-line support: inspection, quarantine, die service, marshalling, dispatch.
x, y = ANCHORS["PR039_FIRST_OFF_SCAN_TBC"]
mesh("PR039", "FirstOffInspectionMast", "mast", x - 180.0, y, 0.0, 90.0)
mesh("PR039", "InspectionBench", "bench", x - 520.0, y + 340.0, 0.0, 90.0)
mesh("PR039", "InspectionCabinet", "cabinet", x - 520.0, y - 340.0, 0.0, 90.0)

x, y = ANCHORS["PR040_QUARANTINE_TBC"]
for i, dy in enumerate((-380.0, 0.0, 380.0), 1):
    mesh("PR040", f"QuarantineStillage{i}", "stillage", x - 400.0, y + dy, 59.0, 90.0)
mesh("PR040", "QuarantineEStop", "estop", x - 120.0, y, 0.0, 90.0)

x, y = ANCHORS["PR042_DIE_SERVICES_TBC"]
for i, dy in enumerate((-420.0, 0.0, 420.0), 1):
    mesh("PR042", f"DieServiceStillage{i}", "stillage", x + 260.0, y + dy, 59.0, 90.0)
mesh("PR042", "DieServiceCabinet", "cabinet", x - 280.0, y, 0.0, -90.0)

x, y = ANCHORS["PR043_STILLAGE_MARSHALLING_TBC"]
for i, dy in enumerate((-500.0, 0.0, 500.0), 1):
    mesh("PR043", f"MarshallingStillage{i}", "stillage", x - 450.0, y + dy, 59.0, 90.0)

x, y = ANCHORS["PR044_DISPATCH_HANDOFF_TBC"]
for i, dy in enumerate((-420.0, 0.0, 420.0), 1):
    mesh("PR044", f"DispatchPallet{i}", "pallet", x - 400.0, y + dy, 10.0, 90.0)
    mesh("PR044", f"DispatchCrate{i}", "crate", x - 400.0, y + dy, 30.0, 90.0)
for dy in (-650.0, 650.0):
    mesh("PR044", "DockBollard", "bollard", x - 100.0, y + dy, 0.0)

if len(added) != 45:
    failures.append(f"expected 45 support actors, added {len(added)}")
if not levels.save_current_level():
    failures.append("could not save v250")
parent_hash_after = sha256(BASE_FILE)
if parent_hash_before != parent_hash_after:
    failures.append("protected v249 parent changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-support-areas-build-v250/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__AUTHORITATIVE_EST_P_SUPPORT_ANCHORS_POPULATED_WITH_EXISTING_ASSETS__TBC_PLACEMENT__FRESH_VISUAL_COLLISION_NAV_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "parent_hash_before": parent_hash_before,
    "parent_hash_after": parent_hash_after,
    "map_hash": sha256(MAP_FILE) if MAP_FILE.exists() else None,
    "added_actor_count": len(added),
    "added_actors": added,
    "scope": "Support-area presentation only; no machine, train, authority, lighting, collision-contract or navigation-contract actor changed.",
    "engineering_values_invented": False,
    "placement_status": "TBC at authoritative EST-P anchors",
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
