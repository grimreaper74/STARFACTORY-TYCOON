#include "LBOneFactoryPlayerController.h"

#include "Components/InputComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBOneFactoryDevEnvelopeActor.h"
#include "LBOneFactoryDevFactoryCommands.h"
#include "LBOneFactoryDevStationDressingActor.h"
#include "LBOneFactoryPressStarterPresentationActor.h"
#include "LBOneFactoryProductionFlow.h"
#include "LBOneFactoryRuntimeCoordinator.h"
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
}

void ALBOneFactoryPlayerController::CommissionFactory()
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    FString Reason;
    if (!ULBOneFactoryDevFactory::BuildAndCommissionWholeFactory(this, Reason))
    {
        UE_LOG(LogLineBossOneFactoryPlayer, Warning,
            TEXT("LINE_BOSS_PLAYER_COMMISSION failed: %s"), *Reason);
        return;
    }
    UE_LOG(LogLineBossOneFactoryPlayer, Display,
        TEXT("LINE_BOSS_PLAYER_COMMISSION %s"), *Reason);

    FActorSpawnParameters Params;
    Params.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

    // Bring the site up with the factory: enclosure, machinery, lighting and
    // the work-in-progress view. Without these the commissioned factory is
    // technically running but unreadable.
    FString StepReason;
    if (ALBOneFactoryDevEnvelopeActor* Envelope =
        World->SpawnActor<ALBOneFactoryDevEnvelopeActor>(
            ALBOneFactoryDevEnvelopeActor::StaticClass(),
            FVector::ZeroVector, FRotator::ZeroRotator, Params))
    {
        Envelope->BuildFromRoute(6000.0, 1400.0, StepReason);
    }
    if (ALBOneFactoryDevStationDressingActor* Dressing =
        World->SpawnActor<ALBOneFactoryDevStationDressingActor>(
            ALBOneFactoryDevStationDressingActor::StaticClass(),
            FVector::ZeroVector, FRotator::ZeroRotator, Params))
    {
        const bool bDressed = Dressing->BuildFromRoute(StepReason);
        UE_LOG(LogLineBossOneFactoryPlayer, Display,
            TEXT("LINE_BOSS_PLAYER_DRESSING ok=%d %s"), bDressed ? 1 : 0,
            *StepReason);
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

    ULBOneFactoryDevFactory::FrameProductionLine(this, TEXT("All"), StepReason);
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
    using namespace LBOneFactoryPlayerPrivate;

    ALBOneFactoryRuntimeCoordinator* Coordinator = FindCoordinator(GetWorld());
    if (!Coordinator)
    {
        return;
    }
    FString Reason;
    if (Coordinator->SetRuntimeTimeScale(TimeScale, Reason))
    {
        if (TimeScale > KINDA_SMALL_NUMBER)
        {
            LastRunningTimeScale = TimeScale;
        }
        UE_LOG(LogLineBossOneFactoryPlayer, Display,
            TEXT("LINE_BOSS_PLAYER_SPEED %.2fx"), TimeScale);
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

    ALBOneFactoryRuntimeCoordinator* Coordinator = FindCoordinator(GetWorld());
    if (!Coordinator)
    {
        return;
    }
    const bool bRunning =
        Coordinator->GetRuntimeTimeScale() > KINDA_SMALL_NUMBER;
    ApplyTimeScale(bRunning ? 0.0f : LastRunningTimeScale);
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
