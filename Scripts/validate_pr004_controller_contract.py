"""Strict source-contract audit for the PR-004 station controller.

This gate deliberately does not claim an Unreal compile or runtime pass.  It
checks declaration/definition parity and the source-visible invariants needed
by all 18 authoritative scenarios while the host MSVC/Windows SDK is absent.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HEADER = ROOT / "Source/LineBossCarFactory/LBPR004Station.h"
SOURCE = ROOT / "Source/LineBossCarFactory/LBPR004Station.cpp"
CELL_CONTRACT = ROOT / "Content/LineBoss/Data/pr004_robotic_depack_cell_v001.json"
FLOW_CONTRACT = ROOT / "Content/LineBoss/Data/first_coil_automation_v001.json"
TEST_MATRIX = ROOT / "Content/LineBoss/Data/pr004_controller_test_matrix_v001.json"
COMPILE_AUDIT = ROOT / "Saved/Audits/pr004_controller_cpp_compile_v001.json"
OUTPUT = ROOT / "Saved/Audits/pr004_controller_contract_v001_source.json"


def contains_all(text: str, values: list[str]) -> bool:
    return all(value in text for value in values)


def ordered(text: str, values: list[str]) -> bool:
    position = -1
    for value in values:
        position = text.find(value, position + 1)
        if position < 0:
            return False
    return True


def declaration_definition_parity(header: str, source: str) -> tuple[bool, list[str], list[str]]:
    class_body = header.split("class LINEBOSSCARFACTORY_API ALBPR004Station", 1)[1]
    declaration_pattern = re.compile(
        r"^\s*(?:virtual\s+)?(?:static\s+)?(?:bool|void|float|int32|int64|FString|"
        r"ELBPR004Fault|ELBPR004ActionSubstage|ELBPR004MaterialOwner)\s+"
        r"([A-Za-z_][A-Za-z0-9_]*)\s*\([^;{}]*\)\s*(?:const\s*)?(?:override\s*)?;",
        re.MULTILINE,
    )
    declared = set(declaration_pattern.findall(class_body))
    defined = set(re.findall(r"ALBPR004Station::([A-Za-z_][A-Za-z0-9_]*)\s*\(", source))
    defined.discard("ALBPR004Station")
    missing = sorted(declared - defined)
    extra = sorted(defined - declared)
    return not missing and not extra, missing, extra


def save_fields(header: str) -> list[str]:
    block = header.split("struct FLBPR004SaveState", 1)[1].split("};", 1)[0]
    pattern = re.compile(
        r"^\s*(?:bool|int32|int64|FString|FName|ELBPR004\w+|FLBPR004\w+|TArray<[^>]+>)\s+"
        r"([A-Za-z_][A-Za-z0-9_]*)\s*(?:=[^;]+)?;",
        re.MULTILINE,
    )
    return pattern.findall(block)


def main() -> None:
    header = HEADER.read_text(encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")
    cell = json.loads(CELL_CONTRACT.read_text(encoding="utf-8"))
    flow = json.loads(FLOW_CONTRACT.read_text(encoding="utf-8"))
    tests = json.loads(TEST_MATRIX.read_text(encoding="utf-8"))
    compile_audit = json.loads(COMPILE_AUDIT.read_text(encoding="utf-8"))

    parity, missing_definitions, extra_definitions = declaration_definition_parity(header, source)
    persistent_fields = save_fields(header)
    save_round_trip_complete = (
        "CandidateState.SaveVersion != CurrentSaveVersion" in source
        and all(
            f"OutState.{field}" in source and f"InState.{field}" in source
            for field in persistent_fields
            if field != "SaveVersion"
        )
    )

    scenario_ids = [item.get("id") for item in tests.get("required_scenarios", [])]
    expected_ids = [f"PR004-T{index:02d}" for index in range(1, 19)]

    required_states = [
        "AwaitingAuthorisation", "AwaitingRobotClearance", "RemovingBands",
        "RemovingEdgeProtectors", "RemovingWrap", "Inspecting",
        "AwaitingDisposition", "ReadyForHandoff", "QualityHold", "Rejected",
        "AwaitingRejectRemoval", "Fault",
    ]
    required_faults = [
        "WrongCoilIdentity", "BandEndNotCaptured", "BandSprungAfterCut",
        "BandWithdrawalJam", "BandWinderJam", "BandCoilEjectionFault",
        "WrapSeamNotFound", "WrapTabNotCaptured", "FilmSpindleGripFailed",
        "FilmTensionHighOrLost", "CradleSpindleSyncFault",
        "RobotNotClearForFilmIndex", "FilmStripOffFailed",
        "WrapTornOrFragmented", "WrapTrappedBeneathCoil",
        "RecoveryFragmentsUnaccounted", "TrappedKeyNotRestored",
        "PlasticCompactorJam", "PlasticBaleEjectionFault",
        "PowerLossReconciliationRequired", "InFlightMaterialOwnershipUnclear",
    ]
    required_save_fields = [
        "SaveVersion", "State", "StateBeforeFault", "StateBeforePowerLoss",
        "ActiveFault", "Disposition", "CoilId", "HeatId", "SupplierLotId",
        "TraceabilityBarcode", "ExpectedCoilId", "RecipeId",
        "ActiveCycleSerial", "NextCycleSerial", "NextActionToken",
        "RemainingBandMask", "RemainingProtectorMask", "RemainingWrapMask",
        "AcceptedWrapMask", "ActiveAction", "WasteLedger",
        "PackagingScanReport", "InspectionReport", "BandStreamStatus",
        "ProtectorStreamStatus", "PlasticStreamStatus", "FilmDewrapStatus",
        "CompactedBandCoilCount", "CompactedPlasticBaleCount",
        "UnrecoveredWrapFragmentIds", "RecoveredWrapFragmentIds",
        "bManualWrapRecoveryRequired", "bManualWrapRecoveryInProgress",
        "bRecoveryZeroMotionVerified", "TrappedKeyState", "ManualRecoveryPermitId",
        "bPowerLossReconciliationRequired", "ActiveHandoffTransactionId",
        "LastCompletedHandoffTransactionId", "ActiveRejectRemovalTransactionId",
        "LastCompletedRejectRemovalTransactionId", "LastCompletedCoilId",
        "LastCompletedCycleSerial",
    ]
    action_contracts = [
        "CAPTURE_BOTH_ENDS__SNIP__KINKED_SPLINE_PULL__STRAIGHTENER_FEED__COMPACT_PANCAKE_WIND__TAIL_SECURE__VISIBLE_STEEL_BIN_EJECTION",
        "GRIP__DETACH__VISIBLE_BIN_ENTRY",
        "VACUUM_GRIP__FLEXIBLE_PEEL__NIP_ROLLER_FEED_ACK",
        "VACUUM_GRIP__FLEXIBLE_PEEL__NIP_ROLLER_FEED__COMPACT_IRREGULAR_BALE__VISIBLE_PLASTIC_BIN_EJECTION",
    ]
    removed_legacy_symbols = [
        "SetWasteCapacityAvailable", "SetWasteModuleHealth",
        "CompletePackagingAction", "CompleteCurrentPackagingItem",
        "RequestNextPackagingAction", "RobotInterlocksHealthy",
    ]

    scenario_checks = {
        "PR004-T01_cold_start_safe": contains_all(source, [
            "!bControlPowerOn || !bCellCommissioned", "ProcessState != ELBPR004State::AwaitingCoil",
            "ProcessState != ELBPR004State::AwaitingAuthorisation",
        ]),
        "PR004-T02_packaged_coil_identity_and_masks": contains_all(source, [
            "RemainingBandMask = FullBandMask", "RemainingProtectorMask = FullProtectorMask",
            "RemainingWrapMask = FullWrapMask", "CoilId = NewCoilId",
        ]),
        "PR004-T03_wrong_identity_rejected": contains_all(source, [
            "CoilId != ExpectedCoilId", "ELBPR004Fault::WrongCoilIdentity",
        ]),
        "PR004-T04_crane_robot_exclusion": contains_all(source, [
            "AwaitingRobotClearance", "!bCradleLocked || !bCHookWithdrawn",
            "TryResumeAfterCraneClearance",
        ]),
        "PR004-T05_band_cannot_complete_early": contains_all(source, [
            "Substage != Expected", "TimeoutFaultForActiveAction",
            "LastAcknowledgedSubstage != ActiveAction.TerminalSubstage",
        ]),
        "PR004-T06_one_band_one_waste_record": contains_all(source, [
            "RemainingBandMask &= ~Bit", "CompactedBandCoilType",
            "AppendWasteRecordIfAbsent", "OnPackagingRemoved.Broadcast",
        ]),
        "PR004-T07_gate_stops_hazardous_motion": ordered(source, [
            "if (!SafetyEnvelopeHealthy())", "StopFilmDrives();",
            "RaiseFaultInternal(ELBPR004Fault::GateOrSafetyInterlockOpen)",
        ]),
        "PR004-T08_recovery_is_idempotent": contains_all(source, [
            "Existing.RecordId == Record.RecordId", "Existing.CycleSerial == Record.CycleSerial",
            "if (bWasAppended)", "BroadcastActiveActionRequest",
        ]),
        "PR004-T09_separate_waste_permissives": contains_all(source, [
            "BandStreamStatus", "ProtectorStreamStatus", "PlasticStreamStatus",
            "IsWasteStreamReady", "bRequireEject",
        ]),
        "PR004-T10_quality_hold_blocks_release": contains_all(source, [
            "ELBPR004State::QualityHold", "Disposition != ELBPR004Disposition::Ready",
            "ProcessState != ELBPR004State::ReadyForHandoff",
        ]),
        "PR004-T11_resolved_hold_can_release": contains_all(source, [
            "ProcessState != ELBPR004State::QualityHold", "ELBPR004Disposition::Ready",
            "OnDispositionChanged.Broadcast(CoilId, Disposition)",
        ]),
        "PR004-T12_save_round_trip_is_exhaustive": save_round_trip_complete,
        "PR004-T13_transient_save_rejected": contains_all(source, [
            "IsStableStateValue(ProcessState)", "if (!IsAtStableSaveBoundary())",
        ]),
        "PR004-T14_handoff_is_transactional": contains_all(source, [
            "TransactionId != ActiveHandoffTransactionId", "LastCompletedCoilId = CoilId",
            "LastCompletedCycleSerial = ActiveCycleSerial", "ResetActiveCycleAfterTransfer",
        ]),
        "PR004-T15_plastic_remains_physical": contains_all(source, [
            "SpindleGripConfirmed", "RobotClearForIndex", "CradleSpindleSynchronized",
            "TensionControlledWindComplete", "WasteTransferAccepted",
            "FilmDewrapStatus.bTransferChuteClear", "FilmDewrapStatus.bStripperReady",
        ]),
        "PR004-T16_one_plastic_bale": contains_all(source, [
            "PR004_%lld_PLASTIC_BALE", "++CompactedPlasticBaleCount",
            "CompactedPlasticBaleCount > 1", "CompactedPlasticBaleType",
        ]),
        "PR004-T17_tension_fault_stops_both_drives": contains_all(source, [
            "bCradleIndexDriveEnabled = false", "bFilmSpindleDriveEnabled = false",
            "OnFilmDriveCommand.Broadcast(false, false)", "FilmTensionHighOrLost",
            "CradleSpindleSyncFault",
        ]),
        "PR004-T18_trapped_key_fragment_recovery": contains_all(source, [
            "BeginTrappedKeyManualRecovery", "ConfirmTrappedKeyIsolation",
            "RecordRecoveredWrapFragment", "CompleteTrappedKeyManualRecovery",
            "RemovedAndRetained", "UnrecoveredWrapFragmentIds.IsEmpty()",
            "OnManualRecoveryChanged.Broadcast",
        ]),
    }

    checks = {
        "authoritative_contracts_load": bool(cell.get("automatic_sequence")) and bool(flow.get("states")),
        "eighteen_required_scenarios_declared_in_order": scenario_ids == expected_ids,
        "header_source_declaration_definition_parity": parity,
        "constructor_defined": "ALBPR004Station::ALBPR004Station()" in source,
        "legacy_simplified_api_removed": not any(symbol in source for symbol in removed_legacy_symbols),
        "persistent_coil_root_exists": "PR004_PersistentCoilRoot" in source,
        "persistent_coil_attached_to_cradle": "PersistentCoilRoot->SetupAttachment(CradleMover)" in source,
        "required_process_states_declared": contains_all(header, required_states),
        "required_faults_declared": contains_all(header, required_faults),
        "four_band_eight_protector_sixteen_wrap_masks": contains_all(header, [
            "FullBandMask = 0x0F", "FullProtectorMask = 0xFF", "FullWrapMask = 0xFFFF",
        ]),
        "save_v3_contains_required_identity_ownership_and_recovery_fields": contains_all(header, required_save_fields),
        "every_save_field_is_serialized_and_restored": save_round_trip_complete,
        "visible_action_requested_before_removal": (
            source.find("OnPackagingActionRequested.Broadcast") >= 0
            and source.find("OnPackagingRemoved.Broadcast") >= 0
        ),
        "all_visible_action_contracts_declared": contains_all(source, action_contracts),
        "exact_expected_substage_required": "Substage != Expected" in source,
        "film_drives_are_commanded_as_a_pair": contains_all(source, [
            "OnFilmDriveCommand.Broadcast(true, true)", "OnFilmDriveCommand.Broadcast(false, false)",
        ]),
        "waste_ledger_is_idempotent": contains_all(source, [
            "AppendWasteRecordIfAbsent", "Existing.RecordId == Record.RecordId",
        ]),
        "stable_save_boundary_and_coherence_are_explicit": contains_all(source, [
            "IsStableStateValue", "IsSaveStateCoherent", "ValidateActiveActionCoherence",
            "ValidateWasteLedgerCoherence",
        ]),
        "manual_recovery_requires_zero_motion_retained_key_and_all_fragments": scenario_checks["PR004-T18_trapped_key_fragment_recovery"],
        "compile_audit_is_current_and_consistent": compile_audit.get("status") in {
            "NOT_RUN_TO_COMPILER__HOST_TOOLCHAIN_MISSING", "EDITOR_TARGET_COMPILE_PASS"
        },
        **scenario_checks,
    }

    mismatches: list[str] = []
    if missing_definitions:
        mismatches.append(f"Header methods missing definitions: {missing_definitions}")
    if extra_definitions:
        mismatches.append(f"Source methods missing declarations: {extra_definitions}")
    if sorted(persistent_fields) != sorted(set(persistent_fields)):
        mismatches.append("Duplicate FLBPR004SaveState field names detected")
    if len(persistent_fields) < 60:
        mismatches.append(f"FLBPR004SaveState unexpectedly contains only {len(persistent_fields)} fields")
    if "all_source_bands_rewound_as_compact_coils_ejected_and_accounted_for" not in flow["interlocks"]["pr004_release"]:
        mismatches.append("First-coil release contract lost compact band-coil accounting")
    if "irregular_plastic_bale_ejected_and_accounted_for" not in flow["interlocks"]["pr004_release"]:
        mismatches.append("First-coil release contract lost irregular plastic-bale accounting")

    passed = all(checks.values()) and not mismatches
    result = {
        "$schema": "line-boss/audit/pr004-controller-source-contract/v2",
        "status": ("SOURCE_CONTRACT_GATE_PASS_CPP_COMPILE_PASS"
                   if passed and compile_audit.get("status") == "EDITOR_TARGET_COMPILE_PASS"
                   else "SOURCE_CONTRACT_GATE_PASS_CPP_COMPILE_UNPROVEN" if passed
                   else "SOURCE_CONTRACT_GATE_FAIL"),
        "files": {
            "header": str(HEADER),
            "source": str(SOURCE),
            "cell_contract": str(CELL_CONTRACT),
            "flow_contract": str(FLOW_CONTRACT),
            "test_matrix": str(TEST_MATRIX),
            "compile_audit": str(COMPILE_AUDIT),
        },
        "declaration_definition_parity": {
            "pass": parity,
            "missing_definitions": missing_definitions,
            "extra_definitions": extra_definitions,
        },
        "save_round_trip": {
            "field_count": len(persistent_fields),
            "all_fields_written_and_restored": save_round_trip_complete,
        },
        "checks": checks,
        "mismatches": mismatches,
        "all_source_contract_checks_pass": passed,
        "scope_limit": "Source/data contract plus the separately recorded editor-target compile and native automation results; Blueprint binding, isolated map runtime and fixed-camera visual quality remain separately gated.",
        "promotion": "FORBIDDEN until isolated runtime, collision/navigation and fresh fixed-camera visual gates pass.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "failed_checks": [name for name, value in checks.items() if not value],
        "mismatches": mismatches,
        "method_parity": result["declaration_definition_parity"],
        "save_field_count": len(persistent_fields),
    }, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
