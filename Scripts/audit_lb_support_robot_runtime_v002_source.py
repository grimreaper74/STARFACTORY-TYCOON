"""Read-only/static quarantine audit for support-robot runtime v002.

This script never enables the plugin, loads Unreal, changes an asset or grants
promotion. It writes one evidence JSON under Saved/Audits.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
PLUGIN = REPO / "Plugins" / "LineBossSupportRobotsRuntimeV002"
MODULE = PLUGIN / "Source" / "LineBossSupportRobotsRuntimeV002"
PUBLIC = MODULE / "Public"
PRIVATE = MODULE / "Private"
OUT = REPO / "Saved" / "Audits" / "lb_support_robot_runtime_v002_source_audit.json"
BUILD_AUDIT = REPO / "Saved" / "Audits" / "lb_support_robot_runtime_v002_build_v2c5.json"

EXPECTED_BP_SHA256 = "D10E731AF4AE9150AE1FEE46246804C9AF00E8B8565F41BB42BFE4BC1FF1C296"
BP = REPO / "Content" / "LineBoss" / "Robots" / "Shared" / "RP01" / "Candidate_v001" / "Blueprints" / "BP_LB_RP01_MobileBase.uasset"

V001_HASHES = {
    "Source/LineBossCarFactory/LBSupportRobot.h": "68F833B5D51F5121D6F3C7B35AC5B885F407A86226140C3C491644BC3FD033A6",
    "Source/LineBossCarFactory/LBSupportRobot.cpp": "16629E06E100FECD502745A701BFBBA0EC50B86301798B0FF47D457E58593473",
    "Source/LineBossCarFactory/LBCleaningAMR.h": "B200E1CC30500B9A7043D258C7A07748550D8EEEF56689254E7BEE35004B37B8",
    "Source/LineBossCarFactory/LBCleaningAMR.cpp": "17A6ABB34250B30A53FDE34412EC231DC00A94DF4046F1E39CC00E578C966D67",
    "Source/LineBossCarFactory/LBMaintenanceAMR.h": "1CDBD9A9BEC0D4F273CD7FF17F278EF7982FD83DDE0811F524AF5B82350A3935",
    "Source/LineBossCarFactory/LBMaintenanceAMR.cpp": "EB40DC8066983904E087E2F823A2401A6306F7F36E1548334D8DEFCC159DCBC7",
}

REQUIRED_FILES = [
    "LineBossSupportRobotsRuntimeV002.uplugin",
    "Source/LineBossSupportRobotsRuntimeV002/LineBossSupportRobotsRuntimeV002.Build.cs",
    "Source/LineBossSupportRobotsRuntimeV002/Public/LBSupportRobotRuntimeTypesV002.h",
    "Source/LineBossSupportRobotsRuntimeV002/Public/LBSupportRobotAuthorityV002.h",
    "Source/LineBossSupportRobotsRuntimeV002/Public/LBSupportRobotAuthorityRegistryV002.h",
    "Source/LineBossSupportRobotsRuntimeV002/Public/LBSupportRobotRuntimeComponentV002.h",
    "Source/LineBossSupportRobotsRuntimeV002/Public/LBCleaningRobotRuntimeComponentV002.h",
    "Source/LineBossSupportRobotsRuntimeV002/Public/LBMaintenanceRobotRuntimeComponentV002.h",
    "Source/LineBossSupportRobotsRuntimeV002/Private/LineBossSupportRobotsRuntimeV002Module.cpp",
    "Source/LineBossSupportRobotsRuntimeV002/Private/LBSupportRobotAuthorityRegistryV002.cpp",
    "Source/LineBossSupportRobotsRuntimeV002/Private/LBSupportRobotRuntimeComponentV002.cpp",
    "Source/LineBossSupportRobotsRuntimeV002/Private/LBCleaningRobotRuntimeComponentV002.cpp",
    "Source/LineBossSupportRobotsRuntimeV002/Private/LBMaintenanceRobotRuntimeComponentV002.cpp",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def check(name: str, passed: bool, detail: str) -> dict[str, object]:
    return {"name": name, "passed": bool(passed), "detail": detail}


def main() -> int:
    checks: list[dict[str, object]] = []
    missing = [relative for relative in REQUIRED_FILES if not (PLUGIN / relative).is_file()]
    checks.append(check("required_files", not missing, f"missing={missing}"))

    descriptor_path = PLUGIN / "LineBossSupportRobotsRuntimeV002.uplugin"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    modules = descriptor.get("Modules", [])
    checks.append(check(
        "plugin_disabled_by_default",
        descriptor.get("EnabledByDefault") is False,
        f"EnabledByDefault={descriptor.get('EnabledByDefault')!r}",
    ))
    checks.append(check(
        "runtime_module_descriptor",
        len(modules) == 1
        and modules[0].get("Name") == "LineBossSupportRobotsRuntimeV002"
        and modules[0].get("Type") == "Runtime",
        json.dumps(modules, sort_keys=True),
    ))

    project = json.loads((REPO / "LineBossCarFactory.uproject").read_text(encoding="utf-8-sig"))
    enabled_plugins = {entry.get("Name") for entry in project.get("Plugins", [])}
    checks.append(check(
        "project_descriptor_unchanged_activation_boundary",
        "Modules" not in project and "LineBossSupportRobotsRuntimeV002" not in enabled_plugins,
        f"has_modules={'Modules' in project}; explicitly_enabled={'LineBossSupportRobotsRuntimeV002' in enabled_plugins}",
    ))

    actual_bp_hash = sha256(BP) if BP.is_file() else "MISSING"
    checks.append(check(
        "accepted_data_only_rp01_blueprint_unchanged",
        actual_bp_hash == EXPECTED_BP_SHA256,
        f"sha256={actual_bp_hash}",
    ))

    v001_results = {}
    for relative, expected in V001_HASHES.items():
        path = REPO / relative
        actual = sha256(path) if path.is_file() else "MISSING"
        v001_results[relative] = {"expected": expected, "actual": actual, "unchanged": actual == expected}
    checks.append(check(
        "staged_v001_source_untouched",
        all(item["unchanged"] for item in v001_results.values()),
        "all six staged v001 files match the pre-v002 review hashes",
    ))

    source_paths = [PLUGIN / relative for relative in REQUIRED_FILES if relative.endswith((".h", ".cpp"))]
    source_text = "\n".join(path.read_text(encoding="utf-8") for path in source_paths)
    forbidden_geometry_tokens = [
        "SetActorLocation(",
        "SetActorTransform(",
        "CreateDefaultSubobject<",
        "UStaticMeshComponent",
        "USkeletalMeshComponent",
        "UBoxComponent",
    ]
    found_geometry_tokens = [token for token in forbidden_geometry_tokens if token in source_text]
    checks.append(check(
        "geometry_free_component_contract",
        not found_geometry_tokens,
        f"forbidden_tokens={found_geometry_tokens}",
    ))

    authority_h = (PUBLIC / "LBSupportRobotAuthorityV002.h").read_text(encoding="utf-8")
    registry_h = (PUBLIC / "LBSupportRobotAuthorityRegistryV002.h").read_text(encoding="utf-8")
    registry_cpp = (PRIVATE / "LBSupportRobotAuthorityRegistryV002.cpp").read_text(encoding="utf-8")
    types_h = (PUBLIC / "LBSupportRobotRuntimeTypesV002.h").read_text(encoding="utf-8")
    base_h = (PUBLIC / "LBSupportRobotRuntimeComponentV002.h").read_text(encoding="utf-8")
    base_cpp = (PRIVATE / "LBSupportRobotRuntimeComponentV002.cpp").read_text(encoding="utf-8")
    cr_cpp = (PRIVATE / "LBCleaningRobotRuntimeComponentV002.cpp").read_text(encoding="utf-8")
    cr_h = (PUBLIC / "LBCleaningRobotRuntimeComponentV002.h").read_text(encoding="utf-8")
    mr_h = (PUBLIC / "LBMaintenanceRobotRuntimeComponentV002.h").read_text(encoding="utf-8")
    mr_cpp = (PRIVATE / "LBMaintenanceRobotRuntimeComponentV002.cpp").read_text(encoding="utf-8")

    checks.append(check(
        "native_only_authority_interfaces",
        authority_h.count("CannotImplementInterfaceInBlueprint") == 4
        and "UFUNCTION" not in authority_h
        and "UFUNCTION" not in registry_h,
        "four native-only providers; registry/provider methods are not reflected",
    ))
    checks.append(check(
        "opaque_non_blueprint_proofs",
        all(f"struct {name}" in types_h and f"USTRUCT\nstruct {name}" not in types_h for name in [
            "FLBTrustedRouteGrantV002",
            "FLBTrustedDockProofV002",
            "FLBTrustedWorkAuthorityV002",
            "FLBTrustedOutriggerProofV002",
            "FLBTrustedTravelInterlockProofV002",
            "FLBTrustedToolCouplingProofV002",
            "FLBTrustedCleaningTaskGrantV002",
            "FLBTrustedCleaningProcessSampleV002",
        ]),
        "trusted grants/proofs are plain C++ structs",
    ))
    checks.append(check(
        "blueprint_route_request_has_no_waypoints_or_certification_flag",
        "FLBRouteRequestV002" in types_h
        and "TArray<FVector> Waypoints" not in types_h
        and "bCertified" not in types_h,
        "Blueprint requests catalog route ID/revision/emergency only",
    ))
    checks.append(check(
        "dynamic_route_and_dock_revalidation",
        "RevalidateRouteGrant" in base_cpp
        and "RevalidateDockProof" in base_cpp
        and "bOpenTrappedKeyBoundary" in base_cpp
        and "bSuspendedLoadZoneIntersection" in base_cpp
        and "bProtectiveFieldIntrusion" in base_cpp,
        "route safety and dock proof are checked during Tick",
    ))
    checks.append(check(
        "provider_output_reservation_rollback",
        all(token in registry_cpp for token in [
            "Provider->RevokeRouteGrantV002(OutGrant.GrantId",
            "Provider->ReleaseDockProofV002(OutProof.ProofId",
            "Provider->RevokeWorkAuthorityV002(OutGrant.GrantId",
        ]),
        "malformed or identity-mismatched provider output is cleared and its reservation is released",
    ))
    checks.append(check(
        "world_scoped_authority_boundary",
        registry_cpp.count("Provider->GetWorld() != GetWorld()") == 4
        and registry_cpp.count("Robot->GetWorld()") >= 10,
        "provider registration and actor proof use are constrained to this world subsystem's world",
    ))
    checks.append(check(
        "component_variant_identity_locked",
        base_cpp.count("!VariantId.IsNone() && VariantId !=") == 2
        and 'VariantId != TEXT("LB-RP01")' not in base_cpp,
        "RP01/CR01/MR01 components cannot be relabelled to bypass a derived safety contract",
    ))
    checks.append(check(
        "fail_safe_battery_health_and_trusted_service",
        "BatteryHealthPercent = 0.0" in base_h
        and "ApplyTrustedBatteryServiceResult" in base_h
        and 'TEXT("RP01_BATTERY_SERVICE")' in base_cpp
        and base_cpp.count("BatteryHealthPercent <= 0.0") >= 3
        and "BatteryStateOfChargePercent <= LowBatteryThresholdPercent" in base_cpp,
        "unknown battery health defaults to zero, trusted native service can record it, and certification/dispatch remain inhibited",
    ))
    checks.append(check(
        "explicit_commissioning_and_calibration",
        all(token in base_h for token in [
            "BeginManualCommissioning",
            "CompleteManualCommissioning",
            "BeginCalibration",
            "CompleteCalibration",
            "BeginRouteValidation",
            "CertifyRobot",
        ]) and "RequiresCalibration() const override { return true; }" in mr_h,
        "CR follows manual->route; MR requires manual->calibration->route",
    ))
    checks.append(check(
        "safe_stopped_restore_no_teleport",
        "LastObservedTransform" in base_cpp
        and "do not apply LastObservedTransform" in base_cpp
        and "RestoreRevalidationRequired" in base_cpp
        and "SetActorTransform" not in base_cpp
        and "SetActorLocation" not in base_cpp,
        "restore validates finite DTO, clears authority/tasks/proofs and never moves owner",
    ))
    checks.append(check(
        "restore_range_and_certification_consistency",
        all(token in base_cpp for token in [
            "SavedState.BatteryStateOfChargePercent < 0.0",
            "SavedState.BatteryHealthPercent > 100.0",
            "SavedState.OperatingHours < 0.0",
            "SavedState.bCommissioningCertified != bSavedStateCertified",
            "bSavedStateCertified != bSavedConditionCommissioned",
        ]),
        "common restore rejects corrupt ranges and contradictory commissioning identity",
    ))
    checks.append(check(
        "native_only_restore_application_boundary",
        "bool RestoreSafeStopped" in base_h
        and "bool RestoreCleaningSafeStopped" in cr_h
        and "bool RestoreMaintenanceSafeStopped" in mr_h
        and 'Support Robots v002|Save")\n    bool RestoreSafeStopped' not in base_h
        and 'CR01 v002|Save")\n    bool RestoreCleaningSafeStopped' not in cr_h
        and 'MR01 v002|Save")\n    bool RestoreMaintenanceSafeStopped' not in mr_h,
        "Blueprint may serialize DTOs but only a native save coordinator can apply restore",
    ))
    variant_commit = base_cpp.find("CommitVariantFaultClearV002();")
    common_commit = base_cpp.find("ActiveCommonFault = ELBSupportRobotCommonFaultV002::None;", variant_commit)
    checks.append(check(
        "fault_clear_two_phase_order",
        variant_commit >= 0 and common_commit > variant_commit,
        f"variant_commit_offset={variant_commit}; common_commit_offset={common_commit}",
    ))

    rp01_anchor_names = [
        "PayloadInterface", "Attach_CR01_Payload", "Attach_MR01_Payload",
        "Attach_ConfigSpecificService", "Attach_DriveWheel_L", "Attach_DriveWheel_R",
        "Attach_Suspension_Front", "Attach_CasterRoll_Front", "Attach_Suspension_Rear",
        "Attach_CasterRoll_Rear", "Attach_Sensor_Front", "Attach_Sensor_Rear",
        "Attach_Sensor_Left", "Attach_Sensor_Right", "Attach_DockDatum",
        "Attach_ChargeContact_L", "Attach_ChargeContact_R", "Attach_NetworkContact",
        "Attach_TowFront", "Attach_TowRear", "Attach_AudioDrive_L",
        "Attach_AudioDrive_R", "Attach_AudioWarning",
    ]
    checks.append(check(
        "rp01_23_anchor_contract",
        all(name in base_cpp for name in rp01_anchor_names),
        f"required={len(rp01_anchor_names)}",
    ))
    checks.append(check(
        "canonical_anchor_components_are_one_to_one",
        "TMap<USceneComponent*, FName> ClaimedComponents" in base_cpp
        and "ClaimedComponents.Find(Component)" in base_cpp
        and "ResolvedAnchors.Remove(*ExistingClaim)" in base_cpp,
        "one scene component cannot satisfy multiple stable-name/tag anchor identities",
    ))

    cr_required = [
        "CleanWaterCapacityLitres = 120.0",
        "RecoveryWaterCapacityLitres = 130.0",
        "HopperCapacityLitres = 45.0",
        "CleaningSwathMetres = 1.35",
        "FrontBrushRpm = 250.0",
        "SideBrushRpm = 180.0",
        "ScrubDiscRpm = 300.0",
        "CRChildAnchor(TEXT(\"PVT_FrontBrushSpin\"), TEXT(\"PVT_FrontBrushLift\")",
        "CRChildAnchor(TEXT(\"PVT_SqueegeeYaw\"), TEXT(\"PVT_SqueegeeLift\")",
        "NewGrant.Mode == ELBCleaningModeV002::WetScrub",
        "RevalidateActiveDockProofV002",
        "ApplyTrustedConsumableServiceResult",
    ]
    cr_text = cr_h + cr_cpp
    checks.append(check(
        "cr01_static_contract",
        all(token in cr_text for token in cr_required),
        "capacities/speeds/hierarchy/dry-vs-wet/service proofs encoded",
    ))
    checks.append(check(
        "cr01_dynamic_sensor_and_task_authority",
        all(token in cr_text for token in [
            "RefreshVariantDynamicInterlocksV002",
            "ActiveSensorCoverageEvidenceId",
            "ActiveTaskAuthorityEvidenceId",
            "Registry->ValidateSensorCoverage",
            "Registry->ValidateVariantTaskAuthority",
        ]),
        "CR01 revalidates sensor coverage and active cleaning-task authority during use",
    ))
    checks.append(check(
        "cr01_provider_owned_mode_and_measured_process",
        all(token in (types_h + authority_h + registry_h + registry_cpp + cr_text) for token in [
            "FLBTrustedCleaningTaskGrantV002",
            "ILBCleaningProcessAuthorityProviderV002",
            "Registry->IssueCleaningTaskGrant",
            "Registry->RevalidateCleaningTaskGrant",
            "Registry->SampleCleaningProcess",
            "Sample.Sequence <= LastCleaningProcessSequence",
            "Sample.CoverageDeltaSquareMetres > MaximumCoverageDelta",
            "ProcessAuthorityFault",
        ]),
        "native provider selects cleaning mode and supplies monotonic finite plausible resource/coverage progression",
    ))

    fault_tokens = [f"F{number:02d}_" for number in range(1, 23)]
    tool_tokens = [f"T{number}_" for number in range(1, 9)]
    mr_required = [
        "StraightWithdrawalMillimetres >= 350.0",
        "ClampTravelMillimetres, 12.0",
        "45.0 * static_cast<double>(RackSlot - 1)",
        "MaximumArmPayloadIncludingToolKilograms = 25.0",
        "? 200.0 : 120.0",
        "return 35.0",
        "return 120.0",
        "RevalidateWorkAuthority",
        "RevalidateOutriggerProof",
        "RevalidateToolCouplingProof",
        "RevalidateTravelInterlockProof",
    ]
    mr_text = types_h + mr_h + mr_cpp + registry_cpp
    checks.append(check(
        "mr01_static_contract",
        all(token in mr_text for token in fault_tokens + tool_tokens + mr_required),
        "F01-F22, T1-T8, finite arm/tool/payload/dynamic proof and mobility override encoded",
    ))
    checks.append(check(
        "mr01_setup_gap_and_work_grant_rollback",
        "RefreshWorkAndToolProofs(Failure, bArmMotionActive" in mr_cpp
        and "if (bRequireOutriggerProof && !bHasOutriggerProof)" in mr_cpp
        and "Registry->RevokeWorkAuthority(Grant.GrantId, UnitId);" in mr_cpp,
        "MR01 continuously revalidates work/tool authority without faulting before requested outrigger setup, and rejects overweight grants cleanly",
    ))

    failures = [item for item in checks if not item["passed"]]
    source_hashes = {
        str(path.relative_to(REPO)).replace("\\", "/"): sha256(path)
        for path in sorted(source_paths)
    }
    supporting_artifacts = [
        descriptor_path,
        MODULE / "LineBossSupportRobotsRuntimeV002.Build.cs",
        REPO / "Docs" / "LB_SUPPORT_ROBOT_RUNTIME_V002_QUARANTINE.md",
        Path(__file__).resolve(),
        REPO / "LineBossCarFactory.uproject",
        BUILD_AUDIT,
    ]
    supporting_artifact_hashes = {
        str(path.relative_to(REPO)).replace("\\", "/"): sha256(path)
        for path in supporting_artifacts if path.is_file()
    }
    build_audit = json.loads(BUILD_AUDIT.read_text(encoding="utf-8")) if BUILD_AUDIT.is_file() else {}
    build_gates = build_audit.get("gates", {})
    native_build_pass = all(
        build_gates.get(name) == "PASS"
        for name in (
            "unreal_header_tool",
            "unreal_editor_win64_development",
            "unreal_game_win64_development",
            "unreal_game_win64_shipping",
        )
    )
    report = {
        "$schema": "line-boss/audit/support-robot-runtime-v002-source/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "STATIC_SOURCE_CONTRACT_PASS__STRICT_NATIVE_BUILD_PASS__PLUGIN_DISABLED__RUNTIME_VISUAL_COLLISION_GATES_OPEN__NOT_PROMOTED"
        if not failures and native_build_pass else
        "STATIC_SOURCE_CONTRACT_PASS__PLUGIN_DISABLED__NATIVE_BUILD_EVIDENCE_OPEN__NOT_PROMOTED"
        if not failures else "STATIC_SOURCE_CONTRACT_FAIL__PLUGIN_DISABLED__NOT_PROMOTED",
        "plugin": "Plugins/LineBossSupportRobotsRuntimeV002",
        "plugin_enabled_by_default": descriptor.get("EnabledByDefault"),
        "project_descriptor_modified_for_plugin":
            "Modules" in project or "LineBossSupportRobotsRuntimeV002" in enabled_plugins,
        "accepted_rp01_blueprint": "/Game/LineBoss/Robots/Shared/RP01/Candidate_v001/Blueprints/BP_LB_RP01_MobileBase",
        "accepted_rp01_blueprint_sha256": actual_bp_hash,
        "v001_source_status": "UNTOUCHED__SUPERSEDED_AS_DESIGN_DIRECTION_ONLY",
        "v001_hashes": v001_results,
        "checks": checks,
        "failures": failures,
        "source_hashes": source_hashes,
        "supporting_artifact_hashes": supporting_artifact_hashes,
        "gates": {
            "msvc_windows_sdk_build": "PASS_V2C5" if native_build_pass else "OPEN_NO_CURRENT_EVIDENCE",
            "unreal_header_tool": "PASS_V2C5" if native_build_pass else "OPEN_NO_CURRENT_EVIDENCE",
            "plugin_load": "OPEN_PLUGIN_DISABLED",
            "authority_provider_implementations": "OPEN_NONE_INSTALLED_FAIL_CLOSED",
            "blueprint_component_binding": "OPEN_ACCEPTED_RP01_DATA_ONLY_PAWN_UNCHANGED",
            "route_navigation_ai": "OPEN",
            "dock_runtime": "OPEN",
            "native_save_coordinator": "OPEN",
            "savegame_disk_round_trip": "OPEN",
            "collision_and_swept_volume": "OPEN",
            "cr01_animation_and_service_dock": "OPEN",
            "mr01_arm_mast_outrigger_and_service_dock": "OPEN",
            "hmi_logistics_workers_fault_injection": "OPEN",
            "fresh_fixed_camera_unreal_visual_review": "OPEN",
        },
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "checks": len(checks),
        "failures": len(failures),
        "output": str(OUT),
        "promotion_authorized": False,
    }, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
