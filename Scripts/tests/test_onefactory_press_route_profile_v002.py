"""Offline source-contract tests for the save-compatible Press route V002.

These tests deliberately do not launch Unreal. The paired native automation
tests exercise the runtime behaviour when the editor test suite is next built.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "Source" / "LineBossCarFactory"


def read(name: str) -> str:
    return (SOURCE / name).read_text(encoding="utf-8")


class PressRouteProfileV002ContractTests(unittest.TestCase):
    def test_v001_stage_ordinals_are_explicit_and_new_stage_is_append_only(self) -> None:
        header = read("LBOneFactoryProductionFlow.h")
        expected = {
            "InboundCoil": 0,
            "BlankPreparation": 1,
            "Pressing": 2,
            "PressedPanelStillage": 3,
            "BodyFraming": 4,
            "BodyInWhite": 5,
            "BodyQualityInspection": 6,
            "Pretreatment": 7,
            "EDCoat": 8,
            "ColourCoat": 9,
            "Cure": 10,
            "PaintQualityInspection": 11,
            "GeneralAssemblyTrim": 12,
            "PowertrainMarriage": 13,
            "RollingChassis": 14,
            "EndOfLineInspection": 15,
            "FinishedVehicle": 16,
            "Dispatched": 17,
            "PressPanelInspection": 18,
        }
        for stage, ordinal in expected.items():
            self.assertRegex(header, rf"\b{stage}\s*=\s*{ordinal}\b")

    def test_production_semantics_make_press_inspection_a_real_gate(self) -> None:
        source = read("LBOneFactoryProductionFlow.cpp")
        self.assertIn(
            "case ELBOneFactoryVehicleStage::PressPanelInspection:", source
        )
        self.assertIn(
            "OutStage = ELBOneFactoryVehicleStage::PressPanelInspection; return true;",
            source,
        )
        self.assertIn(
            "InStage == ELBOneFactoryVehicleStage::PressPanelInspection", source
        )
        self.assertRegex(
            source,
            r"Unit->Stage == ELBOneFactoryVehicleStage::Pressing\s*"
            r"&& \(NextStage == ELBOneFactoryVehicleStage::PressPanelInspection",
        )

    def test_runtime_keeps_exact_v001_and_v002_topology_contracts(self) -> None:
        source = read("LBOneFactoryRuntimeCoordinator.cpp")
        for marker in (
            "ONEFACTORY_RUNTIME_ROUTE_V001",
            "OF_RUNTIME_TOPOLOGY_V001_%08X",
            "FrozenPersistedV001TopologyAlias",
            "OF_RUNTIME_TOPOLOGY_V001_C9F61F4B",
            "IsAllowedLegacyRoutedTopology",
            "NormalizeFrozenV001TopologyAliasForMutation",
            "ONEFACTORY_RUNTIME_ROUTE_V002",
            "OF_RUNTIME_TOPOLOGY_V002_%08X",
            "ACTIVE ROUTED OR MANUAL WIP MUST DRAIN BEFORE V002 ADMISSION",
            "CANNOT MIX ACTIVE V001 AND V002 ROUTE PROFILES",
            "ACTIVE V001 ROUTE WIP MUST DRAIN FIRST",
        ):
            self.assertIn(marker, source)
        self.assertRegex(
            source,
            r"PressStages\[Index\],\s*Index == PressPanelInspectionRouteIndex",
        )
        self.assertIn("Unit.RuntimeTopologyId != CurrentTopologyId", source)
        self.assertIn("ComputedLegacyTopologyId", source)
        self.assertIn("ComputedCurrentTopologyId", source)
        self.assertIn("Unit.RuntimeTopologyId == ComputedCurrentTopologyId", source)
        self.assertEqual(
            source.count('TEXT("OF_RUNTIME_TOPOLOGY_V001_C9F61F4B")'), 1,
            "the frozen hash must remain one input-only alias, not a generated id",
        )

    def test_existing_save_schema_remains_accepted_via_persisted_topology_id(self) -> None:
        save_header = read("LBOneFactorySaveGame.h")
        unit_header = read("LBOneFactoryProductionFlow.h")
        self.assertIn("static constexpr int32 CurrentSchemaVersion = 1;", save_header)
        self.assertRegex(
            unit_header,
            r"UPROPERTY\(EditAnywhere, BlueprintReadWrite, SaveGame\)\s*"
            r"FName RuntimeTopologyId = NAME_None;",
        )
        self.assertRegex(
            unit_header,
            r"UPROPERTY\(EditAnywhere, BlueprintReadWrite, SaveGame\)\s*"
            r"int32 RouteProfileVersion = 0;",
        )

    def test_unversioned_manual_wip_is_conservatively_fenced_and_drained(self) -> None:
        header = read("LBOneFactoryProductionFlow.h")
        flow = read("LBOneFactoryProductionFlow.cpp")
        runtime = read("LBOneFactoryRuntimeCoordinator.cpp")
        self.assertIn("LegacyRouteProfileV001 = 1", header)
        self.assertIn("PressInspectionRouteProfileV002 = 2", header)
        self.assertIn("ResolveRouteProfileVersion", flow)
        self.assertIn(
            "Unit.Stage == ELBOneFactoryVehicleStage::PressPanelInspection",
            flow,
        )
        self.assertIn(
            "ACTIVE V001 OR UNVERSIONED WIP MUST DRAIN",
            flow,
        )
        self.assertIn(
            "NextStage = ELBOneFactoryVehicleStage::PressedPanelStillage;",
            flow,
        )
        self.assertNotIn(
            "if (Unit.RuntimeStationCursor < 0 || IsTerminal(Unit)) continue;",
            runtime,
        )
        self.assertIn("ResolveRouteProfileVersion(Unit)", runtime)

    def test_manual_and_routed_active_wip_are_mutually_exclusive(self) -> None:
        header = read("LBOneFactoryProductionFlow.h")
        flow = read("LBOneFactoryProductionFlow.cpp")
        runtime = read("LBOneFactoryRuntimeCoordinator.cpp")
        tests = read("LBOneFactoryRuntimeCoordinatorTests.cpp")
        for marker in (
            "friend class ALBOneFactoryRuntimeCoordinator",
            "CreateRoutedVehicleOrder",
            "CreateVehicleOrderInternal",
        ):
            self.assertIn(marker, header)
        for marker in (
            "ONEFACTORY CANNOT MIX ACTIVE MANUAL AND ROUTED WIP",
            "ACTIVE MANUAL WIP MUST DRAIN",
            "ACTIVE ROUTED WIP MUST DRAIN",
        ):
            self.assertIn(marker, flow)
        for marker in (
            "HasActiveManualWIP",
            "ONEFACTORY RUNTIME CANNOT MIX ACTIVE MANUAL AND ROUTED WIP",
            "CreateRoutedVehicleOrder",
        ):
            self.assertIn(marker, runtime)
        for marker in (
            "ManualAndRoutedActiveWIPAreMutuallyExclusive",
            "direct manual admission is blocked by active routed V002 WIP",
            "same-profile active manual and routed WIP is rejected",
            "new routed admission is blocked by active manual V002 WIP",
            "failed mixed-mode restore preserves routed ledger",
        ):
            self.assertIn(marker, tests)

    def test_native_automation_covers_new_gate_and_v001_drain(self) -> None:
        tests = read("LBOneFactoryRuntimeCoordinatorTests.cpp")
        for marker in (
            "V001SaveDrainsBeforeV002PressInspectionAdmission",
            "An active V001 runtime save validates without schema rewrite",
            "New admissions cannot prolong an active V001 route",
            "Automatic dispatch treats the V001 drain as a soft hold",
            "The exact V001 unit drains and dispatches without genealogy loss",
            "Mixed terminal-V001/active-V002 history remains coherent",
            "UnversionedManualWIPDrainsAsV001BeforeV002Admission",
            "active cursor -1 legacy/manual save serializes",
            "downstream active V001 manual genealogy still fences admission",
            "ledger rejects simultaneous active manual V001 and V002 semantics",
            "SaveGameToMemory",
            "LoadGameFromMemory",
            "OF_RUNTIME_TOPOLOGY_V001_C9F61F4B",
            "OF_RUNTIME_TOPOLOGY_V001_E287C325",
            "an unknown V001-looking topology remains fail-closed",
            "first successful tick restamps only to the computed V001 companion",
            "terminal frozen V001 alias validates beside the current route",
            "V002 admission neither rewrites nor adopts the terminal V001 alias",
            "QualityHoldStages.Num(), 4",
            "VisitedStages.Num(), 19",
        ):
            self.assertIn(marker, tests)

    def test_append_only_stage_is_routed_to_existing_press_presentation(self) -> None:
        hud = read("LBOneFactoryProductionHUD.cpp")
        wip = read("LBOneFactoryWIPPresentationActor.cpp")
        self.assertRegex(
            hud,
            r"Stage == ELBOneFactoryVehicleStage::PressPanelInspection\)\s*"
            r"\{\s*return 1;",
        )
        self.assertIn(
            "case ELBOneFactoryVehicleStage::PressPanelInspection:", wip
        )

    def test_overhead_suppression_is_typed_cached_and_enable_aware(self) -> None:
        header = read("LBOneFactoryWIPPresentationActor.h")
        source = read("LBOneFactoryWIPPresentationActor.cpp")
        tests = read("LBOneFactoryWIPPresentationTests.cpp")
        self.assertIn(
            "TWeakObjectPtr<ALBPressShopOverheadPresentationActor>", header
        )
        self.assertIn(
            "TActorIterator<ALBPressShopOverheadPresentationActor>", source
        )
        self.assertNotIn("TActorIterator<AActor>", source)
        self.assertIn("Presentation->IsPresentationEnabled()", source)
        self.assertIn("OverheadPresentationRediscoverySeconds = 1.0", source)
        self.assertIn(
            "DisabledOverheadRestoresGenericPressWIP",
            tests,
        )

    def test_press_overhead_lifecycle_now_requires_and_releases_the_gate(self) -> None:
        lifecycle = read("LBPressShopOverheadLifecycleValidationTests.cpp")
        self.assertIn('#include "Engine/World.h"', lifecycle)
        self.assertIn(
            "Press panel inspection exposes a real quality-decision gate",
            lifecycle,
        )
        self.assertIn(
            "Completed Press inspection cycle holds for player evidence",
            lifecycle,
        )
        self.assertIn("OVERHEAD_PRESS_PANEL_INSPECTION_PASS", lifecycle)
        self.assertNotIn(
            "currently registers OF_PRESS_PANEL_INSPECTION_001 with bQualityGate=false",
            lifecycle,
        )
        self.assertIn("LIFECYCLE_VALIDATION_V002", lifecycle)
        self.assertIn("PressShopOverheadLifecycle_v002", lifecycle)
        self.assertIn("press_shop_overhead_lifecycle_receipt_v002.json", lifecycle)
        self.assertIn('TEXT("route_profile")', lifecycle)
        self.assertIn('TEXT("runtime_topology_id")', lifecycle)


if __name__ == "__main__":
    unittest.main()
