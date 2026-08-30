#if WITH_DEV_AUTOMATION_TESTS

#include "LBPaintShopBuildAuthority.h"

#include "Components/BoxComponent.h"
#include "Engine/World.h"
#include "LBPaintShopCellActor.h"
#include "Misc/AutomationTest.h"
#include "UObject/Class.h"

#include <limits>

namespace LBPaintShopBuildAuthorityTests
{
    template<typename StructType>
    bool StructEquals(const StructType& A, const StructType& B)
    {
        return StructType::StaticStruct()->CompareScriptStruct(&A, &B, 0);
    }

    bool WIPArraysEqual(const TArray<FLBPaintShopWIPSaveState>& A,
        const TArray<FLBPaintShopWIPSaveState>& B)
    {
        if (A.Num() != B.Num()) return false;
        for (int32 Index = 0; Index < A.Num(); ++Index)
        {
            if (!StructEquals(A[Index], B[Index])) return false;
        }
        return true;
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopApprovedEDCoatPlacementTest,
    "LineBoss.PaintShop.Experimental.BuildAuthority.ApprovedEDCoatPlacement",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopApprovedEDCoatPlacementTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBPaintShopApprovedEDCoatPlacementTest"));
    if (!TestNotNull(TEXT("Synthetic Paint Shop placement world exists"), World))
    {
        return false;
    }

    ALBPaintShopBuildAuthority* Authority = World->SpawnActor<ALBPaintShopBuildAuthority>();
    if (!TestNotNull(TEXT("Paint Shop build authority spawns"), Authority))
    {
        World->DestroyWorld(false);
        return false;
    }

    const FLBPaintShopApprovedEDCoatLayoutItem Approved =
        ALBPaintShopBuildAuthority::GetApprovedEDCoatDipLayout();
    TestEqual(TEXT("Approved layout owns one exact stable cell identity"), Approved.CellId,
        FName(TEXT("PAINT_EDCOAT_CELL_001")));
    TestEqual(TEXT("Approved layout accepts only the canonical ED-coat definition"),
        Approved.DefinitionId, LBPaintShopCellIds::EDCoatDipCell);
    TestTrue(TEXT("Approved layout remains centred on the floor-grid datum"),
        Approved.WorldTransform.Equals(FTransform::Identity, 0.001f));
    TestFalse(TEXT("Paint Shop build authority never ticks"),
        Authority->PrimaryActorTick.bCanEverTick);

    FString Reason;
    bool bValid = false;
    Authority->ValidateApprovedCellPlacementForValidation(Approved.DefinitionId,
        Approved.WorldTransform, bValid, Reason);
    TestTrue(TEXT("The one approved ED-coat placement validates"), bValid);
    TestTrue(TEXT("Approved placement has no rejection reason"), Reason.IsEmpty());
    TestFalse(TEXT("Placement preflight does not build a cell"),
        Authority->FindCell(Approved.CellId) != nullptr);

    TestFalse(TEXT("A different canonical Paint definition fails closed"),
        Authority->ValidateApprovedCellPlacement(LBPaintShopCellIds::PhosphateDipCell,
            Approved.WorldTransform, Reason));
    const FTransform OffGrid(FRotator::ZeroRotator, FVector(50.0f, 0.0f, 0.0f),
        FVector::OneVector);
    TestFalse(TEXT("An off-grid ED-coat placement fails closed"),
        Authority->ValidateApprovedCellPlacement(Approved.DefinitionId, OffGrid, Reason));
    const FTransform OutsideFootprint(FRotator::ZeroRotator,
        FVector(100.0f, 0.0f, 0.0f), FVector::OneVector);
    TestFalse(TEXT("An on-grid footprint outside the approved envelope fails closed"),
        Authority->ValidateApprovedCellPlacement(
            Approved.DefinitionId, OutsideFootprint, Reason));
    const FTransform Scaled(FRotator::ZeroRotator, FVector::ZeroVector,
        FVector(1.0f, 2.0f, 1.0f));
    TestFalse(TEXT("A scaled ED-coat placement fails closed"),
        Authority->ValidateApprovedCellPlacement(Approved.DefinitionId, Scaled, Reason));
    FTransform NonFinite = FTransform::Identity;
    NonFinite.SetLocation(FVector(std::numeric_limits<double>::quiet_NaN(), 0.0, 0.0));
    TestFalse(TEXT("A non-finite ED-coat placement fails closed"),
        Authority->ValidateApprovedCellPlacement(Approved.DefinitionId, NonFinite, Reason));

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopApprovedEDCoatBuildCaptureTest,
    "LineBoss.PaintShop.Experimental.BuildAuthority.BuildFindAndCapture",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopApprovedEDCoatBuildCaptureTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBPaintShopApprovedEDCoatBuildCaptureTest"));
    ALBPaintShopBuildAuthority* Authority = World
        ? World->SpawnActor<ALBPaintShopBuildAuthority>() : nullptr;
    if (!TestNotNull(TEXT("Build/capture authority exists"), Authority))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    FString Reason;
    TestTrue(TEXT("Authority builds the one approved empty ED-coat layout"),
        Authority->BuildApprovedEDCoatDipLayout(Reason));
    const FLBPaintShopApprovedEDCoatLayoutItem Approved =
        ALBPaintShopBuildAuthority::GetApprovedEDCoatDipLayout();
    ALBPaintShopCellActor* Cell = Authority->FindCell(Approved.CellId);
    TestNotNull(TEXT("Stable identity finds the built ED-coat cell"), Cell);
    TestTrue(TEXT("Built cell retains the canonical definition and transform"), Cell
        && Cell->GetDefinitionId() == LBPaintShopCellIds::EDCoatDipCell
        && Cell->GetActorTransform().Equals(Approved.WorldTransform, 0.001f));
    TestTrue(TEXT("Built gameplay footprint is the exact 1800 x 1000 x 853 cm contract"), Cell
        && Cell->GetFootprint()->GetUnscaledBoxExtent().Equals(
            FVector(900.0f, 500.0f, 426.5f), 0.01f));
    TestTrue(TEXT("Built protected envelope preserves the 1900 cm service width"), Cell
        && Cell->GetProtectedEnvelope()->GetUnscaledBoxExtent().Equals(
            FVector(950.0f, 650.0f, 475.0f), 0.01f));

    FLBPaintShopExperimentalSaveState Captured;
    TestTrue(TEXT("Built ED-coat topology captures"),
        Authority->CaptureTopologySaveState(Captured, Reason));
    TestEqual(TEXT("Topology capture contains exactly one cell"), Captured.Cells.Num(), 1);
    TestEqual(TEXT("Topology capture contains no generic connection graph"),
        Captured.Connections.Num(), 0);
    TestEqual(TEXT("Approved build synthesizes no WIP"), Captured.WIP.Num(), 0);
    TestTrue(TEXT("Initial topology cell is planned, empty and uncommissioned"),
        Captured.Cells.Num() == 1
        && Captured.Cells[0].State == ELBPaintShopExperimentalCellState::Planned
        && !Captured.Cells[0].bCommissioned
        && Captured.Cells[0].QueuedWIPIds.IsEmpty()
        && Captured.Cells[0].ActiveWIPId.IsNone()
        && FMath::IsNearlyZero(Captured.Cells[0].ProcessProgress01));
    TestTrue(TEXT("Captured topology remains structurally valid"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(Captured, Reason));

    TestFalse(TEXT("A second approved build fails closed"),
        Authority->BuildApprovedEDCoatDipLayout(Reason));
    TestTrue(TEXT("Rejected duplicate build preserves the original actor"),
        Authority->FindCell(Approved.CellId) == Cell);

    if (Cell)
    {
        Cell->SetActorTransform(FTransform(FVector(100.0f, 0.0f, 0.0f)), false,
            nullptr, ETeleportType::TeleportPhysics);
    }
    FLBPaintShopExperimentalSaveState RejectedCapture;
    RejectedCapture.Cells.AddDefaulted();
    TestFalse(TEXT("Capture fails closed after external actor movement"),
        Authority->CaptureTopologySaveState(RejectedCapture, Reason));
    TestTrue(TEXT("Failed capture clears its output instead of leaking stale topology"),
        RejectedCapture.Cells.IsEmpty() && RejectedCapture.WIP.IsEmpty());
    if (Cell)
    {
        Cell->SetActorTransform(Approved.WorldTransform, false, nullptr,
            ETeleportType::TeleportPhysics);
    }
    TestTrue(TEXT("Capture recovers after the exact actor transform is restored"),
        Authority->CaptureTopologySaveState(Captured, Reason));

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopTransactionalTopologyRestoreTest,
    "LineBoss.PaintShop.Experimental.BuildAuthority.TransactionalRestoreAndWIPIsolation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopTransactionalTopologyRestoreTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBPaintShopTransactionalTopologyRestoreTest"));
    ALBPaintShopBuildAuthority* Authority = World
        ? World->SpawnActor<ALBPaintShopBuildAuthority>() : nullptr;
    if (!Authority)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    FString Reason;
    TestTrue(TEXT("Transactional fixture builds its initial topology"),
        Authority->BuildApprovedEDCoatDipLayout(Reason));
    FLBPaintShopExperimentalSaveState Baseline;
    TestTrue(TEXT("Transactional fixture captures its baseline"),
        Authority->CaptureTopologySaveState(Baseline, Reason));
    if (Baseline.Cells.Num() != 1)
    {
        World->DestroyWorld(false);
        return false;
    }
    ALBPaintShopCellActor* OriginalCell = Authority->FindCell(Baseline.Cells[0].CellId);

