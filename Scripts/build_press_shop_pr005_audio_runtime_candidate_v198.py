"""Create an isolated v198 child of retained v197 and audit native PR005 audio bindings."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005RuntimeCageInfillCandidate_v197"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005AudioRuntimeCandidate_v198"
AUDIT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_pr005_audio_runtime_build_v198.json"


def package_file(asset_path):
    return Path(unreal.Paths.project_content_dir()) / (asset_path.removeprefix("/Game/") + ".umap")


def sha256(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


source_file = package_file(SOURCE_MAP)
source_hash_before = sha256(source_file)
if unreal.EditorAssetLibrary.does_asset_exist(TARGET_MAP):
    raise RuntimeError(f"Refusing to overwrite existing isolated candidate: {TARGET_MAP}")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.new_level_from_template(TARGET_MAP, SOURCE_MAP):
    raise RuntimeError(f"Could not clone {SOURCE_MAP} to {TARGET_MAP}")
world = unreal.EditorLevelLibrary.get_editor_world()
stations = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR005Station)
if len(stations) != 1:
    raise RuntimeError(f"Expected exactly one PR005 station, got {len(stations)}")
station = stations[0]
audio_components = station.get_components_by_class(unreal.AudioComponent)
rows = []
for component in audio_components:
    sound = component.get_editor_property("sound")
    rows.append({
        "name": component.get_name(),
        "sound": sound.get_path_name() if sound else None,
        "auto_activate": bool(component.get_editor_property("auto_activate")),
        "allow_spatialization": bool(component.get_editor_property("allow_spatialization")),
        "override_attenuation": bool(component.get_editor_property("override_attenuation")),
        "relative_location_cm": [component.relative_location.x, component.relative_location.y, component.relative_location.z],
    })

expected = {
    "PR005_Audio_HPU": "PR005_HPU_Idle_Loop_v001",
    "PR005_Audio_CoilCar": "PR005_CoilCar_Travel_Loop_v001",
    "PR005_Audio_RollerDrive": "PR005_RollerDrive_Loop_v001",
    "PR005_Audio_StripMotion": "PR005_StripMotion_Loop_v001",
    "PR005_Audio_WarningAlarm": "PR005_WarningAlarm_Loop_v001",
    "PR005_Audio_ActuatorCue": None,
    "PR005_Audio_SafetyCue": None,
    "PR005_Audio_TransportCue": None,
}
by_name = {row["name"]: row for row in rows}
failures = []
for name, expected_sound in expected.items():
    row = by_name.get(name)
    if not row:
        failures.append(f"missing component {name}")
        continue
    if row["auto_activate"]:
        failures.append(f"{name} auto activates")
    if not row["allow_spatialization"] or not row["override_attenuation"]:
        failures.append(f"{name} is not spatialized with explicit attenuation")
    if expected_sound and expected_sound not in (row["sound"] or ""):
        failures.append(f"{name} wrong sound {row['sound']}")

if not levels.save_current_level():
    failures.append("target map save failed")
source_hash_after = sha256(source_file)
if source_hash_after != source_hash_before:
    failures.append("protected v197 package changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-pr005-audio-runtime-build-v198/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__ISOLATED_PR005_AUDIO_RUNTIME_BINDING__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "source_map": SOURCE_MAP,
    "target_map": TARGET_MAP,
    "protected_v197_sha256_before": source_hash_before,
    "protected_v197_sha256_after": source_hash_after,
    "audio_contract": "SourceAssets/PR005/pr005_audio_contract_v001.json",
    "audio_components": rows,
    "one_shot_sources_bound_in_native_station": [
        "PR005_CoilCar_Start_v001", "PR005_CoilCar_Stop_v001", "PR005_Mandrel_Expand_v001",
        "PR005_KeeperArm_Engage_v001", "PR005_GateInterlock_v001", "PR005_ControlledStop_v001",
        "PR005_EmergencyStop_v001",
    ],
    "physical_gate_motion_authority": "TBC_NOT_INVENTED__LOGICAL_INTERLOCK_REMAINS_AUTHORITATIVE",
    "failures": failures,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
if failures:
    raise RuntimeError("; ".join(failures))
unreal.log("LINE_BOSS_PR005_AUDIO_RUNTIME_BUILD_V198_PASS")
unreal.SystemLibrary.quit_editor()
