"""Install the retained native PR-006..PR-010 authorities into v221.

Only native authority actors are added; accepted/corrected presentation already
present in the v221 lineage is not replaced.  v221 and all donors stay immutable.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_WholeShopControlRoomCandidate_v221"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v222"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_playable_management_build_v222.json"

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def rotation(pitch=0.0, yaw=0.0, roll=0.0):
    value = unreal.Rotator()
    value.pitch = pitch
    value.yaw = yaw
    value.roll = roll
    return value


if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
parent_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_WholeShopControlRoomCandidate_v221.umap"
parent_hash_before = sha256(parent_file)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

specs = [
    ("LBPR006Station", "LB_PLAY_V222_PR006_NATIVE_AUTHORITY", (0.0, 0.0, 0.0), 0.0,
     ["LB.Authority.PR006.Native", "LB.Process.PrecisionLevelling", "LB.Station.PR006"]),
    ("LBPR007Station", "LB_PLAY_V222_PR007_NATIVE_AUTHORITY", (0.0, 0.0, 0.0), 0.0,
     ["LB.Authority.PR007.Native", "LB.Process.WashLube", "LB.Station.PR007"]),
    ("LBPR008Station", "LB_PLAY_V222_PR008_NATIVE_AUTHORITY", (0.0, 0.0, 0.0), 0.0,
     ["LB.Authority.PR008.Native", "LB.Process.ServoBlanking", "LB.Station.PR008"]),
    ("LBPR009Station", "LB_PLAY_V222_PR009_NATIVE_AUTHORITY", (600.0, -2000.0, 0.0), -90.0,
     ["LB.Asset.Accepted.PR009.v096", "LB.Authority.PR009.Native", "LB.Process.AutomatedBlankStacking", "LB.Station.PR009"]),
    ("LBPR010Station", "LB_PLAY_V222_PR010_NATIVE_AUTHORITY", (1350.0, -2000.0, 0.0), -90.0,
     ["LB.Asset.Accepted.PR010.v103", "LB.Control.ControlRoomOnly", "LB.RemoteAuthority.CW.MW.CONTROL_ROOM", "LB.Runtime.NativeAuthority", "LB.Save.PR010", "LB.Station.PR010"]),
]

existing_classes = [actor.get_class().get_name() for actor in actors_api.get_all_level_actors()]
failures = []
spawned = []
for class_name, label, location, yaw, source_tags in specs:
    if class_name in existing_classes:
        failures.append(f"parent unexpectedly already contains {class_name}")
        continue
    actor_class = unreal.load_class(None, f"/Script/LineBossCarFactory.{class_name}")
    actor = actors_api.spawn_actor_from_class(
        actor_class, unreal.Vector(*location), rotation(yaw=yaw)) if actor_class else None
    if actor is None:
        failures.append(f"could not spawn {class_name}")
        continue
    actor.set_actor_label(label)
    actor.tags = [unreal.Name(tag) for tag in source_tags + [
        "LB.Integration.PlayableManagement.v222",
        "LB.Asset.Candidate.v222",
        "LB.Asset.CandidateNotPromoted",
    ]]
    spawned.append({"class": class_name, "label": label, "location_cm": list(location), "yaw_deg": yaw})

levels.save_current_level()
parent_hash_after = sha256(parent_file)
if parent_hash_after != parent_hash_before:
    failures.append("protected v221 parent changed")

actors = actors_api.get_all_level_actors()
counts = {}
for actor in actors:
    name = actor.get_class().get_name()
    if name.startswith("LBPR") or name in {"LBPressTrainAStation", "LBControlRoomOperationsConsole", "LBPressShopMaterialFlowController", "PlayerStart"}:
        counts[name] = counts.get(name, 0) + 1
expected = {
    "LBPR004Station": 1, "LBPR005Station": 1, "LBPR006Station": 1,
    "LBPR007Station": 1, "LBPR008Station": 1, "LBPR009Station": 1,
    "LBPR010Station": 1, "LBPressTrainAStation": 4,
    "LBControlRoomOperationsConsole": 1, "LBPressShopMaterialFlowController": 1,
    "PlayerStart": 1,
}
for class_name, count in expected.items():
    if counts.get(class_name, 0) != count:
        failures.append(f"{class_name}: expected {count}, got {counts.get(class_name, 0)}")

map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v222.umap"
payload = {
    "$schema": "cairnwell/audit/press-shop-playable-management-build-v222/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__CURRENT_NATIVE_FRONT_END_AUTHORITIES_AND_FOUR_TRAINS_INSTALLED__EXACT_MAP_RUNTIME_VISUAL_AND_MANAGEMENT_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "parent_hash_before": parent_hash_before,
    "parent_hash_after": parent_hash_after,
    "map_hash": sha256(map_file) if map_file.exists() else None,
    "spawned_authorities": spawned,
    "runtime_authority_counts": counts,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
if failures:
    raise RuntimeError("; ".join(failures))
unreal.log(f"LB_V222_BUILD::{json.dumps(payload)}")

