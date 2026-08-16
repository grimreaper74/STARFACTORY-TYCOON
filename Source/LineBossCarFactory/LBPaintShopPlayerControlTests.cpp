#if WITH_DEV_AUTOMATION_TESTS

#include "LBPaintShopPrototypeGameMode.h"

#include "Components/ActorComponent.h"
#include "Components/Button.h"
#include "Components/PrimitiveComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "LBBodyWeldLineActor.h"
#include "LBPaintShopExperimentalSaveGame.h"
#include "LBPaintShopManagementPawn.h"
#include "LBPaintShopPrototypeHUD.h"
#include "LBPaintShopPrototypeRootWidget.h"
#include "LBPaintShopPrototypeRuntime.h"
#include "LBPaintShopPrototypeWorldBootstrap.h"
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

namespace LBPaintShopPlayerControlTestsPrivate
{
    bool HasIdenticalPanels(const TArray<FLBBodyWeldPanelLineage>& A,
        const TArray<FLBBodyWeldPanelLineage>& B)
    {
        if (A.Num() != B.Num()) return false;
        for (int32 Index = 0; Index < A.Num(); ++Index)
        {
            if (A[Index].PanelId != B[Index].PanelId
                || A[Index].PanelTypeId != B[Index].PanelTypeId
                || A[Index].StillageId != B[Index].StillageId)
            {
                return false;
            }
        }
        return true;
    }

    bool HasIdenticalBody(const FLBBodyInWhiteRecord& A,
        const FLBBodyInWhiteRecord& B)
    {
        const FLBBodyWeldQualityEvidence& AQ = A.QualityEvidence;
        const FLBBodyWeldQualityEvidence& BQ = B.QualityEvidence;
        const FLBBodyWeldCycleEvidence& AC = A.CycleEvidence;
        const FLBBodyWeldCycleEvidence& BC = B.CycleEvidence;
        return A.BodyId == B.BodyId && A.VehicleModelId == B.VehicleModelId
            && A.OrderId == B.OrderId && A.BaseKitId == B.BaseKitId
            && A.ReservationId == B.ReservationId && A.WeldLineId == B.WeldLineId
            && A.QualityState == B.QualityState && A.bEDAccepted == B.bEDAccepted
            && HasIdenticalPanels(A.Panels, B.Panels)
            && AQ.bRecipeComplete == BQ.bRecipeComplete
            && AQ.bFixtureProgramCorrect == BQ.bFixtureProgramCorrect
            && AQ.bSpotOperationsComplete == BQ.bSpotOperationsComplete
            && AQ.bMIGOperationsComplete == BQ.bMIGOperationsComplete
            && AQ.bRobotCalibrationInTolerance == BQ.bRobotCalibrationInTolerance
            && AQ.bServiceConditionAcceptable == BQ.bServiceConditionAcceptable
            && AQ.bSafetyInterlockClear == BQ.bSafetyInterlockClear
            && AQ.ReasonCodes == BQ.ReasonCodes
            && AC.ClosurePreparationSeconds == BC.ClosurePreparationSeconds
            && AC.FramingSeconds == BC.FramingSeconds
            && AC.WeldingSeconds == BC.WeldingSeconds
            && AC.GeometryCheckSeconds == BC.GeometryCheckSeconds
            && AC.CompletionSequence == BC.CompletionSequence;
    }

