#include "LBOneFactoryPlayerController.h"

#include "Components/InputComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBOneFactoryDevEnvelopeActor.h"
#include "LBOneFactoryDevFactoryCommands.h"
#include "LBOneFactoryDevRestoredShopActor.h"
#include "LBOneFactoryDevStationDressingActor.h"
#include "LBOneFactoryOperationsSubsystem.h"
#include "LBOneFactoryPressStarterPresentationActor.h"
#include "LBOneFactoryProductionFlow.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "LBOneFactorySaveSubsystem.h"
#include "LBOneFactoryWIPPresentationActor.h"

DEFINE_LOG_CATEGORY_STATIC(LogLineBossOneFactoryPlayer, Display, All);

namespace LBOneFactoryPlayerPrivate
{
    ALBOneFactoryRuntimeCoordinator* FindCoordinator(const UWorld* World)
    {
        if (!World)
        {
            return nullptr;
        }
        for (TActorIterator<ALBOneFactoryRuntimeCoordinator> It(World); It; ++It)
        {
            if (IsValid(*It))
            {
                return *It;
            }
        }
        return nullptr;
    }

    ALBOneFactoryProductionFlowAuthority* FindProduction(const UWorld* World)
    {
        if (!World)
        {
            return nullptr;
        }
        for (TActorIterator<ALBOneFactoryProductionFlowAuthority> It(World);
            It; ++It)
        {
            if (IsValid(*It))
            {
                return *It;
            }
        }
        return nullptr;
    }
}

ALBOneFactoryPlayerController::ALBOneFactoryPlayerController()
{
    PrimaryActorTick.bCanEverTick = false;
    bShowMouseCursor = true;
}

void ALBOneFactoryPlayerController::SetupInputComponent()
{
    Super::SetupInputComponent();
    if (!InputComponent)
    {
        return;
    }

    InputComponent->BindKey(EKeys::B, IE_Pressed, this,
        &ALBOneFactoryPlayerController::CommissionFactory);
    InputComponent->BindKey(EKeys::N, IE_Pressed, this,
        &ALBOneFactoryPlayerController::PlaceOrder);
    InputComponent->BindKey(EKeys::SpaceBar, IE_Pressed, this,
        &ALBOneFactoryPlayerController::TogglePause);
    InputComponent->BindKey(EKeys::One, IE_Pressed, this,
        &ALBOneFactoryPlayerController::SetSpeedNormal);
    InputComponent->BindKey(EKeys::Two, IE_Pressed, this,
        &ALBOneFactoryPlayerController::SetSpeedFast);
    InputComponent->BindKey(EKeys::Three, IE_Pressed, this,
        &ALBOneFactoryPlayerController::SetSpeedVeryFast);
    InputComponent->BindKey(EKeys::Q, IE_Pressed, this,
        &ALBOneFactoryPlayerController::PassOldestQualityHold);
    InputComponent->BindKey(EKeys::R, IE_Pressed, this,
        &ALBOneFactoryPlayerController::ReworkOldestQualityHold);
    InputComponent->BindKey(EKeys::M, IE_Pressed, this,
        &ALBOneFactoryPlayerController::ServicePlant);
    InputComponent->BindKey(EKeys::F5, IE_Pressed, this,
        &ALBOneFactoryPlayerController::SaveFactory);
    InputComponent->BindKey(EKeys::F9, IE_Pressed, this,
        &ALBOneFactoryPlayerController::LoadFactory);
}

void ALBOneFactoryPlayerController::ServicePlant()
{
    using namespace LBOneFactoryPlayerPrivate;

    ALBOneFactoryRuntimeCoordinator* Coordinator = FindCoordinator(GetWorld());
    if (!Coordinator)
    {
        return;
    }
    FString Reason;
    const bool bOk = Coordinator->PerformPlantMaintenance(Reason);
    UE_LOG(LogLineBossOneFactoryPlayer, Display,
        TEXT("LINE_BOSS_PLAYER_MAINTENANCE ok=%d %s"), bOk ? 1 : 0, *Reason);
}

void ALBOneFactoryPlayerController::CommissionFactory()
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    FString Reason;
    const bool bBuilt =
        ULBOneFactoryDevFactory::BuildAndCommissionWholeFactory(this, Reason);
    if (!bBuilt)
    {
        UE_LOG(LogLineBossOneFactoryPlayer, Warning,
            TEXT("LINE_BOSS_PLAYER_COMMISSION did not build: %s"), *Reason);
        // A restored or console-built factory reports "already built" here;
        // the site presentation must still come up for it, or a loaded game
        // strands the player over a bare lit plane.
        if (!ULBOneFactoryDevFactory::FindCoordinator(World))
        {
            return;
        }
    }
    else
    {
        UE_LOG(LogLineBossOneFactoryPlayer, Display,
            TEXT("LINE_BOSS_PLAYER_COMMISSION %s"), *Reason);
    }
    EnsureSitePresentation();
}

