"""Audit PR-005 stable save/restore source invariants without claiming execution."""

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
HEADER = (ROOT / "Source/LineBossCarFactory/LBPR005Station.h").read_text(encoding="utf-8")
CPP = (ROOT / "Source/LineBossCarFactory/LBPR005Station.cpp").read_text(encoding="utf-8")
SAVE_HEADER = (ROOT / "Source/LineBossCarFactory/LBPressShopSaveGame.h").read_text(encoding="utf-8")
CONTRACT = json.loads((ROOT / "Content/LineBoss/Data/pr005_hmi_controller_contract_v001.json").read_text(encoding="utf-8"))
OUTPUT = ROOT / "Saved/Audits/pr005_save_source_v001.json"

checks = {
    "versioned_station_snapshot": "struct FLBPR005SaveState" in HEADER and "Version = 2" in HEADER,
    "legacy_v1_migration_accepted": "SavedState.Version != 1 && SavedState.Version != 2" in CPP,
    "traceability_saved": all(x in HEADER for x in ["FString HeatId", "FString SupplierLotId", "FString TraceabilityBarcode"])
        and all(x in CPP for x in ["Saved.HeatId = HeatId", "Saved.SupplierLotId = SupplierLotId", "Saved.TraceabilityBarcode = TraceabilityBarcode"]),
    "campaign_save_format_v4": "SaveFormatVersion = 4" in SAVE_HEADER,
    "campaign_save_root": "class LINEBOSSCARFACTORY_API ULBPressShopSaveGame" in SAVE_HEADER,
    "campaign_id": "THE_RESTART_PRESS_SHOP" in SAVE_HEADER,
    "capture_declared": "CaptureSaveState() const" in HEADER,
    "restore_declared": "RestoreSaveState(const FLBPR005SaveState& SavedState)" in HEADER,
    "capture_defined": "ALBPR005Station::CaptureSaveState() const" in CPP,
    "restore_defined": "ALBPR005Station::RestoreSaveState" in CPP,
    "rejects_wrong_version": "SavedState.Version != 1 && SavedState.Version != 2" in CPP,
    "rejects_wrong_station": "SavedState.StationId != StationId" in CPP,
    "interrupted_motion_detected": all(x in CPP for x in ["ELBStationState::DryCycle", "ELBStationState::Starting", "ELBStationState::Running", "ELBStationState::Stopping"]),
    "interrupted_motion_stops": "bCertifiedForProduction ? ELBStationState::Idle : ELBStationState::ReadyForTest" in CPP,
    "safety_requires_revalidation": "Checklist.bSafetyCircuitReset = false" in CPP,
    "interrupted_dry_cycle_not_completed": "Checklist.bDryCycleComplete = false" in CPP,
    "power_off_restores_isolated": "MachineState = ELBStationState::Isolated" in CPP,
    "negative_counters_clamped": all(x in CPP for x in ["FMath::Max(0, SavedState.CycleCount)", "FMath::Max(0, SavedState.ScrapCount)"]),
    "transient_phase_not_saved": "PhaseElapsedSeconds" not in SAVE_HEADER,
}
failures = [name for name, passed in checks.items() if not passed]
result = {
    "status": "PASS_SOURCE_ONLY_ROUND_TRIP_UNPROVEN" if not failures else "FAIL",
    "checks": checks,
    "contract_restore_rule": CONTRACT["persistence"]["restore_rule"],
    "failures": failures,
    "scope_limit": "Source invariant audit only. Native compile and in-memory PR-004 to PR-005 traceable round-trip are recorded separately; disk-slot serialization and future-version migration remain unproven.",
    "promotion": False,
}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
raise SystemExit(1 if failures else 0)
