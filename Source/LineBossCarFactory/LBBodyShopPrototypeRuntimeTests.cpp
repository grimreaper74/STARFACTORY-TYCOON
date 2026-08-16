#if WITH_DEV_AUTOMATION_TESTS

#include "LBBodyShopPrototypeRuntime.h"

#include "LBBodyShopBuildAuthority.h"
#include "LBBodyShopCellActor.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"

namespace LBBodyShopPrototypeRuntimeTestsPrivate
{
    FLBBodyShopExperimentalSaveState MakeValidCompletedPilotSave()
    {
        FLBBodyShopExperimentalSaveState State;
        State.Version = 1;
        State.NextCellSerial = 7;
        State.NextConnectionSerial = 6;
        State.NextWIPSerial = 2;
        State.NextGenealogySequence = 2;

        const TArray<FLBBodyShopApprovedLayoutItem> Layout =
            ALBBodyShopBuildAuthority::GetApprovedUnderbodySliceLayout();
        for (int32 Index = 0; Index < Layout.Num(); ++Index)
        {
            FLBBodyShopPlacedCellSaveState& Cell = State.Cells.AddDefaulted_GetRef();
            Cell.CellId = FName(*FString::Printf(TEXT("BODYSHOP-CELL-%03d"), Index + 1));
            Cell.DefinitionId = Layout[Index].DefinitionId;
            Cell.WorldTransform = Layout[Index].WorldTransform;
            Cell.State = ELBBodyShopCellState::Idle;
            Cell.bCommissioned = true;
        }

        for (const FLBBodyShopPilotRobotBinding& Binding :
            ALBBodyShopPrototypeRuntime::GetRequiredPilotRobotBindings())
        {
            FLBBodyShopPlacedCellSaveState* Cell = State.Cells.FindByPredicate(
                [&Binding](const FLBBodyShopPlacedCellSaveState& Candidate)
                {
                    return Candidate.DefinitionId == Binding.CellDefinitionId;
                });
            if (!Cell) continue;
            FLBBodyShopRobotAssignment& Assignment = Cell->RobotAssignments.AddDefaulted_GetRef();
            Assignment.SlotId = Binding.SlotId;
            Assignment.Role = Binding.Role;
            Assignment.Tool = Binding.Tool;
            Assignment.bEnabled = true;
            Assignment.Condition01 = 1.0f;
        }

        const auto AddConnection = [&State](const int32 SourceIndex, const FName SourcePort,
            const int32 TargetIndex, const FName TargetPort, const int32 Serial)
        {
            FLBBodyShopConnectionSaveState& Connection = State.Connections.AddDefaulted_GetRef();
            Connection.ConnectionId = FName(*FString::Printf(TEXT("BODYSHOP-CONNECTION-%03d"), Serial));
            Connection.SourceCellId = State.Cells[SourceIndex].CellId;
            Connection.SourcePortId = SourcePort;
            Connection.TargetCellId = State.Cells[TargetIndex].CellId;
            Connection.TargetPortId = TargetPort;
        };
        AddConnection(0, LBBodyShopPrototypeIds::StillageOut, 1,
            LBBodyShopPrototypeIds::StillageIn, 1);
        AddConnection(1, LBBodyShopPrototypeIds::PanelOut, 2,
            LBBodyShopPrototypeIds::PanelIn, 2);
        AddConnection(2, LBBodyShopPrototypeIds::SkidOut, 3,
            LBBodyShopPrototypeIds::SkidIn, 3);
        AddConnection(3, LBBodyShopPrototypeIds::SkidOut, 4,
            LBBodyShopPrototypeIds::BodyIn, 4);
        AddConnection(4, LBBodyShopPrototypeIds::BodyOut, 5,
            LBBodyShopPrototypeIds::BodyIn, 5);

        FLBBodyShopWIPSaveState& Unit = State.WIP.AddDefaulted_GetRef();
        Unit.UnitId = TEXT("BODYSHOP-WIP-001");
        Unit.MaterialId = LBBodyShopMaterialIds::Underbody;
        Unit.CurrentCellId = State.Cells[5].CellId;
        Unit.SourceStillageId = TEXT("BODYSHOP-PILOT-STILLAGE-001");
        Unit.SkidId = TEXT("BODYSHOP-PILOT-SKID-001");
        Unit.GenealogySequence = 1;
        Unit.Quality = ELBBodyShopQualityResult::Pass;
        State.Cells[5].QueuedWIPIds.Add(Unit.UnitId);
        return State;
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopPilotRobotBindingContractTest,
    "LineBoss.BodyShop.Experimental.Runtime.PilotRobotBindingContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopPilotRobotBindingContractTest::RunTest(const FString& Parameters)
{
    const TArray<FLBBodyShopPilotRobotBinding> Bindings =
        ALBBodyShopPrototypeRuntime::GetRequiredPilotRobotBindings();
    TestEqual(TEXT("The approved vertical slice has exactly three authored robots"), Bindings.Num(), 3);
    TestEqual(TEXT("The first robot is the panel handling fixture assignment"),
        Bindings[0].CellDefinitionId, LBBodyShopPrototypeIds::PanelPresentation);
    TestEqual(TEXT("The handling robot uses the exact eight-cup EOAT"),
        Bindings[0].Tool, ELBBodyShopToolType::VacuumEightCup);
    TestEqual(TEXT("The second robot is the left spot-weld robot"), Bindings[1].SlotId,
        FName(TEXT("ROBOT_WELD_LEFT")));
    TestEqual(TEXT("The third robot is the right spot-weld robot"), Bindings[2].SlotId,
        FName(TEXT("ROBOT_WELD_RIGHT")));
    TestEqual(TEXT("Both fixture weld robots use C-guns"), Bindings[2].Tool,
        ELBBodyShopToolType::SpotCGun);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopPilotStageContractTest,
    "LineBoss.BodyShop.Experimental.Runtime.DeterministicStageContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopPilotStageContractTest::RunTest(const FString& Parameters)
{
    TestEqual(TEXT("Full stillage begins at the hand-off stage"),
        ALBBodyShopPrototypeRuntime::GetStageForWIPLocation(
            LBBodyShopPrototypeIds::FullStillageDock, ELBBodyShopQualityResult::Pending,
            ELBBodyShopCellState::Running), ELBBodyShopRuntimeStage::TransferringStillage);
    TestEqual(TEXT("Panel presentation maps to the eight-cup process stage"),
        ALBBodyShopPrototypeRuntime::GetStageForWIPLocation(
            LBBodyShopPrototypeIds::PanelPresentation, ELBBodyShopQualityResult::Pending,
            ELBBodyShopCellState::Running), ELBBodyShopRuntimeStage::PresentingPanel);
    TestEqual(TEXT("Underbody fixture maps to bounded welding poses"),
        ALBBodyShopPrototypeRuntime::GetStageForWIPLocation(
            LBBodyShopPrototypeIds::UnderbodyFixture, ELBBodyShopQualityResult::Pending,
            ELBBodyShopCellState::Running), ELBBodyShopRuntimeStage::WeldingUnderbody);
    TestEqual(TEXT("A blocked vision pass exposes output blockage"),
        ALBBodyShopPrototypeRuntime::GetStageForWIPLocation(
            LBBodyShopPrototypeIds::BasicVisionGate, ELBBodyShopQualityResult::Pass,
            ELBBodyShopCellState::Blocked), ELBBodyShopRuntimeStage::OutputBlocked);
    TestEqual(TEXT("A failed vision inspection remains in the isolated quality hold"),
        ALBBodyShopPrototypeRuntime::GetStageForWIPLocation(
            LBBodyShopPrototypeIds::BasicVisionGate, ELBBodyShopQualityResult::Fail,
            ELBBodyShopCellState::Faulted), ELBBodyShopRuntimeStage::QualityHold);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopPilotWIPMotionSamplingTest,
    "LineBoss.BodyShop.Experimental.Runtime.DeterministicContinuousWIPMotion",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopPilotWIPMotionSamplingTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    const FTransform Dock(FVector(0.0f, 0.0f, 0.0f));
    const FTransform Panel(FVector(1000.0f, 0.0f, 0.0f));
    const FTransform Fixture(FVector(2000.0f, 0.0f, 0.0f));
    const FTransform Conveyor(FVector(3000.0f, 0.0f, 0.0f));
    const FTransform Vision(FVector(4000.0f, 0.0f, 0.0f));
    const FTransform Output(FVector(5000.0f, 0.0f, 0.0f));
    const auto Sample = [&](const ELBBodyShopRuntimeStage Stage, const float Progress01)
    {
        return ALBBodyShopPrototypeRuntime::SampleWIPPresentation(Stage, Progress01,
            Dock, Panel, Fixture, Conveyor, Vision, Output);
    };
    const auto IsAt = [](const FTransform& Transform, const FVector& Expected)
    {
        return Transform.GetLocation().Equals(Expected, 0.01f);
    };

    const FLBBodyShopWIPPresentationSample TransferStart = Sample(
        ELBBodyShopRuntimeStage::TransferringStillage, 0.0f);
    const FLBBodyShopWIPPresentationSample TransferMid = Sample(
        ELBBodyShopRuntimeStage::TransferringStillage, 0.5f);
    const FLBBodyShopWIPPresentationSample TransferEnd = Sample(
        ELBBodyShopRuntimeStage::TransferringStillage, 1.0f);
    TestEqual(TEXT("Stillage transfer owns one stillage presentation"), TransferMid.Kind,
        ELBBodyShopWIPPresentationKind::Stillage);
    TestTrue(TEXT("Stillage transfer begins at the dock"),
        IsAt(TransferStart.WorldTransform, FVector::ZeroVector));
    TestTrue(TEXT("Stillage transfer advances continuously between authored anchors"),
        TransferMid.WorldTransform.GetLocation().X > TransferStart.WorldTransform.GetLocation().X
        && TransferMid.WorldTransform.GetLocation().X < TransferEnd.WorldTransform.GetLocation().X);
    TestTrue(TEXT("Stillage transfer ends at the destacking-side anchor"),
        IsAt(TransferEnd.WorldTransform, FVector(810.0f, 110.0f, 0.0f)));
    const FTransform AuthoredDock(FRotator(0.0f, 90.0f, 0.0f),
        FVector(123.0f, 456.0f, 0.0f));
    const FLBBodyShopWIPPresentationSample FloorPivotStart =
        ALBBodyShopPrototypeRuntime::SampleWIPPresentation(
            ELBBodyShopRuntimeStage::TransferringStillage, 0.0f,
            AuthoredDock, Panel, Fixture, Conveyor, Vision, Output);
    TestTrue(TEXT("Native full-stillage start preserves the authored XY and floor Z=0 datum"),
        FloorPivotStart.WorldTransform.GetLocation().Equals(
            AuthoredDock.GetLocation(), 0.01f));
    TestTrue(TEXT("Native full-stillage start preserves the authored dock yaw"),
        FloorPivotStart.WorldTransform.GetRotation().Equals(
            AuthoredDock.GetRotation(), 0.0001f));

    const FLBBodyShopWIPPresentationSample PanelStart = Sample(
        ELBBodyShopRuntimeStage::PresentingPanel, 0.0f);
    const FLBBodyShopWIPPresentationSample PanelMid = Sample(
        ELBBodyShopRuntimeStage::PresentingPanel, 0.5f);
    const FLBBodyShopWIPPresentationSample PanelEnd = Sample(
        ELBBodyShopRuntimeStage::PresentingPanel, 1.0f);
    TestEqual(TEXT("Presentation stage owns a single loose panel"), PanelMid.Kind,
        ELBBodyShopWIPPresentationKind::Panel);
    TestTrue(TEXT("Loose panel begins above the arrived stillage"),
        IsAt(PanelStart.WorldTransform, FVector(810.0f, 110.0f, 54.0f)));
    TestTrue(TEXT("Loose panel follows a visible deterministic transfer arc"),
        PanelMid.WorldTransform.GetLocation().Z > PanelStart.WorldTransform.GetLocation().Z);
    TestTrue(TEXT("Loose panel lands on the raised skid assembly without an endpoint jump"),
        IsAt(PanelEnd.WorldTransform, FVector(2000.0f, 0.0f, 89.0f)));

    const FLBBodyShopWIPPresentationSample Welding = Sample(
        ELBBodyShopRuntimeStage::WeldingUnderbody, 0.5f);
    TestEqual(TEXT("Welding owns the one skid-underbody assembly"), Welding.Kind,
        ELBBodyShopWIPPresentationKind::SkidUnderbody);
    TestTrue(TEXT("Welding holds the skid on the fixture's authored 35 cm conveyor datum"),
        IsAt(Welding.WorldTransform, FVector(2000.0f, 0.0f, 35.0f)));

    const FLBBodyShopWIPPresentationSample ConveyorStart = Sample(
        ELBBodyShopRuntimeStage::ConveyingSkid, 0.0f);
    const FLBBodyShopWIPPresentationSample ConveyorMid = Sample(
        ELBBodyShopRuntimeStage::ConveyingSkid, 0.5f);
    const FLBBodyShopWIPPresentationSample ConveyorEnd = Sample(
        ELBBodyShopRuntimeStage::ConveyingSkid, 1.0f);
    TestEqual(TEXT("Conveyor stage owns one skid-underbody assembly"), ConveyorMid.Kind,
        ELBBodyShopWIPPresentationKind::SkidUnderbody);
    TestTrue(TEXT("Skid starts at the fixture's authored 35 cm conveyor datum"),
        IsAt(ConveyorStart.WorldTransform, Fixture.GetLocation() + FVector(0.0f, 0.0f, 35.0f)));
    TestTrue(TEXT("Skid crosses the straight conveyor at its 35 cm datum"),
        IsAt(ConveyorMid.WorldTransform, Conveyor.GetLocation() + FVector(0.0f, 0.0f, 35.0f)));
    TestTrue(TEXT("Skid reaches the vision gate at its 35 cm datum"),
        IsAt(ConveyorEnd.WorldTransform, Vision.GetLocation() + FVector(0.0f, 0.0f, 35.0f)));

    const FLBBodyShopWIPPresentationSample Repeated = Sample(
        ELBBodyShopRuntimeStage::ConveyingSkid, 0.5f);
    TestTrue(TEXT("The same stage sample is bit-stable for save/reload reconstruction"),
        Repeated.WorldTransform.Equals(ConveyorMid.WorldTransform, 0.0f));
    TestEqual(TEXT("A non-flow stage exposes no WIP visual"),
        Sample(ELBBodyShopRuntimeStage::Ready, 0.7f).Kind,
        ELBBodyShopWIPPresentationKind::None);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopPilotSaveReloadContractTest,
    "LineBoss.BodyShop.Experimental.Runtime.SaveReloadNoDuplicateWIPContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopPilotSaveReloadContractTest::RunTest(const FString& Parameters)
{
    FLBBodyShopExperimentalSaveState State =
        LBBodyShopPrototypeRuntimeTestsPrivate::MakeValidCompletedPilotSave();
    FString Reason;
    TestTrue(TEXT("A completed pilot unit has a valid isolated v1 reload state"),
        ALBBodyShopPrototypeRuntime::ValidateRuntimeSaveState(State, Reason));

    FLBBodyShopWIPSaveState Duplicate = State.WIP[0];
    State.WIP.Add(Duplicate);
    Reason.Reset();
    TestFalse(TEXT("A reload cannot introduce duplicate pilot WIP"),
        ALBBodyShopPrototypeRuntime::ValidateRuntimeSaveState(State, Reason));
    TestTrue(TEXT("Duplicate WIP rejection supplies a diagnostic"), !Reason.IsEmpty());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopFixtureWIPPresentationOwnershipTest,
    "LineBoss.BodyShop.Experimental.Runtime.FixtureWIPPresentationOwnership",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopFixtureWIPPresentationOwnershipTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        FName(TEXT("LBBodyShopFixtureWIPPresentationOwnershipTest")));
    if (!TestNotNull(TEXT("Synthetic Body Shop runtime world exists"), World))
        return false;

    ALBBodyShopBuildAuthority* Authority = World->SpawnActor<ALBBodyShopBuildAuthority>();
    ALBBodyShopPrototypeRuntime* Runtime = World->SpawnActor<ALBBodyShopPrototypeRuntime>();
    TestNotNull(TEXT("Isolated Body Shop build authority spawns"), Authority);
    TestNotNull(TEXT("Body Shop prototype runtime spawns"), Runtime);

    if (Authority && Runtime)
    {
        TestEqual(TEXT("An unseeded runtime has no visible WIP presentation"),
            Runtime->GetVisibleRuntimeWIPPresentationCount(), 0);
        FString Reason;
        TestTrue(TEXT("Prototype runtime binds to its isolated build authority"),
            Runtime->BindBuildAuthority(Authority, Reason));

        FLBBodyShopExperimentalSaveState StillageState =
            LBBodyShopPrototypeRuntimeTestsPrivate::MakeValidCompletedPilotSave();
        FLBBodyShopWIPSaveState& StillageUnit = StillageState.WIP[0];
        StillageState.Cells[5].QueuedWIPIds.Reset();
        StillageUnit.MaterialId = LBBodyShopMaterialIds::PressedPanelStillage;
        StillageUnit.SkidId = NAME_None;
        StillageUnit.CurrentCellId = StillageState.Cells[0].CellId;
        StillageUnit.Quality = ELBBodyShopQualityResult::Pending;
        StillageState.Cells[0].State = ELBBodyShopCellState::Running;
        StillageState.Cells[0].ProcessProgress01 = 0.25f;
        StillageState.Cells[0].ActiveWIPId = StillageUnit.UnitId;
        Reason.Reset();
        TestTrue(TEXT("Stillage-stage pilot WIP restores through the experimental save path"),
            Runtime->RestoreExperimentalSaveState(StillageState, Reason));
        TestEqual(TEXT("The restored stillage hand-off has one logical runtime stillage"),
            Runtime->GetCurrentWIPPresentationKind(), ELBBodyShopWIPPresentationKind::Stillage);
        TestEqual(TEXT("The restored stillage hand-off has one visible runtime WIP presentation"),
            Runtime->GetVisibleRuntimeWIPPresentationCount(), 1);
        TestEqual(TEXT("Runtime stillage uses the exact native v002 full-stillage mesh"),
            Runtime->GetPilotStillagePresentationMeshPath(), FString(TEXT(
                "/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_PanelStillage_Full_v002.SM_LB_BodyShopSupport_PanelStillage_Full_v002")));
        TestFalse(TEXT("Active runtime stillage no longer binds the legacy v001 namespace"),
            Runtime->GetPilotStillagePresentationMeshPath().Contains(
                TEXT("PanelStillageRuntime_v001")));

        FLBBodyShopExperimentalSaveState PanelState =
            LBBodyShopPrototypeRuntimeTestsPrivate::MakeValidCompletedPilotSave();
        FLBBodyShopWIPSaveState& PanelUnit = PanelState.WIP[0];
        PanelState.Cells[5].QueuedWIPIds.Reset();
        PanelUnit.MaterialId = LBBodyShopMaterialIds::PressedPanelStillage;
        PanelUnit.SkidId = NAME_None;
        PanelUnit.CurrentCellId = PanelState.Cells[1].CellId;
        PanelUnit.Quality = ELBBodyShopQualityResult::Pending;
        PanelState.Cells[1].State = ELBBodyShopCellState::Running;
        PanelState.Cells[1].ProcessProgress01 = 0.5f;
        PanelState.Cells[1].ActiveWIPId = PanelUnit.UnitId;
        Reason.Reset();
        TestTrue(TEXT("Panel-stage pilot WIP restores through the experimental save path"),
            Runtime->RestoreExperimentalSaveState(PanelState, Reason));
        TestTrue(TEXT("All three required runtime WIP meshes resolve before presentation"),
            Runtime->HasValidWIPPresentationArt());
        TestEqual(TEXT("The restored unit resumes at deterministic panel presentation"),
            Runtime->GetRuntimeStage(), ELBBodyShopRuntimeStage::PresentingPanel);
        TestEqual(TEXT("The restored panel stage exposes one logical loose-panel WIP"),
            Runtime->GetCurrentWIPPresentationKind(), ELBBodyShopWIPPresentationKind::Panel);
        TestEqual(TEXT("The restored panel stage has one visible runtime WIP presentation"),
            Runtime->GetVisibleRuntimeWIPPresentationCount(), 1);
        TestTrue(TEXT("Saved process progress reconstructs the same motion sample"),
            FMath::IsNearlyEqual(Runtime->GetCurrentWIPPresentationProgress01(), 0.5f));

        FLBBodyShopExperimentalSaveState State =
            LBBodyShopPrototypeRuntimeTestsPrivate::MakeValidCompletedPilotSave();
        FLBBodyShopWIPSaveState& Unit = State.WIP[0];
        State.Cells[5].QueuedWIPIds.Reset();
        Unit.CurrentCellId = State.Cells[2].CellId;
        Unit.Quality = ELBBodyShopQualityResult::Pending;
        State.Cells[2].State = ELBBodyShopCellState::Running;
        State.Cells[2].ProcessProgress01 = 0.5f;
        State.Cells[2].ActiveWIPId = Unit.UnitId;

        Reason.Reset();
        TestTrue(TEXT("Fixture-stage pilot WIP restores through the experimental save path"),
            Runtime->RestoreExperimentalSaveState(State, Reason));
        TestEqual(TEXT("The restored unit resumes at the welding fixture stage"),
            Runtime->GetRuntimeStage(), ELBBodyShopRuntimeStage::WeldingUnderbody);
        TestTrue(TEXT("An active welding-stage restore resumes simulation"),
            Runtime->IsSimulationRunning());
        TestEqual(TEXT("An active welding-stage restore resumes all three articulations"),
            Runtime->GetRunningRobotArticulationCount(), 3);
        Reason.Reset();
        TestTrue(TEXT("Validation can pause the active welding stage"),
            Runtime->SetSimulationRunning(false, Reason));
        TestFalse(TEXT("Runtime simulation reports the deterministic pause"),
            Runtime->IsSimulationRunning());
        TestEqual(TEXT("Runtime pause freezes every spawned robot articulation"),
            Runtime->GetRunningRobotArticulationCount(), 0);
        Reason.Reset();
        TestTrue(TEXT("Validation can resume the paused welding stage"),
            Runtime->SetSimulationRunning(true, Reason));
        TestEqual(TEXT("Runtime resume restarts every spawned robot articulation"),
            Runtime->GetRunningRobotArticulationCount(), 3);
        Reason.Reset();
        TestTrue(TEXT("The fixture visual can be held again for deterministic evidence"),
            Runtime->SetSimulationRunning(false, Reason));
        TestEqual(TEXT("The held evidence frame has zero running articulations"),
            Runtime->GetRunningRobotArticulationCount(), 0);
        TestEqual(TEXT("The restored fixture stage contains exactly one runtime WIP unit"),
            Runtime->GetActivePilotWIPCount(), 1);
        TestEqual(TEXT("The runtime renders exactly one skid-and-underbody WIP assembly"),
            Runtime->GetVisibleRuntimeWIPPresentationCount(), 1);
        TestEqual(TEXT("The fixture-stage visual is the one logical skid-underbody assembly"),
            Runtime->GetCurrentWIPPresentationKind(),
            ELBBodyShopWIPPresentationKind::SkidUnderbody);
        TestFalse(TEXT("The AInfo-derived runtime owner is explicitly unhidden for game rendering"),
            Runtime->IsHidden());
        TestEqual(TEXT("The visible carrier uses the exact approved skid mesh"),
            Runtime->GetPilotSkidPresentationMeshPath(), FString(
                TEXT("/Game/LineBoss/Candidates/Vehicles/Cairnwell2040/BIWBaseKitRuntime_v001/Carrier/SM_LB_C2040_BIWBaseSkid_v001.SM_LB_C2040_BIWBaseSkid_v001")));
        TestEqual(TEXT("The visible workpiece uses the exact approved underbody mesh"),
            Runtime->GetPilotUnderbodyPresentationMeshPath(), FString(
                TEXT("/Game/LineBoss/Candidates/Vehicles/Cairnwell2040/BIWBaseKitRuntime_v001/Workpiece/SM_LB_C2040_BIWBaseKit_Underbody_v001.SM_LB_C2040_BIWBaseKit_Underbody_v001")));
        TestTrue(TEXT("The skid component and its owner are visible and unhidden"),
            Runtime->IsPilotSkidPresentationVisibleAndUnhidden());
        TestTrue(TEXT("The underbody component and its owner are visible and unhidden"),
            Runtime->IsPilotUnderbodyPresentationVisibleAndUnhidden());

        ALBBodyShopCellActor* Fixture = Authority->FindCell(State.Cells[2].CellId);
        if (TestNotNull(TEXT("The restored underbody fixture exists"), Fixture))
        {
            TestEqual(TEXT("The restored WIP remains at the underbody fixture"),
                Fixture->GetDefinitionId(), LBBodyShopPrototypeIds::UnderbodyFixture);
            TestFalse(TEXT("The fixture contributes no second static skid or underbody"),
                Fixture->HasStaticCarrierOrWorkpiecePresentation());
            const FVector FixtureOrigin = Fixture->GetActorLocation();
            const FVector FixtureHalf = Fixture->GetDefinition().FootprintCm * 0.5f;
            const FVector SkidMin = Runtime->GetPilotSkidPresentationWorldBoundsMin();
            const FVector SkidMax = Runtime->GetPilotSkidPresentationWorldBoundsMax();
            const FVector UnderbodyMin = Runtime->GetPilotUnderbodyPresentationWorldBoundsMin();
            const FVector UnderbodyMax = Runtime->GetPilotUnderbodyPresentationWorldBoundsMax();
            TestTrue(TEXT("The skid's render bounds clear the 31 cm powered-roller surface"),
                SkidMin.Z > FixtureOrigin.Z + 31.0f);
            TestTrue(TEXT("The underbody is visibly stacked above the carrier"),
                UnderbodyMin.Z > SkidMin.Z);
            TestTrue(TEXT("The skid render bounds remain inside the fixture footprint"),
                SkidMin.X >= FixtureOrigin.X - FixtureHalf.X
                && SkidMax.X <= FixtureOrigin.X + FixtureHalf.X
                && SkidMin.Y >= FixtureOrigin.Y - FixtureHalf.Y
                && SkidMax.Y <= FixtureOrigin.Y + FixtureHalf.Y
                && SkidMax.Z <= FixtureOrigin.Z + Fixture->GetDefinition().FootprintCm.Z);
            TestTrue(TEXT("The underbody render bounds remain inside the fixture footprint"),
                UnderbodyMin.X >= FixtureOrigin.X - FixtureHalf.X
                && UnderbodyMax.X <= FixtureOrigin.X + FixtureHalf.X
                && UnderbodyMin.Y >= FixtureOrigin.Y - FixtureHalf.Y
                && UnderbodyMax.Y <= FixtureOrigin.Y + FixtureHalf.Y
                && UnderbodyMax.Z <= FixtureOrigin.Z + Fixture->GetDefinition().FootprintCm.Z);
            TestTrue(TEXT("The runtime's weld-fixture alignment evidence gate passes"),
                Runtime->IsSkidUnderbodyPresentationAlignedInWeldFixture());
        }
        TestFalse(TEXT("The skid render-evidence seam fails closed on an invalid tolerance"),
            Runtime->WasPilotSkidPresentationRecentlyRendered(-1.0f));
        TestFalse(TEXT("The underbody render-evidence seam fails closed on an invalid tolerance"),
            Runtime->WasPilotUnderbodyPresentationRecentlyRendered(-1.0f));
        TestFalse(TEXT("The combined render-evidence seam fails closed on an invalid tolerance"),
            Runtime->WasSkidUnderbodyPresentationRecentlyRendered(-1.0f));

        FLBBodyShopExperimentalSaveState CompletedState =
            LBBodyShopPrototypeRuntimeTestsPrivate::MakeValidCompletedPilotSave();
        Reason.Reset();
        TestTrue(TEXT("A completed pilot unit restores before player release"),
            Runtime->RestoreExperimentalSaveState(CompletedState, Reason));
        TestFalse(TEXT("A completed restore stops simulation automatically"),
            Runtime->IsSimulationRunning());
        TestEqual(TEXT("A completed restore cannot leave stale robot articulation running"),
            Runtime->GetRunningRobotArticulationCount(), 0);
        Reason.Reset();
        TestFalse(TEXT("A held completed unit cannot resume a non-runnable process"),
            Runtime->SetSimulationRunning(true, Reason));
        TestEqual(TEXT("Rejected resume leaves all robot articulations paused"),
            Runtime->GetRunningRobotArticulationCount(), 0);
        Reason.Reset();
        TestTrue(TEXT("The player-facing release clears a completed pilot unit"),
            Runtime->ReleaseHeldPilotUnit(Reason));
        TestEqual(TEXT("Player release leaves no logical or visible WIP behind"),
            Runtime->GetActivePilotWIPCount() + Runtime->GetVisibleRuntimeWIPPresentationCount(), 0);
        TestEqual(TEXT("Player release returns the commissioned slice to ready"),
            Runtime->GetRuntimeStage(), ELBBodyShopRuntimeStage::Ready);
        TestEqual(TEXT("Player release keeps every ready-state articulation paused"),
            Runtime->GetRunningRobotArticulationCount(), 0);
        Reason.Reset();
        TestTrue(TEXT("A new pilot cycle explicitly resumes simulation"),
            Runtime->StartPilotCycle(Reason));
        TestTrue(TEXT("A new pilot cycle reports running"), Runtime->IsSimulationRunning());
        TestEqual(TEXT("A new pilot cycle restarts all three robot articulations"),
            Runtime->GetRunningRobotArticulationCount(), 3);
        Reason.Reset();
        TestTrue(TEXT("The restarted pilot cycle remains cleanly pausable"),
            Runtime->SetSimulationRunning(false, Reason));
        TestEqual(TEXT("Restarted-cycle pause leaves no stale articulation"),
            Runtime->GetRunningRobotArticulationCount(), 0);
    }

    World->DestroyWorld(false);
    return true;
}

#endif
