#if WITH_DEV_AUTOMATION_TESTS

#include "LBPaintShopExperimentalSaveGame.h"

#include "Kismet/GameplayStatics.h"
#include "Misc/AutomationTest.h"

#include <limits>

namespace LBPaintShopExperimentalSaveTestsPrivate
{
    FLBPaintShopExperimentalSaveState MakeValidState()
    {
        FLBPaintShopExperimentalSaveState Result;
        const TArray<FLBPaintShopCellDefinition> Definitions =
            FLBPaintShopDefinitionRegistry::GetCanonicalDefinitions();
        for (int32 Index = 0; Index < Definitions.Num(); ++Index)
        {
            FLBPaintShopPlacedCellSaveState Cell;
            Cell.CellId = FName(*FString::Printf(TEXT("PAINT_CELL_%02d"), Index + 1));
            Cell.DefinitionId = Definitions[Index].DefinitionId;
            Cell.WorldTransform = FTransform(FRotator::ZeroRotator,
                FVector(static_cast<float>(Index) * 2000.0f, 0.0f, 0.0f), FVector::OneVector);
            Cell.State = ELBPaintShopExperimentalCellState::Idle;
            Cell.bCommissioned = true;
            Result.Cells.Add(Cell);

            if (Index > 0)
            {
                FLBPaintShopConnectionSaveState Connection;
                Connection.ConnectionId = FName(*FString::Printf(TEXT("PAINT_CONNECTION_%02d"), Index));
                Connection.SourceCellId = Result.Cells[Index - 1].CellId;
                Connection.SourcePortId = LBPaintShopPortIds::CarrierOut;
                Connection.TargetCellId = Cell.CellId;
                Connection.TargetPortId = LBPaintShopPortIds::CarrierIn;
                Result.Connections.Add(Connection);
            }
        }

        FLBPaintShopWIPSaveState Unit;
        Unit.UnitId = TEXT("PAINT_WIP_001");
        Unit.MaterialId = LBPaintShopWIPIds::BIWComplete;
        Unit.CurrentCellId = Result.Cells[0].CellId;
        Unit.CarrierId = TEXT("PAINT_CARRIER_001");
        Unit.GenealogySequence = 1;
        Result.WIP.Add(Unit);
        Result.Cells[0].QueuedWIPIds.Add(Unit.UnitId);
        return Result;
    }

    FLBBodyInWhiteRecord MakeExactSourceBody(const int32 Serial)
    {
        FLBBodyInWhiteRecord Body;
        Body.BodyId = FName(*FString::Printf(TEXT("BIW-PAINT-TEST-%06d"), Serial));
        Body.VehicleModelId = ALBBodyWeldLineActor::GetVehicleModelId();
        Body.OrderId = FName(*FString::Printf(TEXT("ORDER-PAINT-TEST-%06d"), Serial));
        Body.BaseKitId = FName(*FString::Printf(TEXT("BASE-KIT-PAINT-TEST-%06d"), Serial));
        Body.ReservationId = FName(*FString::Printf(
            TEXT("WELD-RESERVATION-PAINT-TEST-%06d"), Serial));
        Body.WeldLineId = FName(*FString::Printf(TEXT("WELD-LINE-PAINT-TEST-%02d"), Serial));
        for (const FName PanelFamily : ALBBodyWeldLineActor::GetRequiredPanelFamilies())
        {
            FLBBodyWeldPanelLineage Panel;
            Panel.PanelId = FName(*FString::Printf(TEXT("PT1-PANEL-%s-%s-%06d"),
                *Body.VehicleModelId.ToString(), *PanelFamily.ToString(), Serial));
            Panel.PanelTypeId = PanelFamily;
            Panel.StillageId = FName(*FString::Printf(TEXT("STILLAGE-%s-%06d"),
                *PanelFamily.ToString(), Serial));
            Body.Panels.Add(Panel);
        }
        Body.QualityState = ELBBodyWeldQualityState::Good;
        Body.QualityEvidence.bRecipeComplete = true;
        Body.QualityEvidence.bFixtureProgramCorrect = true;
        Body.QualityEvidence.bSpotOperationsComplete = true;
        Body.QualityEvidence.bMIGOperationsComplete = true;
        Body.QualityEvidence.bRobotCalibrationInTolerance = true;
        Body.QualityEvidence.bServiceConditionAcceptable = true;
        Body.QualityEvidence.bSafetyInterlockClear = true;
        Body.CycleEvidence.ClosurePreparationSeconds = 5.0f;
        Body.CycleEvidence.FramingSeconds = 6.0f;
        Body.CycleEvidence.WeldingSeconds = 8.0f;
        Body.CycleEvidence.GeometryCheckSeconds = 3.0f;
        Body.CycleEvidence.CompletionSequence = Serial;
        Body.bEDAccepted = true;
        return Body;
    }

