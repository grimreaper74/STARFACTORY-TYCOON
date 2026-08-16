"""Rejection audit for the staged v001 LB-RP01/CR01/MR01 runtime code.

The original token-oriented audit was too weak: it could find authority words
without proving that the safety behaviour was trustworthy.  Independent review
found architectural and runtime defects, so v001 is retained only as a dormant
prototype and must never be registered, compiled into the project, or promoted.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Saved" / "Audits" / "support_robot_runtime_source_v001.json"

CR_PACK = ROOT / "SourceAssets" / "ReferencePacks" / "LB_CR01_SHARED_ROBOT_PLATFORM_BUILD_PACK_v1.0"
MR_PACK = ROOT / "SourceAssets" / "ReferencePacks" / "LB_MR01_SHARED_PLATFORM_BUILD_PACK_v1.0"
MR_MOBILITY = ROOT / "SourceAssets" / "Robots" / "LB_MR01_MaintenanceRobot" / "Data" / "MR01_GAMEPLAY_MOBILITY_PROFILE_v001.json"

FILES = {
    "shared_h": ROOT / "Source" / "LineBossCarFactory" / "LBSupportRobot.h",
    "shared_cpp": ROOT / "Source" / "LineBossCarFactory" / "LBSupportRobot.cpp",
    "cr_h": ROOT / "Source" / "LineBossCarFactory" / "LBCleaningAMR.h",
    "cr_cpp": ROOT / "Source" / "LineBossCarFactory" / "LBCleaningAMR.cpp",
    "mr_h": ROOT / "Source" / "LineBossCarFactory" / "LBMaintenanceAMR.h",
    "mr_cpp": ROOT / "Source" / "LineBossCarFactory" / "LBMaintenanceAMR.cpp",
    "save_h": ROOT / "Source" / "LineBossCarFactory" / "LBPressShopSaveGame.h",
    "uproject": ROOT / "LineBossCarFactory.uproject",
}

INDEPENDENT_REVIEW_FINDINGS = [
    "Fault-clear ordering can deadlock CR01 spill and MR01 maintenance recovery.",
    "Caller-authored route structs can forge certification, route health and authority.",
    "Dock/charge proof is not tied to physical alignment, contacts, brakes or network state.",
    "Save restoration trusts transforms, tasks, permits and sensor proofs and can teleport unsafely.",
    "MR01 does not continuously stop arm motion when key safety permissives are lost.",
    "Outrigger proof accepts unvalidated loads before deployment is physically complete.",
    "CR01 can finish a route while water, brushes or cleaning heads remain active.",
    "The native AActor base conflicts with the accepted data-only RP01 Pawn architecture.",
    "Several CR01 spin rates and MR01 motion/tool-change timings differ from pack authority.",
    "NaN and non-finite values are not rejected consistently at runtime and restore boundaries.",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def has_all(text: str, tokens: list[str]) -> tuple[bool, list[str]]:
    missing = [token for token in tokens if token not in text]
    return not missing, missing


def classify_pivots(pack: Path) -> tuple[list[str], list[str]]:
    manifest = {row["unreal_name"]: row for row in csv_rows(pack / "data" / "asset_manifest.csv")}
    robot: list[str] = []
    dock: list[str] = []
    for row in csv_rows(pack / "data" / "moving_parts_pivots.csv"):
        manifest_row = manifest.get(row["asset"], {})
        source_group = manifest_row.get("source_group", "")
        pivot_name = row["pivot_name"]
        is_robot_charge_contact = "DockCharge" in pivot_name
        is_dock_side = source_group.endswith("_Dock") or (pivot_name.startswith("PVT_Dock") and not is_robot_charge_contact)
        target = dock if is_dock_side else robot
        target.append(pivot_name)
    return robot, dock


texts = {name: read(path) for name, path in FILES.items() if name != "uproject"}
combined = "\n".join(texts.values())
uproject = json.loads(read(FILES["uproject"]))
cr_state = json.loads(read(CR_PACK / "data" / "state_machine.json"))
mr_state = json.loads(read(MR_PACK / "data" / "state_machine.json"))
cr_dimensions = json.loads(read(CR_PACK / "data" / "authoritative_dimensions.json"))
mr_dimensions = json.loads(read(MR_PACK / "data" / "authoritative_dimensions.json"))
mr_mobility = json.loads(read(MR_MOBILITY))

cr_robot_pivots, cr_dock_pivots = classify_pivots(CR_PACK)
mr_robot_pivots, mr_dock_pivots = classify_pivots(MR_PACK)

checks: dict[str, dict[str, object]] = {}


def record(name: str, passed: bool, **evidence: object) -> None:
    checks[name] = {"pass": bool(passed), **evidence}


required_files_present = all(path.is_file() for path in FILES.values())
record("required_source_files_present", required_files_present, files=[str(path) for path in FILES.values()])

module_names = [module.get("Name") for module in uproject.get("Modules", [])]
record(
    "native_module_deliberately_unregistered",
    "LineBossCarFactory" not in module_names,
    modules=module_names,
    reason="Authoritative handoff forbids module registration until MSVC and Windows SDK are installed.",
)

shared_tokens = [
    "struct FLBSupportRobotRoute",
    "bool bCertified = false",
    "bool bRouteAuthorityGranted = false",
    "bLocalisationHealthy",
    "bSafetyNetworkHealthy",
    "bRouteClear",
    "Route.bCertified",
    "SetActorLocation(GetActorLocation() + Direction * Travel, true",
    "bRouteAuthorityGranted = false",
    "bRouteRevalidationRequired = true",
    "bLocalisationHealthy = false",
    "bSafetyNetworkHealthy = false",
    "bRouteClear = false",
    "RestoreRevalidationRequired",
]
passed, missing = has_all(texts["shared_h"] + texts["shared_cpp"], shared_tokens)
record("shared_certified_route_and_safe_restore_contract", passed, missing=missing)

save_tokens = [
    "SaveFormatVersion = 3",
    "FLBPR004SaveState PR004",
    "FLBPR005SaveState PR005",
    "TArray<FLBCleaningAMRSaveState> CleaningRobots",
    "TArray<FLBMaintenanceAMRSaveState> MaintenanceRobots",
    "FLBSupportCraneSaveState FrontEndSupportCrane",
]
passed, missing = has_all(texts["save_h"], save_tokens)
record("campaign_save_root_includes_both_robot_fleets", passed, missing=missing)

cr_source = texts["cr_h"] + texts["cr_cpp"]
missing_cr_pivots = [name for name in cr_robot_pivots if name not in cr_source]
record(
    "cr01_robot_side_pivot_contract",
    not missing_cr_pivots and len(cr_robot_pivots) == 27 and len(cr_dock_pivots) == 3,
    robot_pivot_count=len(cr_robot_pivots),
    dock_pivot_count=len(cr_dock_pivots),
    missing_robot_pivots=missing_cr_pivots,
    separate_dock_pivots=cr_dock_pivots,
)

cr_operation = cr_dimensions["cr01"]["operation"]
cr_capacity = cr_dimensions["cr01"]["capacity"]
cr_numeric_tokens = [
    f"CleanWaterCapacityLitres = {float(cr_capacity['clean_water_l']['value']):.1f}f",
    f"RecoveryWaterCapacityLitres = {float(cr_capacity['recovery_water_l']['value']):.1f}f",
    f"HopperCapacityLitres = {float(cr_capacity['dry_hopper_l']['value']):.1f}f",
    f"return {float(cr_operation['normal_cleaning_speed_mps']['value']) * 100.0:.1f}f",
    f"return {float(cr_operation['max_working_speed_mps']['value']) * 100.0:.1f}f",
    "CleaningSwathMetres = 1.35f",
]
passed, missing = has_all(cr_source, cr_numeric_tokens)
record("cr01_capacity_speed_and_swath_contract", passed, expected_tokens=cr_numeric_tokens, missing=missing)

cr_safety_tokens = [
    "bWaterValveOpen = false",
    "bBrushesRunning = false",
    "bCleaningHeadsLowered = false",
    "AbortRoute(false)",
    "ELBSupportRobotFault::SpillDetected",
    "OnWorkOrderRequested.Broadcast",
    "bSpillBoundaryIsolated",
    "bSensorCoverageCertified = false",
    "Never resume water, brush or head motion from disk",
]
passed, missing = has_all(cr_source + texts["shared_cpp"], cr_safety_tokens)
record("cr01_spill_sensor_and_safe_load_actions", passed, missing=missing)

mr_source = texts["mr_h"] + texts["mr_cpp"]
missing_mr_pivots = [name for name in mr_robot_pivots if name not in mr_source]
record(
    "mr01_robot_side_pivot_contract",
    not missing_mr_pivots and len(mr_robot_pivots) == 34 and len(mr_dock_pivots) == 3,
    robot_pivot_count=len(mr_robot_pivots),
    dock_pivot_count=len(mr_dock_pivots),
    missing_robot_pivots=missing_mr_pivots,
    separate_dock_pivots=mr_dock_pivots,
)

fault_rows = csv_rows(MR_PACK / "data" / "fault_matrix.csv")
missing_faults = [row["fault_id"] for row in fault_rows if f"{row['fault_id']}_" not in texts["mr_h"]]
record("mr01_fault_matrix_f01_f22", not missing_faults and len(fault_rows) == 22, row_count=len(fault_rows), missing=missing_faults)

tool_rows = csv_rows(MR_PACK / "data" / "tool_modules.csv")
tool_tokens = [f"{row['tool_id']}_{row['short_name']}" for row in tool_rows]
missing_tools = [token for token in tool_tokens if token not in texts["mr_h"]]
record("mr01_t1_t8_tool_identity", not missing_tools and len(tool_rows) == 8, expected=tool_tokens, missing=missing_tools)

arm_tokens = [
    "PVT_ArmLift", "PVT_ArmJ1", "PVT_ArmJ2", "PVT_ArmJ3", "PVT_ArmJ4", "PVT_ArmJ5", "PVT_ArmJ6", "PVT_ToolClamp",
    "LiftMillimetres > 400.0f", "JointDegrees[0] >= -170.0f", "JointDegrees[1] >= -95.0f",
    "JointDegrees[2] >= -145.0f", "JointDegrees[3] >= -200.0f", "JointDegrees[4] >= -120.0f",
    "StraightWithdrawalMillimetres < 350.0f", "45.0f * static_cast<float>(ToolCarouselSlot - 1)",
    "bToolLocked ? 10.0f : 11.2f",
]
passed, missing = has_all(mr_source, arm_tokens)
record("mr01_arm_tool_change_numeric_contract", passed, missing=missing)

speed_profile = mr_mobility["speed_profiles_mps"]
mr_speed_tokens = [
    f"return {speed_profile['docking'] * 100.0:.1f}f",
    f"return {speed_profile['inspection_approach'] * 100.0:.1f}f",
    f"return {speed_profile['occupied_or_shared_aisle'] * 100.0:.1f}f",
    f"return {speed_profile['normal_factory_transit'] * 100.0:.1f}f",
    f"? {speed_profile['emergency_transit_certified_clear_route'] * 100.0:.1f}f : {speed_profile['normal_factory_transit'] * 100.0:.1f}f",
]
passed, missing = has_all(mr_source, mr_speed_tokens)
record("mr01_user_approved_mobility_profile", passed, expected_tokens=mr_speed_tokens, missing=missing)

mr_permission_tokens = [
    "bArmParked", "bMastStowed", "bAllOutriggersStowed", "bDoorsClosed", "bPartsDrawerClosed", "bPayloadSecured",
    "bParkingBrakeApplied", "bExclusionZoneReserved", "bOutsideSuspendedLoadZone", "AreFootLoadsProved",
    "bTaskAuthorityValid", "bCellPermissionGranted", "bPlayerAuthorisationGranted", "bLOTOValid",
    "ActivePermitId = NAME_None", "bTaskAuthorityValid = false", "bCellPermissionGranted = false",
    "bPlayerAuthorisationGranted = false", "bLOTOValid = false", "bArmMotionActive = false",
]
passed, missing = has_all(mr_source, mr_permission_tokens)
record("mr01_travel_arm_loto_and_safe_load_interlocks", passed, missing=missing)

prohibited_cpp_tokens = ["Welding", "HeavyLift", "SafetyPLCChange", "ProductionReleaseCertification", "ApplyPhysicalLOTO"]
present_prohibited = [token for token in prohibited_cpp_tokens if token in mr_source]
record("mr01_prohibited_actions_not_exposed", not present_prohibited, present=present_prohibited)

expected_cr_states = cr_state["commissioning"] + cr_state["operational"] + cr_state["exceptions"]
expected_mr_states = mr_state["commissioning"] + mr_state["operational"] + mr_state["exceptions"]
all_state_authority = sorted(set(expected_cr_states + expected_mr_states))
record(
    "state_machine_authority_loaded",
    bool(all_state_authority),
    cr01_state_count=len(expected_cr_states),
    mr01_state_count=len(expected_mr_states),
    union=all_state_authority,
)

token_contract_checks_pass = all(entry["pass"] for entry in checks.values())
record(
    "independent_safety_architecture_review",
    False,
    decision="REJECT_V001_AND_SUPERSEDE_WITH_PAWN_ATTACHED_RUNTIME_COMPONENT_V002",
    findings=INDEPENDENT_REVIEW_FINDINGS,
    note="A token match is not behavioural proof and cannot authorize integration.",
)
all_checks_pass = all(entry["pass"] for entry in checks.values())
toolchain = {
    "vswhere_present": Path(r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe").is_file(),
    "windows_sdk_include_present": Path(r"C:\Program Files (x86)\Windows Kits\10\Include").is_dir(),
}
ue_sdk_config_path = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Config\Windows\Windows_SDK.json")
if ue_sdk_config_path.is_file():
    ue_sdk_config = json.loads(read(ue_sdk_config_path))
    toolchain["ue_5_8_local_requirements"] = {
        "main_windows_sdk": ue_sdk_config.get("MainVersion"),
        "minimum_windows_sdk": ue_sdk_config.get("MinVersion"),
        "maximum_windows_sdk": ue_sdk_config.get("MaxVersion"),
        "minimum_visual_studio_2022": ue_sdk_config.get("MinimumVisualStudio2022Version"),
        "preferred_visual_cpp_versions": ue_sdk_config.get("PreferredVisualCppVersions", []),
        "suggested_visual_studio_components": ue_sdk_config.get("VisualStudioSuggestedComponents", []),
        "suggested_vs2022_ltsc_components": ue_sdk_config.get("VisualStudio2022SuggestedComponents", []),
    }
toolchain["native_build_available"] = toolchain["vswhere_present"] and toolchain["windows_sdk_include_present"]

result = {
    "schema_version": "1.0",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "scope": "rejected dormant v001 native support-robot prototype",
    "status": "SOURCE_CONTRACT_REJECTED__SAFETY_ARCHITECTURE_SUPERSEDED",
    "promotion_authorized": False,
    "all_checks_pass": all_checks_pass,
    "token_contract_checks_pass": token_contract_checks_pass,
    "superseded_by": "disabled-by-default Pawn-attached runtime component candidate v002",
    "checks": checks,
    "toolchain": toolchain,
    "open_gates": [
        "replace AActor-owned geometry architecture with an APawn-compatible attached controller",
        "non-forgeable route and dock authority resolved from trusted world services",
        "finite-value validation at every public, sensor and SaveGame boundary",
        "safe stopped restore that clears tasks, permits and sensor proofs and does not blindly teleport",
        "continuous safety-interlock monitoring and correct fault-clear sequencing",
        "MSVC and supported Windows SDK installation",
        "module registration only after toolchain repair",
        "UHT and C++ compile",
        "Blueprint child composition and mesh binding",
        "CR01 and MR01 production dock actors (three dock-side pivots each)",
        "simple collision and articulated swept-volume tests",
        "certified-route runtime and dynamic obstacle tests",
        "tool-change, spill, LOTO, exclusion-zone and fault functional tests",
        "SaveGame disk round trip in fresh processes",
        "fixed-camera Unreal visual comparison against both Pro sheets",
    ],
    "files": {
        name: {"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size}
        for name, path in FILES.items()
    },
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": result["status"], "audit": str(OUT), "checks": checks}, indent=2))
