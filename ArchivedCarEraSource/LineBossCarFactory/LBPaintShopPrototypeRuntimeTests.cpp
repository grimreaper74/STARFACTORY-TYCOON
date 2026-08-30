#if WITH_DEV_AUTOMATION_TESTS

#include "LBPaintShopPrototypeRuntime.h"

#include "LBBodyWeldLineActor.h"
#include "LBPaintShopBuildAuthority.h"
#include "LBPaintShopCellActor.h"

#include "Components/ActorComponent.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"

namespace LBPaintShopPrototypeRuntimeTestsPrivate
{
    const FName OrderId(TEXT("ORDER-PAINT-RUNTIME-001"));

    FLBBodyWeldStillageInventory MakeStillage(const FName Family, const int32 Serial,
        const int32 SerialOffset)
    {
        const int32 ExactSerial = Serial + SerialOffset;
        FLBBodyWeldStillageInventory Stillage;
        Stillage.StillageId = FName(*FString::Printf(TEXT("PAINT-TEST-STILLAGE-%s-%06d"),
            *Family.ToString(), ExactSerial));
        Stillage.OrderId = OrderId;
        Stillage.VehicleModelId = ALBBodyWeldLineActor::GetVehicleModelId();
        Stillage.PanelTypeId = Family;
        Stillage.DeliverySequence = ExactSerial;
        Stillage.CapacityPanels = 1;
        FLBBodyWeldPanelUnit& Panel = Stillage.PanelUnits.AddDefaulted_GetRef();
        Panel.PanelId = FName(*FString::Printf(TEXT("PTR-PANEL-%s-%s-%06d"),
            *Stillage.VehicleModelId.ToString(), *Family.ToString(), ExactSerial));
        Panel.OrderId = Stillage.OrderId;
        Panel.VehicleModelId = Stillage.VehicleModelId;
        Panel.PanelTypeId = Family;
        Panel.StillageId = Stillage.StillageId;
        return Stillage;
    }

    bool FeedRecipe(ALBBodyWeldLineActor* Line, const int32 SerialOffset)
    {
        if (!Line)
        {
            return false;
        }
        FString Reason;
        int32 Serial = 1;
        for (const FName Family : ALBBodyWeldLineActor::GetRequiredPanelFamilies())
        {
            if (!Line->ReceivePanelStillage(
                MakeStillage(Family, Serial++, SerialOffset), Reason))
            {
                return false;
            }
        }
        FLBBodyWeldBaseKitUnit BaseKit;
        BaseKit.KitId = FName(*FString::Printf(TEXT("PAINT-TEST-BASE-KIT-%06d"),
            SerialOffset + 1));
        BaseKit.OrderId = OrderId;
        BaseKit.DeliverySequence = SerialOffset + 1;
        return Line->ReceiveBaseKit(BaseKit, Reason);
    }

    ALBBodyWeldLineActor* MakeRestoredWeldOutput(UWorld* World, const int32 SerialOffset,
        FLBBodyInWhiteRecord& OutBody)
    {
        OutBody = FLBBodyInWhiteRecord();
        if (!World)
        {
            return nullptr;
        }
        ALBBodyWeldLineActor* Source = World->SpawnActor<ALBBodyWeldLineActor>();
        ALBBodyWeldLineActor* Restored = World->SpawnActor<ALBBodyWeldLineActor>();
        const FName LineId(*FString::Printf(TEXT("WL-PAINT-RUNTIME-%06d"),
            SerialOffset + 1));
        if (!Source || !Restored || !Source->Configure(LineId)
            || !Source->SetAssignedOrder(OrderId) || !FeedRecipe(Source, SerialOffset))
        {
            return nullptr;
        }
        Source->SetEDAvailable(true);
        Source->AdvanceSimulation(22.0f);
        if (!Source->GetOutputBody(OutBody))
        {
            return nullptr;
        }
        const FLBBodyWeldLineSaveState Saved = Source->CaptureSaveState();
        if (!ALBBodyWeldLineActor::IsSaveStateContractValid(Saved)
            || !Restored->RestoreSaveState(Saved))
        {
            return nullptr;
        }
        Source->Destroy();
        return Restored;
    }