void ALBOneFactoryPlayerController::EnsureSitePresentation()
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    FActorSpawnParameters Params;
    Params.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

    // Bring the site up with the factory: enclosure, machinery, lighting and
    // the work-in-progress view. Every step finds an existing actor before
    // spawning, and every builder rebuilds its own content, so running this
    // after a save-load, a console build or a repeated B press converges on
    // exactly one of everything.
    FString StepReason;
    ALBOneFactoryDevEnvelopeActor* Envelope = nullptr;
    for (TActorIterator<ALBOneFactoryDevEnvelopeActor> It(World); It; ++It)
    {
        if (IsValid(*It)) { Envelope = *It; break; }
    }
    if (!Envelope)
    {
        Envelope = World->SpawnActor<ALBOneFactoryDevEnvelopeActor>(
            ALBOneFactoryDevEnvelopeActor::StaticClass(),
            FVector::ZeroVector, FRotator::ZeroRotator, Params);
    }
    if (Envelope)
    {
        // 2200 cm eaves: the restored shop's wide-span trusses hang at
        // 1740 cm with their top chords near 2000, so a 1400 wall left the
        // whole roof zone floating against void.
        Envelope->BuildFromRoute(6000.0, 2200.0, StepReason);
    }

    ALBOneFactoryDevStationDressingActor* Dressing = nullptr;
    for (TActorIterator<ALBOneFactoryDevStationDressingActor> It(World); It;
        ++It)
    {
        if (IsValid(*It)) { Dressing = *It; break; }
    }
    if (!Dressing)
    {
        Dressing = World->SpawnActor<ALBOneFactoryDevStationDressingActor>(
            ALBOneFactoryDevStationDressingActor::StaticClass(),
            FVector::ZeroVector, FRotator::ZeroRotator, Params);
    }
    if (Dressing)
    {
        const bool bDressed = Dressing->BuildFromRoute(StepReason);
        UE_LOG(LogLineBossOneFactoryPlayer, Display,
            TEXT("LINE_BOSS_PLAYER_DRESSING ok=%d %s"), bDressed ? 1 : 0,
            *StepReason);
    }

    ALBOneFactoryDevRestoredShopActor* Shop = nullptr;
    for (TActorIterator<ALBOneFactoryDevRestoredShopActor> It(World); It; ++It)
    {
        if (IsValid(*It)) { Shop = *It; break; }
    }
    if (!Shop)
    {
        Shop = World->SpawnActor<ALBOneFactoryDevRestoredShopActor>(
            ALBOneFactoryDevRestoredShopActor::StaticClass(),
            FVector::ZeroVector, FRotator::ZeroRotator, Params);
    }
    if (Shop)
    {
        Shop->BuildFromManifest(StepReason);
        UE_LOG(LogLineBossOneFactoryPlayer, Display,
            TEXT("LINE_BOSS_PLAYER_RESTORED_SHOP %s"), *StepReason);
    }

    ULBOneFactoryDevFactory::SetRoofHidden(this, true, 900.0, StepReason);

    // The detailed press train now stands at the ConfigurablePressTrain
    // station, so the 268-primitive press blockout must no longer render,
    // exactly as the detailed-press recovery design specifies. Visibility
    // only; LB.OneFactory.PressBlockout 1 restores it.
    for (TActorIterator<ALBOneFactoryPressStarterPresentationActor> It(World);
        It; ++It)
    {
        if (IsValid(*It))
        {
            It->SetActorHiddenInGame(true);
        }
    }
    ULBOneFactoryDevFactory::EnsureDevLighting(this, 9.0f, StepReason);

    bool bHasWip = false;
    for (TActorIterator<ALBOneFactoryWIPPresentationActor> It(World); It; ++It)
    {
        if (IsValid(*It)) { bHasWip = true; break; }
    }
    if (!bHasWip)
    {
        World->SpawnActor<ALBOneFactoryWIPPresentationActor>(
            ALBOneFactoryWIPPresentationActor::StaticClass(),
            FVector::ZeroVector, FRotator::ZeroRotator, Params);
    }

    // Frame onto the player's own pawn, not a dev camera. Passing true here
    // handed the view target to a transient ACameraActor that was never given
    // back, so from this point on every camera control moved an off-screen pawn
    // while the screen stayed frozen on one fixed shot for the whole session.
    ULBOneFactoryDevFactory::FrameProductionLine(this, TEXT("All"), StepReason,
        /*bDriveViewTarget=*/false);

    // Report who actually owns the view. This regressed silently once and cost a
    // great deal of confusion: the camera controls all worked, so nothing looked
    // broken except the screen. viewIsPawn=1 is the contract.
    const AActor* ViewTarget = GetViewTarget();
    UE_LOG(LogLineBossOneFactoryPlayer, Display,
        TEXT("LINE_BOSS_PLAYER_VIEW viewIsPawn=%d viewTarget=%s pawn=%s %s"),
        (ViewTarget && ViewTarget == GetPawn()) ? 1 : 0,
        ViewTarget ? *ViewTarget->GetName() : TEXT("<none>"),
        GetPawn() ? *GetPawn()->GetName() : TEXT("<none>"),
        *StepReason);
}