    bool HasIdenticalState(const FLBPaintShopExperimentalSaveState& A,
        const FLBPaintShopExperimentalSaveState& B)
    {
        if (A.Version != B.Version || A.NextCellSerial != B.NextCellSerial
            || A.NextConnectionSerial != B.NextConnectionSerial
            || A.NextWIPSerial != B.NextWIPSerial
            || A.NextGenealogySequence != B.NextGenealogySequence
            || A.Cells.Num() != B.Cells.Num()
            || A.Connections.Num() != B.Connections.Num()
            || A.WIP.Num() != B.WIP.Num())
        {
            return false;
        }
        for (int32 Index = 0; Index < A.Cells.Num(); ++Index)
        {
            const FLBPaintShopPlacedCellSaveState& AC = A.Cells[Index];
            const FLBPaintShopPlacedCellSaveState& BC = B.Cells[Index];
            if (AC.Version != BC.Version || AC.CellId != BC.CellId
                || AC.DefinitionId != BC.DefinitionId
                || !AC.WorldTransform.Equals(BC.WorldTransform, KINDA_SMALL_NUMBER)
                || AC.State != BC.State || AC.bCommissioned != BC.bCommissioned
                || AC.QueuedWIPIds != BC.QueuedWIPIds
                || AC.ActiveWIPId != BC.ActiveWIPId
                || AC.ProcessProgress01 != BC.ProcessProgress01
                || AC.bProcessPaused != BC.bProcessPaused
                || AC.bOutputBlocked != BC.bOutputBlocked)
            {
                return false;
            }
        }
        for (int32 Index = 0; Index < A.Connections.Num(); ++Index)
        {
            const FLBPaintShopConnectionSaveState& AC = A.Connections[Index];
            const FLBPaintShopConnectionSaveState& BC = B.Connections[Index];
            if (AC.Version != BC.Version || AC.ConnectionId != BC.ConnectionId
                || AC.SourceCellId != BC.SourceCellId
                || AC.SourcePortId != BC.SourcePortId
                || AC.TargetCellId != BC.TargetCellId
                || AC.TargetPortId != BC.TargetPortId)
            {
                return false;
            }
        }
        for (int32 Index = 0; Index < A.WIP.Num(); ++Index)
        {
            const FLBPaintShopWIPSaveState& AW = A.WIP[Index];
            const FLBPaintShopWIPSaveState& BW = B.WIP[Index];
            if (AW.Version != BW.Version || AW.UnitId != BW.UnitId
                || AW.MaterialId != BW.MaterialId
                || AW.CurrentCellId != BW.CurrentCellId
                || AW.CarrierId != BW.CarrierId
                || AW.GenealogySequence != BW.GenealogySequence
                || !HasIdenticalBody(AW.SourceBodyInWhite, BW.SourceBodyInWhite))
            {
                return false;
            }
        }
        return true;
    }

    int32 CountLiveWeldSources(UWorld* World)
    {
        int32 Count = 0;
        if (!World) return Count;
        for (TActorIterator<ALBBodyWeldLineActor> It(World); It; ++It)
        {
            if (IsValid(*It) && !It->IsActorBeingDestroyed()) ++Count;
        }
        return Count;
    }