    ALBPaintShopPrototypeRuntime* SpawnBoundRuntime(UWorld*& OutWorld,
        const TCHAR* WorldName, ALBPaintShopBuildAuthority*& OutAuthority)
    {
        OutAuthority = nullptr;
        OutWorld = UWorld::CreateWorld(EWorldType::Game, false, FName(WorldName));
        ALBPaintShopPrototypeRuntime* Runtime = OutWorld
            ? OutWorld->SpawnActor<ALBPaintShopPrototypeRuntime>() : nullptr;
        OutAuthority = OutWorld ? OutWorld->SpawnActor<ALBPaintShopBuildAuthority>() : nullptr;
        FString Reason;
        if (!Runtime || !OutAuthority
            || !Runtime->BindBuildAuthority(OutAuthority, Reason)
            || !Runtime->InitializePrototype(Reason))
        {
            return nullptr;
        }
        return Runtime;
    }

    bool HasIdenticalBody(const FLBBodyInWhiteRecord& A, const FLBBodyInWhiteRecord& B)
    {
        if (A.BodyId != B.BodyId || A.VehicleModelId != B.VehicleModelId
            || A.OrderId != B.OrderId || A.BaseKitId != B.BaseKitId
            || A.ReservationId != B.ReservationId || A.WeldLineId != B.WeldLineId
            || A.QualityState != B.QualityState || A.bEDAccepted != B.bEDAccepted
            || A.Panels.Num() != B.Panels.Num()
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
            || A.CycleEvidence.CompletionSequence != B.CycleEvidence.CompletionSequence)
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopPrototypeRuntimeInitializationTest,
    "LineBoss.PaintShop.Experimental.Runtime.BoundAuthorityInitializationAndStarvation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopPrototypeRuntimeInitializationTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LB_Paint_Runtime_Initialization"));
    ALBPaintShopPrototypeRuntime* Runtime = World
        ? World->SpawnActor<ALBPaintShopPrototypeRuntime>() : nullptr;
    ALBPaintShopBuildAuthority* Authority = World
        ? World->SpawnActor<ALBPaintShopBuildAuthority>() : nullptr;
    ALBPaintShopBuildAuthority* RebindAuthority = World
        ? World->SpawnActor<ALBPaintShopBuildAuthority>() : nullptr;
    TestNotNull(TEXT("Prototype runtime spawns as a non-visual process authority"), Runtime);
    TestNotNull(TEXT("Bootstrap-owned build authority is separate"), Authority);
    if (!World || !Runtime || !Authority || !RebindAuthority)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    TArray<UActorComponent*> RuntimeComponents;
    Runtime->GetComponents(RuntimeComponents);
    int32 PackagedRuntimeComponentCount = 0;
    for (const UActorComponent* Component : RuntimeComponents)
    {
        if (Component && !Component->IsEditorOnly())
        {
            ++PackagedRuntimeComponentCount;
        }
    }
    TestEqual(TEXT("Runtime creates no packaged child components"),
        PackagedRuntimeComponentCount, 0);
    TestTrue(TEXT("Actual play enables Tick on the same deterministic runtime step"),
        Runtime->PrimaryActorTick.bCanEverTick);
    FString Reason;
    TestFalse(TEXT("Initialization rejects a missing bound authority"),
        Runtime->InitializePrototype(Reason));
    TestFalse(TEXT("Null authority binding fails closed"),
        Runtime->BindBuildAuthority(nullptr, Reason));
    TestTrue(TEXT("The externally spawned authority binds exactly once"),
        Runtime->BindBuildAuthority(Authority, Reason));
    TestFalse(TEXT("A second authority cannot replace the bound authority"),
        Runtime->BindBuildAuthority(RebindAuthority, Reason));
    int32 AuthorityCountBeforeInitialize = 0;
    for (TActorIterator<ALBPaintShopBuildAuthority> It(World); It; ++It)
    {
        ++AuthorityCountBeforeInitialize;
    }
    TestTrue(TEXT("Bound authority builds the one approved ED-coat cell"),
        Runtime->InitializePrototype(Reason));
    int32 AuthorityCountAfterInitialize = 0;
    for (TActorIterator<ALBPaintShopBuildAuthority> It(World); It; ++It)
    {
        ++AuthorityCountAfterInitialize;
    }
    TestTrue(TEXT("Runtime retains the external authority without owning it"),
        Runtime->GetBuildAuthority() == Authority && Authority->GetOwner() != Runtime);
    TestEqual(TEXT("Initialization never spawns a duplicate build authority"),
        AuthorityCountAfterInitialize, AuthorityCountBeforeInitialize);
    TestTrue(TEXT("Initialized empty runtime reports deterministic starvation"),
        Runtime->IsInitialized() && Runtime->IsStarved()
        && Runtime->GetPhase() == ELBPaintShopPrototypePhase::Starved);
    TestTrue(TEXT("Approved ED-coat cell is configured through the authority"),
        Runtime->GetEDCoatCell() && Runtime->GetEDCoatCell()->IsConfigured()
        && Runtime->GetEDCoatCell()->GetDefinitionId() == LBPaintShopCellIds::EDCoatDipCell);

    FLBPaintShopExperimentalSaveState Saved;
    TestTrue(TEXT("Starved runtime captures one-cell topology with no invented WIP"),
        Runtime->CaptureSaveState(Saved, Reason) && Saved.Cells.Num() == 1
        && Saved.WIP.IsEmpty()
        && Saved.Cells[0].State == ELBPaintShopExperimentalCellState::Starved);
    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopPrototypeRuntimeAtomicHandoffTest,
    "LineBoss.PaintShop.Experimental.Runtime.AtomicWeldHandoffExactOnce",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopPrototypeRuntimeAtomicHandoffTest::RunTest(const FString& Parameters)
{
    UWorld* World = nullptr;
    ALBPaintShopBuildAuthority* Authority = nullptr;
    ALBPaintShopPrototypeRuntime* Runtime =
        LBPaintShopPrototypeRuntimeTestsPrivate::SpawnBoundRuntime(
            World, TEXT("LB_Paint_Runtime_Handoff"), Authority);
    FLBBodyInWhiteRecord WeldBody;
    ALBBodyWeldLineActor* Weld =
        LBPaintShopPrototypeRuntimeTestsPrivate::MakeRestoredWeldOutput(World, 0, WeldBody);
    TestNotNull(TEXT("Runtime and restored exact Weld output are available"), Runtime);
    TestNotNull(TEXT("A valid Weld save state reconstructs the handoff source"), Weld);
    if (!World || !Runtime || !Weld)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    FString Reason;
    FLBPaintShopExperimentalSaveState BeforeRejectedHandoff;
    TestTrue(TEXT("Empty Paint state captures before rejected handoffs"),
        Runtime->CaptureSaveState(BeforeRejectedHandoff, Reason));
    TestFalse(TEXT("Null Weld source cannot mutate Paint capacity or counters"),
        Runtime->AcceptAndAcknowledgeBodyInWhite(
            nullptr, WeldBody.BodyId, TEXT("CARRIER-ATOMIC-001"), Reason));
    TestFalse(TEXT("Wrong body ID cannot acknowledge the real Weld output"),
        Runtime->AcceptAndAcknowledgeBodyInWhite(
            Weld, TEXT("BIW-WRONG"), TEXT("CARRIER-ATOMIC-001"), Reason));
    FLBBodyInWhiteRecord StillAtWeld;
    FLBPaintShopExperimentalSaveState AfterRejectedHandoff;
    TestTrue(TEXT("Failed preflights leave exact Weld output and Paint capacity unchanged"),
        !Runtime->HasActiveWIP() && Weld->GetOutputBody(StillAtWeld)
        && StillAtWeld.BodyId == WeldBody.BodyId && !StillAtWeld.bEDAccepted
        && Runtime->CaptureSaveState(AfterRejectedHandoff, Reason)
        && AfterRejectedHandoff.NextWIPSerial == BeforeRejectedHandoff.NextWIPSerial
        && AfterRejectedHandoff.NextGenealogySequence
            == BeforeRejectedHandoff.NextGenealogySequence);

    TestTrue(TEXT("Valid handoff acknowledges Weld only after Paint save preflight"),
        Runtime->AcceptAndAcknowledgeBodyInWhite(
            Weld, WeldBody.BodyId, TEXT("CARRIER-ATOMIC-001"), Reason));
    FLBPaintShopWIPSaveState Active;
    FLBBodyInWhiteRecord ExpectedTransferredBody = WeldBody;
    ExpectedTransferredBody.bEDAccepted = true;
    TestTrue(TEXT("Paint commits the exact acknowledged record as version-two WIP"),
        Runtime->GetActiveWIP(Active) && Active.Version == 2
        && Active.MaterialId == LBPaintShopWIPIds::BIWComplete
        && Active.SourceBodyInWhite.bEDAccepted
        && LBPaintShopPrototypeRuntimeTestsPrivate::HasIdenticalBody(
            Active.SourceBodyInWhite, ExpectedTransferredBody));
    TestTrue(TEXT("Weld output is consumed exactly once and retained in completed history"),
        !Weld->GetOutputBody(StillAtWeld) && Weld->GetCompletedBodyCount() == 1);
    TestFalse(TEXT("A second acknowledgement cannot duplicate active Paint WIP"),
        Runtime->AcceptAndAcknowledgeBodyInWhite(
            Weld, WeldBody.BodyId, TEXT("CARRIER-ATOMIC-001"), Reason));

    Runtime->AdvanceSimulation(0.0f);
    TestTrue(TEXT("First process update makes the accepted carrier visible at load"),
        Runtime->GetEDCoatCell()->CapturePresentationState().bCarrierVisible);
    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopPrototypeRuntimeProcessTest,
    "LineBoss.PaintShop.Experimental.Runtime.PauseStagesBlockedOutputReleaseAndFault",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopPrototypeRuntimeProcessTest::RunTest(const FString& Parameters)
{
    UWorld* World = nullptr;
    ALBPaintShopBuildAuthority* Authority = nullptr;
    ALBPaintShopPrototypeRuntime* Runtime =
        LBPaintShopPrototypeRuntimeTestsPrivate::SpawnBoundRuntime(
            World, TEXT("LB_Paint_Runtime_Process"), Authority);
    FLBBodyInWhiteRecord WeldBody;
    ALBBodyWeldLineActor* Weld =
        LBPaintShopPrototypeRuntimeTestsPrivate::MakeRestoredWeldOutput(World, 100, WeldBody);
    FString Reason;
    if (!World || !Runtime || !Weld
        || !Runtime->AcceptAndAcknowledgeBodyInWhite(
            Weld, WeldBody.BodyId, TEXT("CARRIER-PROCESS-001"), Reason))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    Runtime->AdvanceSimulation(0.5f);
    TestTrue(TEXT("Load stage advances deterministically"),
        Runtime->GetPhase() == ELBPaintShopPrototypePhase::Loading
        && FMath::IsNearlyEqual(Runtime->GetCycleProgress01(), 0.05f));
    Runtime->SetPaused(true);
    const float PausedCycle = Runtime->GetCycleProgress01();
    const float PausedPhase = Runtime->GetPhaseProgress01();
    FLBPaintShopWIPSaveState PausedWIPBefore;
    TestTrue(TEXT("Paused runtime retains an exact active WIP snapshot"),
        Runtime->GetActiveWIP(PausedWIPBefore));
    Runtime->AdvanceSimulation(100.0f);
    FLBPaintShopWIPSaveState PausedWIPAfter;
    TestTrue(TEXT("Paused process has no cycle, phase, or material drift"),
        Runtime->IsPaused()
        && FMath::IsNearlyEqual(Runtime->GetCycleProgress01(), PausedCycle)
        && FMath::IsNearlyEqual(Runtime->GetPhaseProgress01(), PausedPhase)
        && Runtime->GetActiveWIP(PausedWIPAfter)
        && PausedWIPAfter.UnitId == PausedWIPBefore.UnitId
        && PausedWIPAfter.MaterialId == PausedWIPBefore.MaterialId
        && LBPaintShopPrototypeRuntimeTestsPrivate::HasIdenticalBody(
            PausedWIPAfter.SourceBodyInWhite, PausedWIPBefore.SourceBodyInWhite));
    FLBPaintShopExperimentalSaveState PausedSave;
    TestTrue(TEXT("Paused process captures its exact operator hold in isolated state"),
        Runtime->CaptureSaveState(PausedSave, Reason)
        && PausedSave.Cells.Num() == 1 && PausedSave.Cells[0].bProcessPaused
        && PausedSave.Cells[0].State == ELBPaintShopExperimentalCellState::Processing);
    Runtime->SetPaused(false);

    Runtime->AdvanceSimulation(0.5f);
    TestEqual(TEXT("Load transitions to descend"), Runtime->GetPhase(),
        ELBPaintShopPrototypePhase::Descending);
    Runtime->AdvanceSimulation(2.0f);
    TestEqual(TEXT("Descend transitions to immerse"), Runtime->GetPhase(),
        ELBPaintShopPrototypePhase::Immersing);
    Runtime->AdvanceSimulation(3.0f);
    TestEqual(TEXT("Immerse transitions to rise"), Runtime->GetPhase(),
        ELBPaintShopPrototypePhase::Rising);
    Runtime->AdvanceSimulation(2.0f);
    TestEqual(TEXT("Rise transitions to drain"), Runtime->GetPhase(),
        ELBPaintShopPrototypePhase::Draining);
    FLBPaintShopWIPSaveState Active;
    TestTrue(TEXT("Material remains BIW_COMPLETE until the whole dip cycle completes"),
        Runtime->GetActiveWIP(Active)
        && Active.MaterialId == LBPaintShopWIPIds::BIWComplete);

    Runtime->SetOutputBlocked(true);
    Runtime->AdvanceSimulation(2.0f);
    TestTrue(TEXT("Drain completion creates retained BIW_ED_COATED output"),
        Runtime->GetPhase() == ELBPaintShopPrototypePhase::OutputReady
        && Runtime->GetActiveWIP(Active)
        && Active.MaterialId == LBPaintShopWIPIds::BIWEDCoated
        && FMath::IsNearlyEqual(Runtime->GetCycleProgress01(), 1.0f));
    FLBPaintShopWIPSaveState Released;
    TestFalse(TEXT("Blocked output cannot release and never deletes coated WIP"),
        Runtime->ReleaseOutput(Released, Reason));
    TestTrue(TEXT("Blocked output remains owned and captures an explicit blocked cell"),
        Runtime->HasActiveWIP());
    FLBPaintShopExperimentalSaveState BlockedSave;
    TestTrue(TEXT("Blocked retention is represented without a new save schema"),
        Runtime->CaptureSaveState(BlockedSave, Reason)
        && BlockedSave.Cells[0].State == ELBPaintShopExperimentalCellState::Blocked
        && BlockedSave.Cells[0].bOutputBlocked);

    Runtime->SetOutputBlocked(false);
    TestTrue(TEXT("Unblocked output releases exact coated WIP and returns to starvation"),
        Runtime->ReleaseOutput(Released, Reason)
        && Released.MaterialId == LBPaintShopWIPIds::BIWEDCoated
        && Released.SourceBodyInWhite.bEDAccepted
        && !Runtime->HasActiveWIP() && Runtime->IsStarved()
        && !Runtime->GetEDCoatCell()->CapturePresentationState().bCarrierVisible);

    FLBBodyInWhiteRecord FaultBody;
    ALBBodyWeldLineActor* FaultWeld =
        LBPaintShopPrototypeRuntimeTestsPrivate::MakeRestoredWeldOutput(
            World, 200, FaultBody);
    TestTrue(TEXT("Runtime can accept the next distinct body after release"),
        FaultWeld && Runtime->AcceptAndAcknowledgeBodyInWhite(
            FaultWeld, FaultBody.BodyId, TEXT("CARRIER-PROCESS-002"), Reason));
    Runtime->AdvanceSimulation(-1.0f);
    TestTrue(TEXT("Invalid process input faults closed while retaining exact WIP"),
        Runtime->IsProcessFaulted() && Runtime->HasActiveWIP()
        && Runtime->GetPhase() == ELBPaintShopPrototypePhase::Faulted
        && Runtime->GetEDCoatCell()->CapturePresentationState().bFaulted);
    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopPrototypeRuntimeSaveRestoreTest,
    "LineBoss.PaintShop.Experimental.Runtime.SaveRestoreExactLineageAndNoDuplicate",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopPrototypeRuntimeSaveRestoreTest::RunTest(const FString& Parameters)
{
    UWorld* SourceWorld = nullptr;
    ALBPaintShopBuildAuthority* SourceAuthority = nullptr;
    ALBPaintShopPrototypeRuntime* SourceRuntime =
        LBPaintShopPrototypeRuntimeTestsPrivate::SpawnBoundRuntime(
            SourceWorld, TEXT("LB_Paint_Runtime_Save_Source"), SourceAuthority);
    FLBBodyInWhiteRecord WeldBody;
    ALBBodyWeldLineActor* Weld =
        LBPaintShopPrototypeRuntimeTestsPrivate::MakeRestoredWeldOutput(
            SourceWorld, 300, WeldBody);
    FString Reason;
    if (!SourceWorld || !SourceRuntime || !Weld
        || !SourceRuntime->AcceptAndAcknowledgeBodyInWhite(
            Weld, WeldBody.BodyId, TEXT("CARRIER-SAVE-001"), Reason))
    {
        if (SourceWorld) SourceWorld->DestroyWorld(false);
        return false;
    }
    SourceRuntime->AdvanceSimulation(4.0f);
    FLBPaintShopExperimentalSaveState Saved;
    TestTrue(TEXT("Mid-immerse runtime captures exact topology, WIP, lineage, and counters"),
        SourceRuntime->CaptureSaveState(Saved, Reason)
        && Saved.WIP.Num() == 1 && Saved.WIP[0].Version == 2
        && Saved.WIP[0].SourceBodyInWhite.bEDAccepted);

    UWorld* TargetWorld = nullptr;
    ALBPaintShopBuildAuthority* TargetAuthority = nullptr;
    ALBPaintShopPrototypeRuntime* TargetRuntime =
        LBPaintShopPrototypeRuntimeTestsPrivate::SpawnBoundRuntime(
            TargetWorld, TEXT("LB_Paint_Runtime_Save_Target"), TargetAuthority);
    if (!TargetWorld || !TargetRuntime)
    {
        SourceWorld->DestroyWorld(false);
        if (TargetWorld) TargetWorld->DestroyWorld(false);
        return false;
    }
    TestTrue(TEXT("Fresh runtime restores stripped topology then exact runtime ownership"),
        TargetRuntime->RestoreSaveState(Saved, Reason));
    FLBPaintShopWIPSaveState RestoredWIP;
    TestTrue(TEXT("Restore reconstructs immerse phase and presentation from saved progress"),
        TargetRuntime && TargetRuntime->GetActiveWIP(RestoredWIP)
        && TargetRuntime->GetPhase() == ELBPaintShopPrototypePhase::Immersing
        && FMath::IsNearlyEqual(TargetRuntime->GetCycleProgress01(), 0.4f)
        && FMath::IsNearlyEqual(
            TargetRuntime->GetEDCoatCell()->CapturePresentationState().CycleProgress01, 0.4f));
    TestTrue(TEXT("Every exact Weld lineage field survives Paint save and restore"),
        LBPaintShopPrototypeRuntimeTestsPrivate::HasIdenticalBody(
            RestoredWIP.SourceBodyInWhite, Saved.WIP[0].SourceBodyInWhite));

    FLBBodyInWhiteRecord CapacityBody;
    ALBBodyWeldLineActor* CapacityWeld =
        LBPaintShopPrototypeRuntimeTestsPrivate::MakeRestoredWeldOutput(
            TargetWorld, 400, CapacityBody);
    TestNotNull(TEXT("Second exact Weld output exists for capacity preflight"), CapacityWeld);
    if (!CapacityWeld)
    {
        SourceWorld->DestroyWorld(false);
        TargetWorld->DestroyWorld(false);
        return false;
    }
    TestFalse(TEXT("Restored max-one WIP rejects another source before acknowledging it"),
        TargetRuntime->AcceptAndAcknowledgeBodyInWhite(
            CapacityWeld, CapacityBody.BodyId, TEXT("CARRIER-SAVE-002"), Reason));
    FLBBodyInWhiteRecord CapacityStillAtWeld;
    TestTrue(TEXT("Capacity rejection leaves the second Weld body untouched"),
        CapacityWeld->GetOutputBody(CapacityStillAtWeld)
        && CapacityStillAtWeld.BodyId == CapacityBody.BodyId
        && !CapacityStillAtWeld.bEDAccepted);

    FLBPaintShopExperimentalSaveState Duplicate = Saved;
    const FLBPaintShopWIPSaveState DuplicateWIP = Duplicate.WIP[0];
    Duplicate.WIP.Add(DuplicateWIP);
    TestFalse(TEXT("Restore rejects duplicate exact WIP before mutating live runtime"),
        TargetRuntime->RestoreSaveState(Duplicate, Reason));
    FLBPaintShopExperimentalSaveState AfterRejectedRestore;
    TestTrue(TEXT("Rejected duplicate restore preserves prior exact WIP and progress"),
        TargetRuntime->CaptureSaveState(AfterRejectedRestore, Reason)
        && AfterRejectedRestore.WIP.Num() == 1
        && FMath::IsNearlyEqual(AfterRejectedRestore.Cells[0].ProcessProgress01, 0.4f)
        && LBPaintShopPrototypeRuntimeTestsPrivate::HasIdenticalBody(
            AfterRejectedRestore.WIP[0].SourceBodyInWhite,
            Saved.WIP[0].SourceBodyInWhite));

    SourceWorld->DestroyWorld(false);
    TargetWorld->DestroyWorld(false);
    return true;
}

#endif
