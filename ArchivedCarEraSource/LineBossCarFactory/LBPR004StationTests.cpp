#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "LBPR004Station.h"
#include "LBPR004HMIWidget.h"
#include "LBManagementPawn.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Components/WidgetComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBPR004CommissioningInterlockTest,
    "LineBoss.PressShop.PR004.CommissioningInterlocks",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBPR004StableSaveRoundTripTest,
    "LineBoss.PressShop.PR004.StableSaveRoundTrip",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBPR004SimpleUnpackageInteractionTest,
    "LineBoss.PressShop.PR004.SimpleUnpackageInteraction",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

namespace
{
    struct FLBTransientPR004World
    {
        UWorld* World = nullptr;

        FLBTransientPR004World(const FName WorldName)
        {
            World = UWorld::CreateWorld(EWorldType::Game, false, WorldName);
            if (World)
            {
                FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
                Context.SetCurrentWorld(World);
                World->InitializeActorsForPlay(FURL());
                World->BeginPlay();
            }
        }

        ~FLBTransientPR004World()
        {
            if (World)
            {
                World->DestroyWorld(false);
                GEngine->DestroyWorldContext(World);
            }
        }

        ALBPR004Station* SpawnStation() const
        {
            return World
                ? World->SpawnActor<ALBPR004Station>(ALBPR004Station::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator)
                : nullptr;
        }
    };

    FLBPR004WasteStreamStatus ReadyWasteStream(const bool bNeedsEject)
    {
        FLBPR004WasteStreamStatus Status;
        Status.bEquipmentHealthy = true;
        Status.bGuardClosed = true;
        Status.bBinPresent = true;
        Status.bCapacityAvailable = true;
        Status.bEjectReady = bNeedsEject;
        return Status;
    }

    FLBPR004FilmDewrapStatus ReadyFilmDewrap()
    {
        FLBPR004FilmDewrapStatus Status;
        Status.bSpindleHealthy = true;
        Status.bDancerAndTensionHealthy = true;
        Status.bCradleSpindleSynchronized = true;
        Status.bRobotClearForIndex = true;
        Status.bSpindleGripConfirmed = true;
        Status.bTransferChuteClear = true;
        Status.bStripperReady = true;
        Status.bFragmentCameraClear = true;
        return Status;
    }

    UStaticMeshComponent* FindPresentationComponent(ALBPR004Station* Station, const FName ComponentName)
    {
        if (!Station)
        {
            return nullptr;
        }
        TArray<UStaticMeshComponent*> Components;
        Station->GetComponents<UStaticMeshComponent>(Components);
        for (UStaticMeshComponent* Component : Components)
        {
            if (Component && Component->GetFName() == ComponentName)
            {
                return Component;
            }
        }
        return nullptr;
    }

    template<typename TComponent>
    TComponent* FindNamedComponent(ALBPR004Station* Station, const FName ComponentName)
    {
        if (!Station)
        {
            return nullptr;
        }
        TArray<TComponent*> Components;
        Station->GetComponents<TComponent>(Components);
        for (TComponent* Component : Components)
        {
            if (Component && Component->GetFName() == ComponentName)
            {
                return Component;
            }
        }
        return nullptr;
    }

    bool PrepareAwaitingAuthorisation(ALBPR004Station* Station, const FString& CoilId)
    {
        return Station
            && Station->SetControlPower(true)
            && Station->SetCellCommissioned(true)
            && Station->SetSafetyInputs(true, true, true)
            && Station->SetRobotHealthy(true)
            && Station->SetInspectionSystemsHealthy(true, true)
            && Station->SetWasteStreamStatus(ELBPR004WasteStream::SteelBand, ReadyWasteStream(true))
            && Station->SetWasteStreamStatus(ELBPR004WasteStream::EdgeProtector, ReadyWasteStream(false))
            && Station->SetWasteStreamStatus(ELBPR004WasteStream::PlasticWrap, ReadyWasteStream(true))
            && Station->SetFilmDewrapStatus(ReadyFilmDewrap())
            && Station->LoadPackagedCoil(CoilId)
            && Station->SelectDepackRecipe(TEXT("PR004_DEPACK_STANDARD"), CoilId)
            && Station->SetCradleLocked(true)
            && Station->SetCHookWithdrawn(true);
    }
}