    FLBPaintShopExperimentalSaveState WrongDefinition = Baseline;
    WrongDefinition.Cells[0].DefinitionId = LBPaintShopCellIds::PhosphateDipCell;
    TestFalse(TEXT("A different Paint cell type is rejected before commit"),
        Authority->RestoreTopologySaveState(WrongDefinition, Reason));
    TestTrue(TEXT("Definition rejection leaves the previous actor untouched"),
        OriginalCell && Authority->FindCell(Baseline.Cells[0].CellId) == OriginalCell);

    FLBPaintShopExperimentalSaveState MalformedPlacement = Baseline;
    MalformedPlacement.Cells[0].WorldTransform = FTransform(FVector(100.0f, 0.0f, 0.0f));
    TestFalse(TEXT("An on-grid but out-of-bay saved footprint is rejected"),
        Authority->RestoreTopologySaveState(MalformedPlacement, Reason));
    FLBPaintShopExperimentalSaveState AfterRejectedRestore;
    TestTrue(TEXT("Rejected placement leaves a capturable previous topology"),
        Authority->CaptureTopologySaveState(AfterRejectedRestore, Reason));
    TestTrue(TEXT("Rejected placement cannot partially mutate topology state"),
        LBPaintShopBuildAuthorityTests::StructEquals(AfterRejectedRestore, Baseline));