void ALBOneFactoryPlayerController::PlaceOrder()
{
    FString Reason;
    const bool bOk =
        ULBOneFactoryDevFactory::StartDemoProduction(this, 1, Reason);
    UE_LOG(LogLineBossOneFactoryPlayer, Display,
        TEXT("LINE_BOSS_PLAYER_ORDER ok=%d %s"), bOk ? 1 : 0, *Reason);
}

void ALBOneFactoryPlayerController::ApplyTimeScale(const float TimeScale)
{
    // Routed through the operations subsystem, not the coordinator directly:
    // rate 0 must become the ledger's durable bLinePaused, and the
    // coordinator's SetRuntimeTimeScale clamp ([0.25, 4.0]) rejects 0, which
    // is how the pause key shipped dead.
    UWorld* World = GetWorld();
    ULBOneFactoryOperationsSubsystem* Operations =
        World ? World->GetSubsystem<ULBOneFactoryOperationsSubsystem>()
              : nullptr;
    if (!Operations)
    {
        return;
    }
    FString Reason;
    if (Operations->SetSimulationRate(TimeScale, Reason))
    {
        if (TimeScale > KINDA_SMALL_NUMBER)
        {
            LastRunningTimeScale = TimeScale;
        }
        UE_LOG(LogLineBossOneFactoryPlayer, Display,
            TEXT("LINE_BOSS_PLAYER_SPEED %.2fx %s"), TimeScale, *Reason);
    }
    else
    {
        UE_LOG(LogLineBossOneFactoryPlayer, Warning,
            TEXT("LINE_BOSS_PLAYER_SPEED rejected %.2f: %s"), TimeScale,
            *Reason);
    }
}

void ALBOneFactoryPlayerController::TogglePause()
{
    using namespace LBOneFactoryPlayerPrivate;

    ALBOneFactoryProductionFlowAuthority* Production =
        FindProduction(GetWorld());
    if (!Production)
    {
        return;
    }
    // Pause state lives on the ledger, not in the time scale: the scale
    // never goes below 0.25, so reading it always claimed "running".
    const bool bPaused = Production->CaptureLedger().bLinePaused;
    ApplyTimeScale(bPaused ? LastRunningTimeScale : 0.0f);
}

void ALBOneFactoryPlayerController::SetSpeedNormal() { ApplyTimeScale(1.0f); }
void ALBOneFactoryPlayerController::SetSpeedFast() { ApplyTimeScale(2.0f); }
void ALBOneFactoryPlayerController::SetSpeedVeryFast() { ApplyTimeScale(4.0f); }

bool ALBOneFactoryPlayerController::ResolveOldestHold(FName& OutUnitId,
    FString& OutReason) const
{
    using namespace LBOneFactoryPlayerPrivate;

    ALBOneFactoryRuntimeCoordinator* Coordinator = FindCoordinator(GetWorld());
    ALBOneFactoryProductionFlowAuthority* Production =
        FindProduction(GetWorld());
    if (!Coordinator || !Production)
    {
        OutReason = TEXT("no commissioned factory yet");
        return false;
    }

    // Ledger order is creation order, so the first match is the oldest car
    // waiting - which is the one a line manager would clear first.
    const FLBOneFactoryProductionLedgerState Ledger = Production->CaptureLedger();
    for (const FLBOneFactoryVehicleUnitState& Unit : Ledger.Units)
    {
        if (Unit.bDispatched)
        {
            continue;
        }
        FLBOneFactoryRuntimeVehicleStatus Status;
        FString StatusReason;
        if (Coordinator->GetVehicleRuntimeStatus(Unit.UnitId, Status,
                StatusReason)
            && Status.bAwaitingQualityResult)
        {
            OutUnitId = Unit.UnitId;
            return true;
        }
    }
    OutReason = TEXT("nothing is waiting on a quality result");
    return false;
}