bool FLBPR004CommissioningInterlockTest::RunTest(const FString& Parameters)
{
    FLBTransientPR004World TestWorld(TEXT("LB_PR004_CommissioningInterlockTest"));
    TestNotNull(TEXT("Transient PR-004 runtime world exists"), TestWorld.World);
    ALBPR004Station* Station = TestWorld.SpawnStation();
    TestNotNull(TEXT("Native PR-004 station spawns"), Station);
    if (!Station)
    {
        return false;
    }

    TestEqual(TEXT("Fresh station begins unsurveyed"), Station->GetProcessState(), ELBPR004State::Unsurveyed);
    TestFalse(TEXT("Commissioning is rejected without control power"), Station->SetCellCommissioned(true));
    TestTrue(TEXT("Release-ready inputs prepare an authorised coil"),
        PrepareAwaitingAuthorisation(Station, TEXT("MCX-U-000401")));
    TestEqual(TEXT("Prepared station awaits authorisation"),
        Station->GetProcessState(), ELBPR004State::AwaitingAuthorisation);

    TArray<FText> BlockingReasons;
    TestTrue(TEXT("All required permissives allow cycle authorisation"),
        Station->CanAuthoriseCycle(BlockingReasons));
    TestEqual(TEXT("Authorisation has no blockers"), BlockingReasons.Num(), 0);
    TestTrue(TEXT("Automatic cycle enters packaging scan"), Station->AuthoriseAutomaticCycle());
    TestEqual(TEXT("Station is scanning"), Station->GetProcessState(), ELBPR004State::Scanning);

    FLBPR004PackagingScanReport ScanReport;
    ScanReport.ReportId = TEXT("SCAN_PR004_000401");
    ScanReport.CoilId = TEXT("MCX-U-000401");
    ScanReport.RecipeId = TEXT("PR004_DEPACK_STANDARD");
    ScanReport.DetectedBandMask = 0x0F;
    ScanReport.DetectedProtectorMask = 0xFF;
    ScanReport.DetectedWrapMask = 0xFFFF;
    ScanReport.bScannerHealthy = true;
    ScanReport.bIdentityReadable = true;
    ScanReport.bDimensionsWithinRecipe = true;
    ScanReport.bPackagingClassificationComplete = true;
    const int64 ScanToken = Station->GetActivePackagingScanRequestToken();
    TestTrue(TEXT("Packaging scan exposes a request token"), ScanToken > 0);
    TestTrue(TEXT("Valid packaging scan advances to securing motion"),
        Station->SubmitPackagingScanReport(ScanToken, ScanReport));
    TestEqual(TEXT("Station enters securing motion"), Station->GetProcessState(), ELBPR004State::Securing);

    TestTrue(TEXT("Gate input mutation is accepted"), Station->SetSafetyInputs(false, true, true));
    TestEqual(TEXT("Opening a gate during motion latches the safety fault"),
        Station->GetActiveFault(), ELBPR004Fault::GateOrSafetyInterlockOpen);
    TestEqual(TEXT("Safety fault forces the fault state"), Station->GetProcessState(), ELBPR004State::Fault);
    TestFalse(TEXT("Fault cannot reset while the gate remains open"), Station->ResetFault(TEXT("EVID_GATE_OPEN")));
    TestTrue(TEXT("Closed gate restores the safety input"), Station->SetSafetyInputs(true, true, true));
    TestTrue(TEXT("Proved recovery evidence resets the safety fault"), Station->ResetFault(TEXT("EVID_GATE_PROVED")));
    TestEqual(TEXT("Reset resumes interrupted securing motion"), Station->GetProcessState(), ELBPR004State::Securing);

    TestTrue(TEXT("Control power can be removed during scan"), Station->SetControlPower(false));
    TestTrue(TEXT("Interrupted scan requires explicit power-loss reconciliation"),
        Station->GetActiveFault() == ELBPR004Fault::PowerLossReconciliationRequired
            || Station->GetActiveFault() == ELBPR004Fault::InFlightMaterialOwnershipUnclear);
    TestTrue(TEXT("Control power restores without silently clearing the fault"), Station->SetControlPower(true));
    TestEqual(TEXT("Power-loss fault remains latched"), Station->GetProcessState(), ELBPR004State::Fault);
    TestTrue(TEXT("Explicit material ownership reconciliation succeeds"),
        Station->ReconcilePowerLoss(ELBPR004MaterialOwner::Coil, TEXT("EVID_POWERLOSS_OWNER")));
    TestEqual(TEXT("Reconciliation resumes interrupted securing motion"),
        Station->GetProcessState(), ELBPR004State::Securing);
    TestEqual(TEXT("Reconciliation clears the active fault"),
        Station->GetActiveFault(), ELBPR004Fault::None);
    return true;
}