    FLBPaintShopExperimentalSaveState MakeExactLineageState(const int32 Serial = 1)
    {
        FLBPaintShopExperimentalSaveState Result = MakeValidState();
        Result.WIP[0].Version = 2;
        Result.WIP[0].SourceBodyInWhite = MakeExactSourceBody(Serial);
        Result.NextGenealogySequence = 2;
        return Result;
    }

    void PlaceOnlyWIPAtCell(FLBPaintShopExperimentalSaveState& State, const int32 CellIndex,
        const FName MaterialId)
    {
        for (FLBPaintShopPlacedCellSaveState& Cell : State.Cells)
        {
            Cell.QueuedWIPIds.Reset();
            Cell.ActiveWIPId = NAME_None;
        }
        State.WIP[0].MaterialId = MaterialId;
        State.WIP[0].CurrentCellId = State.Cells[CellIndex].CellId;
        State.Cells[CellIndex].QueuedWIPIds.Add(State.WIP[0].UnitId);
    }

    void AddDistinctSecondWIP(FLBPaintShopExperimentalSaveState& State)
    {
        FLBPaintShopWIPSaveState Unit = State.WIP[0];
        Unit.UnitId = TEXT("PAINT_WIP_002");
        Unit.CarrierId = TEXT("PAINT_CARRIER_002");
        Unit.GenealogySequence = 2;
        Unit.SourceBodyInWhite = MakeExactSourceBody(2);
        State.WIP.Add(Unit);
        State.NextGenealogySequence = FMath::Max(
            State.NextGenealogySequence, static_cast<int64>(3));
        const int32 CellIndex = State.Cells.IndexOfByPredicate([&Unit](
            const FLBPaintShopPlacedCellSaveState& Cell)
        {
            return Cell.CellId == Unit.CurrentCellId;
        });
        if (CellIndex != INDEX_NONE)
        {
            State.Cells[CellIndex].QueuedWIPIds.Add(Unit.UnitId);
        }
    }