    bool IsCompletelyIsolatedSource(ALBBodyWeldLineActor* Source)
    {
        if (!IsValid(Source) || Source->IsActorBeingDestroyed()
            || !Source->IsHidden() || Source->GetActorEnableCollision()
            || Source->IsActorTickEnabled())
        {
            return false;
        }
        TArray<UActorComponent*> Components;
        Source->GetComponents(Components);
        for (UActorComponent* Component : Components)
        {
            if (!IsValid(Component) || Component->IsComponentTickEnabled()) return false;
            if (const UPrimitiveComponent* Primitive = Cast<UPrimitiveComponent>(Component))
            {
                if (Primitive->IsVisible()
                    || Primitive->GetCollisionEnabled() != ECollisionEnabled::NoCollision
                    || Primitive->GetGenerateOverlapEvents())
                {
                    return false;
                }
            }
        }
        return true;
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopNativeUMGOnlyControlShellTest,
    "LineBoss.PaintShop.Experimental.PlayerControls.UI.NativeUMGOnlyNoCanvas",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopNativeUMGOnlyControlShellTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    TestFalse(TEXT("Paint HUD declares no Canvas rendering path"),
        ALBPaintShopPrototypeHUD::UsesCanvasRendering());

    ULBPaintShopPrototypeRootWidget* Widget =
        NewObject<ULBPaintShopPrototypeRootWidget>();
    TestNotNull(TEXT("Native Paint UMG root widget can be instantiated"), Widget);
    if (!Widget) return false;
    TestTrue(TEXT("Native Paint UMG root widget initializes"), Widget->Initialize());
    const TSharedRef<SWidget> SlateShell = Widget->TakeWidget();
    (void)SlateShell;
    TestTrue(TEXT("Native Paint UMG root owns a complete renderable tree"),
        Widget->HasRenderableShell());

    const TArray<FName> Controls =
        ULBPaintShopPrototypeRootWidget::GetCanonicalControlIds();
    TestEqual(TEXT("Paint UMG shell exposes six bounded operator controls"),
        Controls.Num(), 6);
    TSet<FName> DistinctControls;
    for (const FName Control : Controls) DistinctControls.Add(Control);
    TestEqual(TEXT("Paint UMG control IDs are stable and unique"),
        DistinctControls.Num(), Controls.Num());

    const FName ButtonNames[] = {TEXT("PaintShopStart"), TEXT("PaintShopPause"),
        TEXT("PaintShopBlock"), TEXT("PaintShopRelease"),
        TEXT("PaintShopSave"), TEXT("PaintShopLoad")};
    for (const FName ButtonName : ButtonNames)
    {
        UButton* Button = Cast<UButton>(Widget->GetWidgetFromName(ButtonName));
        TestNotNull(FString::Printf(TEXT("%s is a real UMG button"),
            *ButtonName.ToString()), Button);
        if (Button)
        {
            TestTrue(FString::Printf(TEXT("%s delegates a bounded command"),
                *ButtonName.ToString()), Button->OnClicked.IsBound());
        }
    }

    FString HUDSource;
    const FString HUDSourcePath = FPaths::Combine(FPaths::ProjectDir(),
        TEXT("Source/LineBossCarFactory/LBPaintShopPrototypeHUD.cpp"));
    TestTrue(TEXT("Paint HUD host source is available to the Editor automation gate"),
        FFileHelper::LoadFileToString(HUDSource, *HUDSourcePath));
    TestFalse(TEXT("Paint HUD host has no DrawHUD override"),
        HUDSource.Contains(TEXT("DrawHUD(")));
    TestFalse(TEXT("Paint HUD host does not include Engine Canvas"),
        HUDSource.Contains(TEXT("Engine/Canvas.h")));
    TestTrue(TEXT("Paint HUD host constructs the native UMG root"),
        HUDSource.Contains(TEXT("CreateWidget<ULBPaintShopPrototypeRootWidget>")));

    const FString OperatorControls = ALBPaintShopPrototypeHUD::GetOperatorControlsReadout();
    TestTrue(TEXT("UMG shell names every deterministic operator key"),
        OperatorControls.Contains(TEXT("SPACE")) && OperatorControls.Contains(TEXT("P PAUSE"))
        && OperatorControls.Contains(TEXT("O BLOCK")) && OperatorControls.Contains(TEXT("R RELEASE"))
        && OperatorControls.Contains(TEXT("F5 SAVE")) && OperatorControls.Contains(TEXT("F9 LOAD")));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopPlayerControlLiveWorldTest,
    "LineBoss.PaintShop.Experimental.PlayerControls.World.CanonicalHandoffPauseReleaseSaveLoad",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopPlayerControlLiveWorldTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    const FString ValidSlot = FString::Printf(
        TEXT("LineBossPaintShopExperimental_Automation_Player_%s"),
        *FGuid::NewGuid().ToString(EGuidFormats::Digits));
    const FString InvalidSlot = FString::Printf(
        TEXT("LineBossPaintShopExperimental_Automation_Invalid_%s"),
        *FGuid::NewGuid().ToString(EGuidFormats::Digits));
    const int32 UserIndex = ULBPaintShopExperimentalSaveGame::GetUserIndex();
    UGameplayStatics::DeleteGameInSlot(ValidSlot, UserIndex);
    UGameplayStatics::DeleteGameInSlot(InvalidSlot, UserIndex);

    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBPaintShopPlayerControlLiveWorldTest"));
    ALBPaintShopPrototypeWorldBootstrap* Bootstrap = World
        ? World->SpawnActor<ALBPaintShopPrototypeWorldBootstrap>() : nullptr;
    FString Reason;
    if (!TestNotNull(TEXT("Player-control world owns one Paint bootstrap"), Bootstrap)
        || !TestTrue(TEXT("Bootstrap creates its isolated Paint authority pair"),
            Bootstrap && Bootstrap->InitializePrototypeWorld(Reason)))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    ALBPaintShopPrototypeGameMode* Mode =
        World->SpawnActor<ALBPaintShopPrototypeGameMode>();
    APlayerController* Controller = World->SpawnActor<APlayerController>();
    ALBPaintShopManagementPawn* Pawn = World->SpawnActor<ALBPaintShopManagementPawn>();
    ALBPaintShopPrototypeRuntime* Runtime = Bootstrap->GetRuntime();
    if (!TestNotNull(TEXT("Player-control GameMode exists"), Mode)
        || !TestNotNull(TEXT("Player-control controller exists"), Controller)
        || !TestNotNull(TEXT("Player-control presentation pawn exists"), Pawn)
        || !TestNotNull(TEXT("Player-control runtime authority exists"), Runtime))
    {
        World->DestroyWorld(false);
        return false;
    }
    Controller->Possess(Pawn);
    if (!TestTrue(TEXT("Player-control shell validates before accepting commands"),
        Mode->ValidatePrototypeShellNow(Controller)))
    {
        World->DestroyWorld(false);
        return false;
    }

    FLBPaintShopExperimentalSaveState InitialState;
    TestTrue(TEXT("Initial state is captured before blocked release"),
        Runtime->CaptureSaveState(InitialState, Reason));
    TestFalse(TEXT("Release fails closed before an output exists"),
        Mode->ReleasePaintOutput(Reason));
    FLBPaintShopExperimentalSaveState AfterInitialReleaseFailure;
    TestTrue(TEXT("Initial failed release leaves Paint state unchanged"),
        Runtime->CaptureSaveState(AfterInitialReleaseFailure, Reason)
        && LBPaintShopPlayerControlTestsPrivate::HasIdenticalState(
            InitialState, AfterInitialReleaseFailure));

    TestTrue(TEXT("Start manufactures and accepts one canonical Weld body"),
        Mode->StartCanonicalWeldHandoff(Reason));
    FLBPaintShopWIPSaveState AcceptedWIP;
    TestTrue(TEXT("Paint owns exactly one acknowledged v2 Weld lineage"),
        Runtime->GetActiveWIP(AcceptedWIP)
        && AcceptedWIP.Version == 2
        && AcceptedWIP.SourceBodyInWhite.bEDAccepted
        && AcceptedWIP.SourceBodyInWhite.QualityState == ELBBodyWeldQualityState::Good
        && AcceptedWIP.SourceBodyInWhite.Panels.Num() == 11
        && AcceptedWIP.SourceBodyInWhite.QualityEvidence.bRecipeComplete
        && AcceptedWIP.SourceBodyInWhite.QualityEvidence.bSpotOperationsComplete
        && AcceptedWIP.SourceBodyInWhite.QualityEvidence.bMIGOperationsComplete);
    TestEqual(TEXT("Exactly one transient Weld provenance source exists while WIP is active"),
        LBPaintShopPlayerControlTestsPrivate::CountLiveWeldSources(World), 1);
    TestTrue(TEXT("Transient Weld provenance source has no render, collision or tick presence"),
        LBPaintShopPlayerControlTestsPrivate::IsCompletelyIsolatedSource(
            Mode->GetOperatorWeldSourceForTests()));

    FLBPaintShopExperimentalSaveState BeforeDoubleStart;
    TestTrue(TEXT("State before duplicate start is captured"),
        Runtime->CaptureSaveState(BeforeDoubleStart, Reason));
    TestFalse(TEXT("Double start is rejected before a second handoff"),
        Mode->StartCanonicalWeldHandoff(Reason));
    FLBPaintShopExperimentalSaveState AfterDoubleStart;
    TestTrue(TEXT("Rejected double start leaves exact WIP and counters unchanged"),
        Runtime->CaptureSaveState(AfterDoubleStart, Reason)
        && LBPaintShopPlayerControlTestsPrivate::HasIdenticalState(
            BeforeDoubleStart, AfterDoubleStart));
    TestEqual(TEXT("Rejected double start creates no second Weld source"),
        LBPaintShopPlayerControlTestsPrivate::CountLiveWeldSources(World), 1);

    Runtime->AdvanceSimulation(4.0f);
    const float BeforePauseProgress = Runtime->GetCycleProgress01();
    TestTrue(TEXT("Player can pause one in-flight Paint WIP"),
        Mode->ToggleProcessPause(Reason) && Runtime->IsPaused());
    Runtime->AdvanceSimulation(8.0f);
    TestTrue(TEXT("Paused Paint process has no deterministic drift"),
        FMath::IsNearlyEqual(Runtime->GetCycleProgress01(), BeforePauseProgress));
    FLBPaintShopExperimentalSaveState PausedState;
    TestTrue(TEXT("Paused in-flight state captures exact lineage and operator hold"),
        Runtime->CaptureSaveState(PausedState, Reason)
        && PausedState.Cells.Num() == 1 && PausedState.Cells[0].bProcessPaused);
    TestTrue(TEXT("Paused in-flight state saves to the isolated Paint test slot"),
        Mode->SavePaintStateToAutomationSlot(ValidSlot, Reason));
    TestTrue(TEXT("Player can resume the exact paused WIP"),
        Mode->ToggleProcessPause(Reason) && !Runtime->IsPaused());
    Runtime->AdvanceSimulation(1.0f);
    TestTrue(TEXT("Loading the paused snapshot restores exact progress and pause state"),
        Mode->LoadPaintStateFromAutomationSlot(ValidSlot, Reason));
    FLBPaintShopExperimentalSaveState ReloadedPausedState;
    TestTrue(TEXT("Paused reload is exact and cannot drift while held"),
        Runtime->CaptureSaveState(ReloadedPausedState, Reason)
        && Runtime->IsPaused()
        && LBPaintShopPlayerControlTestsPrivate::HasIdenticalState(
            PausedState, ReloadedPausedState));
    Runtime->AdvanceSimulation(8.0f);
    TestTrue(TEXT("Reloaded paused WIP still has no drift"),
        FMath::IsNearlyEqual(Runtime->GetCycleProgress01(), BeforePauseProgress));
    TestEqual(TEXT("Paused reload does not synthesize a Weld source"),
        LBPaintShopPlayerControlTestsPrivate::CountLiveWeldSources(World), 0);
    TestTrue(TEXT("Player resumes the exact reloaded paused WIP"),
        Mode->ToggleProcessPause(Reason) && !Runtime->IsPaused());
    Runtime->AdvanceSimulation(6.0f);
    TestEqual(TEXT("Resumed Paint process reaches retained output"),
        Runtime->GetPhase(), ELBPaintShopPrototypePhase::OutputReady);

    TestTrue(TEXT("Player can apply the downstream output block"),
        Mode->ToggleOutputBlock(Reason) && Runtime->IsOutputBlocked());
    FLBPaintShopExperimentalSaveState BeforeBlockedRelease;
    TestTrue(TEXT("Blocked output state captures exact WIP"),
        Runtime->CaptureSaveState(BeforeBlockedRelease, Reason));
    TestFalse(TEXT("Blocked release fails closed and retains coated WIP"),
        Mode->ReleasePaintOutput(Reason));
    FLBPaintShopExperimentalSaveState AfterBlockedRelease;
    TestTrue(TEXT("Blocked release leaves lineage, progress and counters unchanged"),
        Runtime->CaptureSaveState(AfterBlockedRelease, Reason)
        && LBPaintShopPlayerControlTestsPrivate::HasIdenticalState(
            BeforeBlockedRelease, AfterBlockedRelease));

    TestTrue(TEXT("Player save writes only a unique isolated Paint automation slot"),
        Mode->SavePaintStateToAutomationSlot(ValidSlot, Reason));
    const FLBPaintShopExperimentalSaveState SavedBlockedState = BeforeBlockedRelease;
    TestTrue(TEXT("Unblock command clears the retained output hold"),
        Mode->ToggleOutputBlock(Reason) && !Runtime->IsOutputBlocked());
    TestTrue(TEXT("Unblocked output releases and returns to starvation"),
        Mode->ReleasePaintOutput(Reason) && Runtime->IsStarved());
    TestEqual(TEXT("Successful output release removes transient Weld provenance source"),
        LBPaintShopPlayerControlTestsPrivate::CountLiveWeldSources(World), 0);

    TestTrue(TEXT("Player load restores the exact isolated blocked-output state"),
        Mode->LoadPaintStateFromAutomationSlot(ValidSlot, Reason));
    FLBPaintShopExperimentalSaveState ReloadedState;
    TestTrue(TEXT("Reload preserves exact WIP, Weld lineage, progress, flags and counters"),
        Runtime->CaptureSaveState(ReloadedState, Reason)
        && LBPaintShopPlayerControlTestsPrivate::HasIdenticalState(
            SavedBlockedState, ReloadedState));
    TestEqual(TEXT("Reload never synthesizes a replacement Weld source"),
        LBPaintShopPlayerControlTestsPrivate::CountLiveWeldSources(World), 0);
    TestFalse(TEXT("Reloaded active WIP rejects a duplicate start"),
        Mode->StartCanonicalWeldHandoff(Reason));
    FLBPaintShopExperimentalSaveState AfterReloadedDoubleStart;
    TestTrue(TEXT("Reloaded duplicate start leaves exactly one WIP unchanged"),
        Runtime->CaptureSaveState(AfterReloadedDoubleStart, Reason)
        && LBPaintShopPlayerControlTestsPrivate::HasIdenticalState(
            ReloadedState, AfterReloadedDoubleStart));

    ULBPaintShopExperimentalSaveGame* InvalidSave =
        Cast<ULBPaintShopExperimentalSaveGame>(UGameplayStatics::CreateSaveGameObject(
            ULBPaintShopExperimentalSaveGame::StaticClass()));
    TestNotNull(TEXT("Invalid-load fixture uses the isolated Paint save root"), InvalidSave);
    if (InvalidSave && ReloadedState.WIP.Num() == 1)
    {
        InvalidSave->State = ReloadedState;
        InvalidSave->State.WIP.Add(ReloadedState.WIP[0]);
        TestTrue(TEXT("Corrupt duplicate-WIP fixture writes only its unique test slot"),
            UGameplayStatics::SaveGameToSlot(InvalidSave, InvalidSlot, UserIndex));
        TestFalse(TEXT("Invalid duplicate-WIP load fails before runtime mutation"),
            Mode->LoadPaintStateFromAutomationSlot(InvalidSlot, Reason));
        FLBPaintShopExperimentalSaveState AfterInvalidLoad;
        TestTrue(TEXT("Invalid load leaves the exact live Paint state unchanged"),
            Runtime->CaptureSaveState(AfterInvalidLoad, Reason)
            && LBPaintShopPlayerControlTestsPrivate::HasIdenticalState(
                ReloadedState, AfterInvalidLoad));
    }
    else
    {
        TestTrue(TEXT("Invalid-load fixture requires one restored WIP"), false);
    }

    TestTrue(TEXT("Reloaded blocked output can be unblocked"),
        Mode->ToggleOutputBlock(Reason) && !Runtime->IsOutputBlocked());
    TestTrue(TEXT("Reloaded exact coated output releases once and only once"),
        Mode->ReleasePaintOutput(Reason) && Runtime->IsStarved());
    TestFalse(TEXT("A second release cannot duplicate the same output"),
        Mode->ReleasePaintOutput(Reason));

    UGameplayStatics::DeleteGameInSlot(ValidSlot, UserIndex);
    UGameplayStatics::DeleteGameInSlot(InvalidSlot, UserIndex);
    World->DestroyWorld(false);
    return true;
}

#endif