bool FLBPR004StableSaveRoundTripTest::RunTest(const FString& Parameters)
{
    FLBTransientPR004World TestWorld(TEXT("LB_PR004_StableSaveRoundTripTest"));
    TestNotNull(TEXT("Transient PR-004 save world exists"), TestWorld.World);
    ALBPR004Station* Source = TestWorld.SpawnStation();
    ALBPR004Station* Reloaded = TestWorld.SpawnStation();
    TestNotNull(TEXT("Source PR-004 station spawns"), Source);
    TestNotNull(TEXT("Reload target PR-004 station spawns"), Reloaded);
    if (!Source || !Reloaded)
    {
        return false;
    }

    TestTrue(TEXT("Source reaches a stable awaiting-authorisation boundary"),
        PrepareAwaitingAuthorisation(Source, TEXT("MCX-U-000402")));
    TestTrue(TEXT("Awaiting authorisation is a stable save boundary"), Source->IsAtStableSaveBoundary());

    FLBPR004SaveState Saved;
    TestTrue(TEXT("Stable station state captures coherently"), Source->GetStableSaveState(Saved));
    TestEqual(TEXT("Save records the active coil"), Saved.CoilId, FString(TEXT("MCX-U-000402")));
    TestFalse(TEXT("Save records a non-empty steel heat"), Saved.HeatId.IsEmpty());
    TestFalse(TEXT("Save records a non-empty supplier lot"), Saved.SupplierLotId.IsEmpty());
    TestFalse(TEXT("Save records a non-empty traceability barcode"), Saved.TraceabilityBarcode.IsEmpty());
    TestEqual(TEXT("Save records the approved recipe"), Saved.RecipeId, FName(TEXT("PR004_DEPACK_STANDARD")));
    TestTrue(TEXT("Save records the locked cradle"), Saved.bCradleLocked);
    TestTrue(TEXT("Save records the withdrawn crane hook"), Saved.bCHookWithdrawn);

    TestTrue(TEXT("Fresh station accepts the coherent stable save"), Reloaded->RestoreSaveState(Saved));
    TestEqual(TEXT("Reload restores process state"),
        Reloaded->GetProcessState(), ELBPR004State::AwaitingAuthorisation);
    TArray<FText> ReloadBlockers;
    TestTrue(TEXT("Reload preserves all authorisation permissives"),
        Reloaded->CanAuthoriseCycle(ReloadBlockers));
    TestEqual(TEXT("Reload has no new authorisation blockers"), ReloadBlockers.Num(), 0);

    FLBPR004SaveState Recaptured;
    TestTrue(TEXT("Reloaded state recaptures coherently"), Reloaded->GetStableSaveState(Recaptured));
    TestEqual(TEXT("Round trip preserves coil identity"), Recaptured.CoilId, Saved.CoilId);
    TestEqual(TEXT("Round trip preserves steel heat"), Recaptured.HeatId, Saved.HeatId);
    TestEqual(TEXT("Round trip preserves supplier lot"), Recaptured.SupplierLotId, Saved.SupplierLotId);
    TestEqual(TEXT("Round trip preserves traceability barcode"), Recaptured.TraceabilityBarcode, Saved.TraceabilityBarcode);
    TestTrue(TEXT("Reload regenerates the live heat/lot label"),
        Reloaded->GetWrappedCoilTraceLabelText().Contains(Saved.HeatId)
        && Reloaded->GetWrappedCoilTraceLabelText().Contains(Saved.SupplierLotId));
    TestEqual(TEXT("Round trip preserves active cycle serial"), Recaptured.ActiveCycleSerial, Saved.ActiveCycleSerial);
    TestEqual(TEXT("Round trip preserves next cycle serial"), Recaptured.NextCycleSerial, Saved.NextCycleSerial);

    FLBPR004SaveState Invalid = Saved;
    Invalid.SaveVersion += 100;
    TArray<FText> CoherenceErrors;
    TestFalse(TEXT("Unsupported save version is incoherent"),
        Reloaded->IsSaveStateCoherent(Invalid, CoherenceErrors));
    TestTrue(TEXT("Unsupported save version reports an error"), CoherenceErrors.Num() > 0);
    TestFalse(TEXT("Unsupported save version is rejected on restore"), Reloaded->RestoreSaveState(Invalid));
    TestEqual(TEXT("Rejected restore leaves current process state intact"),
        Reloaded->GetProcessState(), ELBPR004State::AwaitingAuthorisation);
    return true;
}