    bool HasIdenticalLineage(const FLBBodyInWhiteRecord& A, const FLBBodyInWhiteRecord& B)
    {
        if (A.BodyId != B.BodyId || A.VehicleModelId != B.VehicleModelId
            || A.OrderId != B.OrderId || A.BaseKitId != B.BaseKitId
            || A.ReservationId != B.ReservationId || A.WeldLineId != B.WeldLineId
            || A.Panels.Num() != B.Panels.Num() || A.QualityState != B.QualityState
            || A.QualityEvidence.bRecipeComplete != B.QualityEvidence.bRecipeComplete
            || A.QualityEvidence.bFixtureProgramCorrect != B.QualityEvidence.bFixtureProgramCorrect
            || A.QualityEvidence.bSpotOperationsComplete != B.QualityEvidence.bSpotOperationsComplete
            || A.QualityEvidence.bMIGOperationsComplete != B.QualityEvidence.bMIGOperationsComplete
            || A.QualityEvidence.bRobotCalibrationInTolerance
                != B.QualityEvidence.bRobotCalibrationInTolerance
            || A.QualityEvidence.bServiceConditionAcceptable
                != B.QualityEvidence.bServiceConditionAcceptable
            || A.QualityEvidence.bSafetyInterlockClear
                != B.QualityEvidence.bSafetyInterlockClear
            || A.QualityEvidence.ReasonCodes != B.QualityEvidence.ReasonCodes
            || A.CycleEvidence.ClosurePreparationSeconds
                != B.CycleEvidence.ClosurePreparationSeconds
            || A.CycleEvidence.FramingSeconds != B.CycleEvidence.FramingSeconds
            || A.CycleEvidence.WeldingSeconds != B.CycleEvidence.WeldingSeconds
            || A.CycleEvidence.GeometryCheckSeconds != B.CycleEvidence.GeometryCheckSeconds
            || A.CycleEvidence.CompletionSequence != B.CycleEvidence.CompletionSequence
            || A.bEDAccepted != B.bEDAccepted)
        {
            return false;
        }
        for (int32 Index = 0; Index < A.Panels.Num(); ++Index)
        {
            if (A.Panels[Index].PanelId != B.Panels[Index].PanelId
                || A.Panels[Index].PanelTypeId != B.Panels[Index].PanelTypeId
                || A.Panels[Index].StillageId != B.Panels[Index].StillageId)
            {
                return false;
            }
        }
        return true;
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopExperimentalSaveIsolationTest,
    "LineBoss.PaintShop.Experimental.SaveGameV1Isolation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopExperimentalSaveIsolationTest::RunTest(const FString& Parameters)
{
    ULBPaintShopExperimentalSaveGame* Save = NewObject<ULBPaintShopExperimentalSaveGame>();
    TestNotNull(TEXT("Experimental Paint Shop save class can be created"), Save);
    if (!Save)
    {
        return false;
    }

    TestEqual(TEXT("Experimental Paint Shop save uses its dedicated v1 slot"),
        Save->GetSlotName(), FName(TEXT("LineBossPaintShopExperimental_v001")));
    TestEqual(TEXT("Experimental Paint Shop save remains schema v1"),
        Save->SaveSchemaVersion, ULBPaintShopExperimentalSaveGame::SchemaVersion);
    TestEqual(TEXT("Experimental Paint Shop save targets only the isolated prototype map"),
        Save->PrototypeMapId, FString(TEXT("LB_PaintShop_Prototype_v001")));

    Save->State = LBPaintShopExperimentalSaveTestsPrivate::MakeValidState();
    FString Reason;
    TestTrue(TEXT("A valid isolated Paint Shop state validates before load"),
        Save->ValidateForLoad(Reason));

    TArray<uint8> Bytes;
    TestTrue(TEXT("Experimental Paint Shop save serializes independently"),
        UGameplayStatics::SaveGameToMemory(Save, Bytes));
    ULBPaintShopExperimentalSaveGame* MemoryReload =
        Cast<ULBPaintShopExperimentalSaveGame>(UGameplayStatics::LoadGameFromMemory(Bytes));
    TestNotNull(TEXT("Experimental Paint Shop save reloads independently"), MemoryReload);
    if (MemoryReload)
    {
        TestTrue(TEXT("Reloaded isolated Paint Shop state validates"),
            MemoryReload->ValidateForLoad(Reason));
    }

    Save->SaveSchemaVersion = 2;
    TestFalse(TEXT("A different schema is rejected before any runtime restore"),
        Save->ValidateForLoad(Reason));
    TestTrue(TEXT("A rejected schema has a reason"), !Reason.IsEmpty());

    Save->SaveSchemaVersion = ULBPaintShopExperimentalSaveGame::SchemaVersion;
    Save->PrototypeMapId = TEXT("LB_A_Different_Prototype");
    TestFalse(TEXT("A different map target is rejected before any runtime restore"),
        Save->ValidateForLoad(Reason));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopExperimentalSaveTopologyAndWIPTest,
    "LineBoss.PaintShop.Experimental.SaveGameV1TopologyAndWIPInvariant",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopExperimentalSaveTopologyAndWIPTest::RunTest(const FString& Parameters)
{
    const FLBPaintShopExperimentalSaveState ValidState =
        LBPaintShopExperimentalSaveTestsPrivate::MakeValidState();
    FString Reason;
    TestTrue(TEXT("The six-cell carrier topology and unique WIP validate atomically"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(ValidState, Reason));

    FLBPaintShopExperimentalSaveState InvalidTopology = ValidState;
    InvalidTopology.Connections[0].TargetPortId = LBPaintShopPortIds::CarrierOut;
    TestFalse(TEXT("An output-to-output connection is rejected before restore"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(InvalidTopology, Reason));

    FLBPaintShopExperimentalSaveState SkippedStage = ValidState;
    SkippedStage.Connections[0].TargetCellId = SkippedStage.Cells[2].CellId;
    TestFalse(TEXT("A connection that skips the ordered Paint process is rejected"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(SkippedStage, Reason));

    FLBPaintShopExperimentalSaveState DuplicateWIP = ValidState;
    const FLBPaintShopWIPSaveState DuplicateWIPRecord = DuplicateWIP.WIP[0];
    DuplicateWIP.WIP.Add(DuplicateWIPRecord);
    TestFalse(TEXT("Duplicate WIP unit IDs are rejected"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(DuplicateWIP, Reason));

    FLBPaintShopExperimentalSaveState DoubleOwnedWIP = ValidState;
    DoubleOwnedWIP.Cells[1].QueuedWIPIds.Add(DoubleOwnedWIP.WIP[0].UnitId);
    TestFalse(TEXT("One WIP unit cannot be owned by two cells"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(DoubleOwnedWIP, Reason));

    FLBPaintShopExperimentalSaveState UnownedWIP = ValidState;
    UnownedWIP.Cells[0].QueuedWIPIds.Reset();
    TestFalse(TEXT("Every saved WIP unit must have one cell owner"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(UnownedWIP, Reason));

    FLBPaintShopExperimentalSaveState ImpossiblePause = ValidState;
    ImpossiblePause.Cells[0].bProcessPaused = true;
    TestFalse(TEXT("A paused flag without one active in-flight process is rejected"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(
            ImpossiblePause, Reason));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopExperimentalSaveV1LineageCompatibilityTest,
    "LineBoss.PaintShop.Experimental.SaveGameV1LineageCompatibilityAndFailClosed",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopExperimentalSaveV1LineageCompatibilityTest::RunTest(
    const FString& Parameters)
{
    FString Reason;
    const FLBPaintShopExperimentalSaveState ValidV1 =
        LBPaintShopExperimentalSaveTestsPrivate::MakeValidState();
    TestTrue(TEXT("An unchanged version-one WIP with completely default lineage remains valid"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(ValidV1, Reason));

    FLBPaintShopExperimentalSaveState NonDefaultV1 = ValidV1;
    NonDefaultV1.WIP[0].SourceBodyInWhite.BodyId = TEXT("BIW-MUST-NOT-LEAK-INTO-V1");
    TestFalse(TEXT("Version-one WIP fails closed when any Weld lineage field is populated"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(NonDefaultV1, Reason));

    FLBPaintShopExperimentalSaveState NestedNonDefaultV1 = ValidV1;
    NestedNonDefaultV1.WIP[0].SourceBodyInWhite.QualityEvidence.bRecipeComplete = true;
    TestFalse(TEXT("Version-one WIP rejects a partially populated nested lineage field"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(
            NestedNonDefaultV1, Reason));

    FLBPaintShopExperimentalSaveState DefaultV2 = ValidV1;
    DefaultV2.WIP[0].Version = 2;
    TestFalse(TEXT("Version-two WIP fails closed when exact acknowledged lineage is absent"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(DefaultV2, Reason));

    FLBPaintShopExperimentalSaveState UnsupportedWIPVersion = ValidV1;
    UnsupportedWIPVersion.WIP[0].Version = 3;
    TestFalse(TEXT("An unsupported WIP version is rejected without changing the top-level schema"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(
            UnsupportedWIPVersion, Reason));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopExperimentalSaveV2LineageRoundTripTest,
    "LineBoss.PaintShop.Experimental.SaveGameV2ExactLineageRoundTripAndMaterialProgression",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopExperimentalSaveV2LineageRoundTripTest::RunTest(const FString& Parameters)
{
    ULBPaintShopExperimentalSaveGame* Save = NewObject<ULBPaintShopExperimentalSaveGame>();
    TestNotNull(TEXT("Exact-lineage Paint Shop save can be created"), Save);
    if (!Save)
    {
        return false;
    }

    Save->State = LBPaintShopExperimentalSaveTestsPrivate::MakeExactLineageState();
    const FLBBodyInWhiteRecord ExpectedLineage = Save->State.WIP[0].SourceBodyInWhite;
    const FName MaterialIds[] = {
        LBPaintShopWIPIds::BIWComplete,
        LBPaintShopWIPIds::BIWEDCoated,
        LBPaintShopWIPIds::BIWCuredEDCoat
    };
    const int32 CellIndices[] = {0, 2, 5};
    FString Reason;
    for (int32 StageIndex = 0; StageIndex < UE_ARRAY_COUNT(MaterialIds); ++StageIndex)
    {
        LBPaintShopExperimentalSaveTestsPrivate::PlaceOnlyWIPAtCell(
            Save->State, CellIndices[StageIndex], MaterialIds[StageIndex]);
        TestTrue(*FString::Printf(TEXT("Material stage %d validates with exact lineage"),
            StageIndex), Save->ValidateForLoad(Reason));

        TArray<uint8> Bytes;
        TestTrue(*FString::Printf(TEXT("Material stage %d serializes"), StageIndex),
            UGameplayStatics::SaveGameToMemory(Save, Bytes));
        ULBPaintShopExperimentalSaveGame* Reloaded =
            Cast<ULBPaintShopExperimentalSaveGame>(UGameplayStatics::LoadGameFromMemory(Bytes));
        TestNotNull(*FString::Printf(TEXT("Material stage %d reloads"), StageIndex), Reloaded);
        if (!Reloaded)
        {
            return false;
        }
        TestTrue(*FString::Printf(TEXT("Material stage %d reload validates"), StageIndex),
            Reloaded->ValidateForLoad(Reason));
        TestEqual(*FString::Printf(TEXT("Material stage %d remains WIP version 2"), StageIndex),
            Reloaded->State.WIP[0].Version, 2);
        TestEqual(*FString::Printf(TEXT("Material stage %d preserves its semantic material"),
            StageIndex), Reloaded->State.WIP[0].MaterialId, MaterialIds[StageIndex]);
        TestTrue(*FString::Printf(TEXT("Material stage %d preserves every Weld lineage field"),
            StageIndex), LBPaintShopExperimentalSaveTestsPrivate::HasIdenticalLineage(
                Reloaded->State.WIP[0].SourceBodyInWhite, ExpectedLineage));
        Save = Reloaded;
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopExperimentalSaveV2LineageRejectionTest,
    "LineBoss.PaintShop.Experimental.SaveGameV2ExactLineageInvalidAndDuplicateRejection",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopExperimentalSaveV2LineageRejectionTest::RunTest(const FString& Parameters)
{
    const FLBPaintShopExperimentalSaveState Valid =
        LBPaintShopExperimentalSaveTestsPrivate::MakeExactLineageState();
    FString Reason;
    TestTrue(TEXT("A complete acknowledged Good Weld record validates as version-two WIP"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(Valid, Reason));

    FLBPaintShopExperimentalSaveState MissingIdentity = Valid;
    MissingIdentity.WIP[0].SourceBodyInWhite.ReservationId = NAME_None;
    TestFalse(TEXT("Version-two WIP rejects incomplete source identity"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(MissingIdentity, Reason));

    FLBPaintShopExperimentalSaveState Unacknowledged = Valid;
    Unacknowledged.WIP[0].SourceBodyInWhite.bEDAccepted = false;
    TestFalse(TEXT("Version-two WIP rejects a BIW not acknowledged at the Weld-to-ED boundary"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(Unacknowledged, Reason));

    FLBPaintShopExperimentalSaveState BadQuality = Valid;
    BadQuality.WIP[0].SourceBodyInWhite.QualityEvidence.bMIGOperationsComplete = false;
    TestFalse(TEXT("Good quality state cannot contradict incomplete deterministic evidence"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(BadQuality, Reason));

    FLBPaintShopExperimentalSaveState BadReasonCodes = Valid;
    BadReasonCodes.WIP[0].SourceBodyInWhite.QualityEvidence.ReasonCodes.Add(
        TEXT("MIG_OPERATIONS_INCOMPLETE"));
    TestFalse(TEXT("Good quality lineage cannot retain a failure reason code"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(BadReasonCodes, Reason));

    FLBPaintShopExperimentalSaveState BadCycle = Valid;
    BadCycle.WIP[0].SourceBodyInWhite.CycleEvidence.WeldingSeconds = -1.0f;
    TestFalse(TEXT("Negative deterministic cycle evidence is rejected"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(BadCycle, Reason));

    FLBPaintShopExperimentalSaveState NaNCycle = Valid;
    NaNCycle.WIP[0].SourceBodyInWhite.CycleEvidence.FramingSeconds =
        std::numeric_limits<float>::quiet_NaN();
    TestFalse(TEXT("Non-finite deterministic cycle evidence is rejected"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(NaNCycle, Reason));

    FLBPaintShopExperimentalSaveState MissingCompletion = Valid;
    MissingCompletion.WIP[0].SourceBodyInWhite.CycleEvidence.CompletionSequence = 0;
    TestFalse(TEXT("A non-positive Weld completion sequence is rejected"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(
            MissingCompletion, Reason));

    FLBPaintShopExperimentalSaveState FutureGenealogy = Valid;
    FutureGenealogy.WIP[0].GenealogySequence = FutureGenealogy.NextGenealogySequence;
    TestFalse(TEXT("Version-two WIP genealogy must precede the next sequence counter"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(
            FutureGenealogy, Reason));

    FLBPaintShopExperimentalSaveState BadPanelCatalog = Valid;
    BadPanelCatalog.WIP[0].SourceBodyInWhite.Panels[0].PanelTypeId = TEXT("UNKNOWN_PANEL");
    TestFalse(TEXT("Panel lineage outside the exact catalog and family set is rejected"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(BadPanelCatalog, Reason));

    FLBPaintShopExperimentalSaveState TwoBodies = Valid;
    LBPaintShopExperimentalSaveTestsPrivate::AddDistinctSecondWIP(TwoBodies);
    TestTrue(TEXT("Two completely distinct exact BIW lineages can coexist"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(TwoBodies, Reason));

    FLBPaintShopExperimentalSaveState SameSequenceDifferentLine = TwoBodies;
    SameSequenceDifferentLine.WIP[1].SourceBodyInWhite.CycleEvidence.CompletionSequence =
        SameSequenceDifferentLine.WIP[0].SourceBodyInWhite.CycleEvidence.CompletionSequence;
    TestTrue(TEXT("Completion sequence may repeat when the Weld line identity differs"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(
            SameSequenceDifferentLine, Reason));

    FLBPaintShopExperimentalSaveState SameLineDifferentSequence = TwoBodies;
    SameLineDifferentSequence.WIP[1].SourceBodyInWhite.WeldLineId =
        SameLineDifferentSequence.WIP[0].SourceBodyInWhite.WeldLineId;
    TestTrue(TEXT("Weld line identity may repeat when the completion sequence differs"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(
            SameLineDifferentSequence, Reason));

    FLBPaintShopExperimentalSaveState DuplicateBody = TwoBodies;
    DuplicateBody.WIP[1].SourceBodyInWhite.BodyId =
        DuplicateBody.WIP[0].SourceBodyInWhite.BodyId;
    TestFalse(TEXT("Source BodyId cannot be reused across Paint WIP"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(DuplicateBody, Reason));

    FLBPaintShopExperimentalSaveState DuplicateBaseKit = TwoBodies;
    DuplicateBaseKit.WIP[1].SourceBodyInWhite.BaseKitId =
        DuplicateBaseKit.WIP[0].SourceBodyInWhite.BaseKitId;
    TestFalse(TEXT("Source BaseKitId cannot be reused across Paint WIP"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(DuplicateBaseKit, Reason));

    FLBPaintShopExperimentalSaveState DuplicateReservation = TwoBodies;
    DuplicateReservation.WIP[1].SourceBodyInWhite.ReservationId =
        DuplicateReservation.WIP[0].SourceBodyInWhite.ReservationId;
    TestFalse(TEXT("Source ReservationId cannot be reused across Paint WIP"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(
            DuplicateReservation, Reason));

    FLBPaintShopExperimentalSaveState DuplicatePanel = TwoBodies;
    DuplicatePanel.WIP[1].SourceBodyInWhite.Panels[0] =
        DuplicatePanel.WIP[0].SourceBodyInWhite.Panels[0];
    TestFalse(TEXT("Source PanelId cannot be reused across Paint WIP"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(DuplicatePanel, Reason));

    FLBPaintShopExperimentalSaveState DuplicateWeldCompletion = TwoBodies;
    DuplicateWeldCompletion.WIP[1].SourceBodyInWhite.WeldLineId =
        DuplicateWeldCompletion.WIP[0].SourceBodyInWhite.WeldLineId;
    DuplicateWeldCompletion.WIP[1].SourceBodyInWhite.CycleEvidence.CompletionSequence =
        DuplicateWeldCompletion.WIP[0].SourceBodyInWhite.CycleEvidence.CompletionSequence;
    TestFalse(TEXT("The same WeldLineId and CompletionSequence pair cannot be reused"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(
            DuplicateWeldCompletion, Reason));
    return true;
}

#endif