void ALBOneFactoryPlayerController::PassOldestQualityHold()
{
    using namespace LBOneFactoryPlayerPrivate;

    FName UnitId = NAME_None;
    FString Reason;
    if (!ResolveOldestHold(UnitId, Reason))
    {
        UE_LOG(LogLineBossOneFactoryPlayer, Display,
            TEXT("LINE_BOSS_PLAYER_QUALITY %s"), *Reason);
        return;
    }
    ALBOneFactoryRuntimeCoordinator* Coordinator = FindCoordinator(GetWorld());
    const FName EvidenceId(*FString::Printf(TEXT("PLAYER_QA_%s_%d"),
        *UnitId.ToString(), ++QualityEvidenceCounter));
    const bool bOk = Coordinator && Coordinator->SubmitRuntimeQualityResult(
        UnitId, ELBOneFactoryVehicleQualityState::Passed, EvidenceId, Reason);
    UE_LOG(LogLineBossOneFactoryPlayer, Display,
        TEXT("LINE_BOSS_PLAYER_QUALITY_PASS ok=%d unit=%s %s"),
        bOk ? 1 : 0, *UnitId.ToString(), *Reason);
}

void ALBOneFactoryPlayerController::ReworkOldestQualityHold()
{
    using namespace LBOneFactoryPlayerPrivate;

    FName UnitId = NAME_None;
    FString Reason;
    if (!ResolveOldestHold(UnitId, Reason))
    {
        UE_LOG(LogLineBossOneFactoryPlayer, Display,
            TEXT("LINE_BOSS_PLAYER_QUALITY %s"), *Reason);
        return;
    }
    ALBOneFactoryRuntimeCoordinator* Coordinator = FindCoordinator(GetWorld());
    const FName EvidenceId(*FString::Printf(TEXT("PLAYER_REWORK_%s_%d"),
        *UnitId.ToString(), ++QualityEvidenceCounter));
    // Rework repeats the same inspection cycle without creating another unit.
    const bool bOk = Coordinator
        && Coordinator->CompleteRuntimeRework(UnitId, EvidenceId, Reason);
    UE_LOG(LogLineBossOneFactoryPlayer, Display,
        TEXT("LINE_BOSS_PLAYER_REWORK ok=%d unit=%s %s"),
        bOk ? 1 : 0, *UnitId.ToString(), *Reason);
}

void ALBOneFactoryPlayerController::SaveFactory()
{
    ULBOneFactorySaveSubsystem* Saves =
        GetWorld() ? GetWorld()->GetSubsystem<ULBOneFactorySaveSubsystem>()
                   : nullptr;
    if (!Saves)
    {
        UE_LOG(LogLineBossOneFactoryPlayer, Warning,
            TEXT("LINE_BOSS_PLAYER_SAVE no save subsystem"));
        return;
    }
    FString Reason;
    const bool bOk = Saves->SaveOneFactory(Reason);
    UE_LOG(LogLineBossOneFactoryPlayer, Display,
        TEXT("LINE_BOSS_PLAYER_SAVE ok=%d %s"), bOk ? 1 : 0, *Reason);
}

void ALBOneFactoryPlayerController::LoadFactory()
{
    ULBOneFactorySaveSubsystem* Saves =
        GetWorld() ? GetWorld()->GetSubsystem<ULBOneFactorySaveSubsystem>()
                   : nullptr;
    if (!Saves)
    {
        UE_LOG(LogLineBossOneFactoryPlayer, Warning,
            TEXT("LINE_BOSS_PLAYER_LOAD no save subsystem"));
        return;
    }
    FString Reason;
    const bool bOk = Saves->LoadOneFactory(Reason);
    UE_LOG(LogLineBossOneFactoryPlayer, Display,
        TEXT("LINE_BOSS_PLAYER_LOAD ok=%d %s"), bOk ? 1 : 0, *Reason);
    if (bOk)
    {
        // A restored factory arrives without its site presentation - the
        // save carries production state, not scenery - so bring the
        // envelope, dressing, restored shop, lighting and WIP view up
        // around the loaded line.
        EnsureSitePresentation();
    }
}