bool FLBPR004SimpleUnpackageInteractionTest::RunTest(const FString& Parameters)
{
    FLBTransientPR004World TestWorld(TEXT("LB_PR004_SimpleUnpackageInteractionTest"));
    TestNotNull(TEXT("Transient PR-004 interaction world exists"), TestWorld.World);
    ALBPR004Station* Source = TestWorld.SpawnStation();
    ALBPR004Station* Reloaded = TestWorld.SpawnStation();
    TestNotNull(TEXT("Source PR-004 station spawns"), Source);
    TestNotNull(TEXT("Reload target PR-004 station spawns"), Reloaded);
    if (!Source || !Reloaded)
    {
        return false;
    }

    TestTrue(TEXT("Control power enables simplified station"), Source->SetControlPower(true));
    TestTrue(TEXT("Simplified station commissions"), Source->SetCellCommissioned(true));
    TestTrue(TEXT("Packaged coil loads"), Source->LoadPackagedCoil(TEXT("MCX-U-000403")));
    TestTrue(TEXT("Player-selected coil receives its recipe"),
        Source->SelectDepackRecipe(TEXT("PR004_DEPACK_STANDARD"), TEXT("MCX-U-000403")));
    TestTrue(TEXT("Preparation stand locks the coil"), Source->SetCradleLocked(true));
    TestTrue(TEXT("Crane hook clears the stand"), Source->SetCHookWithdrawn(true));
    TestFalse(TEXT("Missing interaction evidence is rejected"), Source->UnpackageCoil(NAME_None));

    TArray<FText> UnpackageBlockers;
    TestTrue(TEXT("Prepared station exposes the guarded Unpackage action"),
        Source->CanUnpackageCoil(UnpackageBlockers));
    TestEqual(TEXT("Prepared station reports no Unpackage blockers"), UnpackageBlockers.Num(), 0);

    UStaticMeshComponent* WrappedVisual = FindPresentationComponent(Source, TEXT("PR004_WrappedCoilVisual"));
    UStaticMeshComponent* WrappedLabelVisual = FindPresentationComponent(Source, TEXT("PR004_WrappedCoilLabelVisual"));
    UStaticMeshComponent* BareVisual = FindPresentationComponent(Source, TEXT("PR004_BareCoilVisual"));
    UTextRenderComponent* WrappedLabelHeading = FindNamedComponent<UTextRenderComponent>(Source, TEXT("PR004_WrappedCoilLabelHeading"));
    UTextRenderComponent* WrappedLabelDetail = FindNamedComponent<UTextRenderComponent>(Source, TEXT("PR004_WrappedCoilLabelDetail"));
    UWidgetComponent* OperatorHMI = FindNamedComponent<UWidgetComponent>(Source, TEXT("PR004_OperatorHMI"));
    TestNotNull(TEXT("Wrapped presentation component exists"), WrappedVisual);
    TestNotNull(TEXT("Reusable wrapped-label presentation component exists"), WrappedLabelVisual);
    TestNotNull(TEXT("Wrapped label heading component exists"), WrappedLabelHeading);
    TestNotNull(TEXT("Wrapped label detail component exists"), WrappedLabelDetail);
    TestNotNull(TEXT("Bare presentation component exists"), BareVisual);
    TestNotNull(TEXT("Physical operator HMI component exists"), OperatorHMI);
    TestTrue(TEXT("Physical HMI is bound to the native Cairnwell screen class"),
        OperatorHMI && OperatorHMI->GetWidgetClass() == ULBPR004HMIWidget::StaticClass());
    TestTrue(TEXT("Loaded packaged coil shows wrapped presentation"), WrappedVisual && WrappedVisual->IsVisible());
    TestTrue(TEXT("Loaded packaged coil shows wrapped label"), WrappedLabelVisual && WrappedLabelVisual->IsVisible());
    TestTrue(TEXT("Loaded packaged coil shows label heading"), WrappedLabelHeading && WrappedLabelHeading->IsVisible());
    TestTrue(TEXT("Loaded packaged coil shows label detail"), WrappedLabelDetail && WrappedLabelDetail->IsVisible());
    TestFalse(TEXT("Loaded packaged coil hides bare presentation"), BareVisual && BareVisual->IsVisible());

    // No robot, cage, waste-module, scanner or vision-system health inputs are
    // supplied: the player-facing action deliberately does not require them.
    ALBManagementPawn* ManagementPawn = TestWorld.World->SpawnActor<ALBManagementPawn>(
        ALBManagementPawn::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator);
    TestNotNull(TEXT("Management interaction pawn spawns"), ManagementPawn);
    TestTrue(TEXT("Player interaction route atomically prepares the coil"),
        ManagementPawn && ManagementPawn->InteractWithActor(Source));
    TestTrue(TEXT("Coil presentation state is bare"), Source->IsCoilUnpackaged());
    TestFalse(TEXT("Unpackage hides wrapped presentation"), WrappedVisual && WrappedVisual->IsVisible());
    TestFalse(TEXT("Unpackage hides wrapped label"), WrappedLabelVisual && WrappedLabelVisual->IsVisible());
    TestFalse(TEXT("Unpackage hides wrapped label heading"), WrappedLabelHeading && WrappedLabelHeading->IsVisible());
    TestFalse(TEXT("Unpackage hides wrapped label detail"), WrappedLabelDetail && WrappedLabelDetail->IsVisible());
    TestTrue(TEXT("Unpackage shows bare presentation"), BareVisual && BareVisual->IsVisible());
    TestEqual(TEXT("Simplified action reaches handoff state"),
        Source->GetProcessState(), ELBPR004State::ReadyForHandoff);
    TestEqual(TEXT("Simplified action records ready disposition"),
        Source->GetDisposition(), ELBPR004Disposition::Ready);
    TArray<FText> ReleaseBlockers;
    TestTrue(TEXT("Prepared coil is valid for PR-005 handoff"), Source->CanReleaseCoil(ReleaseBlockers));
    TestEqual(TEXT("Simplified handoff has no blockers"), ReleaseBlockers.Num(), 0);

    FLBPR004SaveState Saved;
    TestTrue(TEXT("Simplified ready state is saveable"), Source->GetStableSaveState(Saved));
    TestTrue(TEXT("Fresh station restores simplified ready state"), Reloaded->RestoreSaveState(Saved));
    TestTrue(TEXT("Reload preserves bare-coil presentation state"), Reloaded->IsCoilUnpackaged());
    UStaticMeshComponent* ReloadedWrappedVisual = FindPresentationComponent(Reloaded, TEXT("PR004_WrappedCoilVisual"));
    UStaticMeshComponent* ReloadedBareVisual = FindPresentationComponent(Reloaded, TEXT("PR004_BareCoilVisual"));
    TestFalse(TEXT("Reload keeps wrapped presentation hidden"), ReloadedWrappedVisual && ReloadedWrappedVisual->IsVisible());
    TestTrue(TEXT("Reload keeps bare presentation visible"), ReloadedBareVisual && ReloadedBareVisual->IsVisible());
    TestEqual(TEXT("Reload preserves handoff state"),
        Reloaded->GetProcessState(), ELBPR004State::ReadyForHandoff);
    return true;
}

#endif