    FLBPaintShopExperimentalSaveState RuntimeState = Baseline;
    RuntimeState.Cells[0].State = ELBPaintShopExperimentalCellState::Processing;
    RuntimeState.Cells[0].bCommissioned = true;
    RuntimeState.Cells[0].ProcessProgress01 = 0.375f;
    RuntimeState.Cells[0].ActiveWIPId = TEXT("PAINT_WIP_ED_001");
    FLBPaintShopWIPSaveState& Unit = RuntimeState.WIP.AddDefaulted_GetRef();
    Unit.UnitId = RuntimeState.Cells[0].ActiveWIPId;
    Unit.MaterialId = LBPaintShopWIPIds::BIWComplete;
    Unit.CurrentCellId = RuntimeState.Cells[0].CellId;
    Unit.CarrierId = TEXT("PAINT_CARRIER_ED_001");
    Unit.GenealogySequence = 17;
    RuntimeState.NextWIPSerial = 18;
    RuntimeState.NextGenealogySequence = 18;
    TestTrue(TEXT("Complete runtime state with one exact WIP lineage validates"),
        ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(RuntimeState, Reason));
    const FLBPaintShopExperimentalSaveState ExactRuntimeBeforeStrip = RuntimeState;

    TestFalse(TEXT("Topology authority refuses to become the WIP or lineage owner"),
        Authority->RestoreTopologySaveState(RuntimeState, Reason));
    TestTrue(TEXT("WIP rejection is transactional"),
        OriginalCell && Authority->FindCell(Baseline.Cells[0].CellId) == OriginalCell);
    TestTrue(TEXT("Rejected runtime WIP remains byte-for-field exact"),
        LBPaintShopBuildAuthorityTests::WIPArraysEqual(
            RuntimeState.WIP, ExactRuntimeBeforeStrip.WIP));

    FLBPaintShopExperimentalSaveState TopologyOnly = RuntimeState;
    TopologyOnly.WIP.Reset();
    TopologyOnly.Cells[0].QueuedWIPIds.Reset();
    TopologyOnly.Cells[0].ActiveWIPId = NAME_None;
    TestTrue(TEXT("Stripping a copy cannot mutate the original WIP or lineage"),
        LBPaintShopBuildAuthorityTests::WIPArraysEqual(
            RuntimeState.WIP, ExactRuntimeBeforeStrip.WIP)
        && RuntimeState.NextWIPSerial == ExactRuntimeBeforeStrip.NextWIPSerial
        && RuntimeState.NextGenealogySequence ==
            ExactRuntimeBeforeStrip.NextGenealogySequence);
    TestTrue(TEXT("Topology-only copy preserves Processing state and exact progress"),
        TopologyOnly.Cells[0].State == ELBPaintShopExperimentalCellState::Processing
        && TopologyOnly.Cells[0].bCommissioned
        && FMath::IsNearlyEqual(TopologyOnly.Cells[0].ProcessProgress01, 0.375f));
    TestTrue(TEXT("Authority transactionally restores the stripped topology copy"),
        Authority->RestoreTopologySaveState(TopologyOnly, Reason));
    ALBPaintShopCellActor* RestoredCell = Authority->FindCell(TopologyOnly.Cells[0].CellId);
    TestTrue(TEXT("Successful restore atomically replaces the previous actor"),
        RestoredCell && RestoredCell != OriginalCell);

    FLBPaintShopExperimentalSaveState RoundTripTopology;
    TestTrue(TEXT("Restored topology captures"),
        Authority->CaptureTopologySaveState(RoundTripTopology, Reason));
    TestTrue(TEXT("Topology capture preserves every stripped record field and counter"),
        LBPaintShopBuildAuthorityTests::StructEquals(RoundTripTopology, TopologyOnly));
    TestTrue(TEXT("Original runtime state remains exact after topology restore"),
        LBPaintShopBuildAuthorityTests::StructEquals(
            RuntimeState, ExactRuntimeBeforeStrip));

    World->DestroyWorld(false);
    return true;
}

#endif
