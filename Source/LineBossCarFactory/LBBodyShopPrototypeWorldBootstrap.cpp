#include "LBBodyShopPrototypeWorldBootstrap.h"

#include "EngineUtils.h"
#include "Engine/World.h"
#include "GameFramework/GameModeBase.h"
#include "LBBodyShopBuildAuthority.h"
#include "LBBodyShopPrototypeGameMode.h"
#include "LBBodyShopPrototypeRuntime.h"

ALBBodyShopPrototypeWorldBootstrap::ALBBodyShopPrototypeWorldBootstrap()
{
    PrimaryActorTick.bCanEverTick = false;
    SetActorEnableCollision(false);
    SetReplicates(false);
}

void ALBBodyShopPrototypeWorldBootstrap::BeginPlay()
{
    Super::BeginPlay();
    // The isolated GameMode owns the one startup call. Keeping this actor's
    // BeginPlay observational prevents a map bootstrap from ever creating
    // production authorities under a different GameMode.
    RefreshBootstrapState();
}

void ALBBodyShopPrototypeWorldBootstrap::RefreshBootstrapState()
{
    FString Reason;
    bBootstrapConfigurationValid = ValidateBootstrapFlags(bPrototypeEnabled,
        bRejectLegacyAuthorities, bUseExperimentalSaveOnly,
        bRequirePrototypeGameMode, PrototypeGridSizeCm, Reason);
    if (!bBootstrapConfigurationValid)
    {
        bDetectedLegacyAuthority = false;
        bWorldIsolationValid = false;
        BootstrapState = ELBBodyShopPrototypeBootstrapState::Incompatible;
        BootstrapStatusText = Reason;
        return;
    }

    bDetectedLegacyAuthority = false;
    bWorldIsolationValid = ValidateWorldIsolation(Reason);
    if (!bWorldIsolationValid)
    {
        BootstrapState = ELBBodyShopPrototypeBootstrapState::Incompatible;
        BootstrapStatusText = Reason;
        return;
    }

    if (RuntimeWiringStage == ELBBodyShopPrototypeRuntimeWiringStage::Failed)
    {
        BootstrapState = ELBBodyShopPrototypeBootstrapState::Incompatible;
        if (BootstrapStatusText.IsEmpty())
        {
            BootstrapStatusText = TEXT("BODY SHOP PROTOTYPE RUNTIME WIRING FAILED");
        }
        return;
    }

    BootstrapState = ArePrototypeAuthoritiesBound()
        ? ELBBodyShopPrototypeBootstrapState::Ready
        : ELBBodyShopPrototypeBootstrapState::WaitingForRuntime;
    if (ArePrototypeAuthoritiesBound())
    {
        BootstrapStatusText = bInitialUnderbodySliceCommissioned
            ? TEXT("BODY SHOP PROTOTYPE UNDERBODY SLICE COMMISSIONED")
            : TEXT("BODY SHOP PROTOTYPE AUTHORITIES BOUND; WAITING FOR SLICE COMMISSIONING");
    }
    else
    {
        BootstrapStatusText = TEXT("BODY SHOP PROTOTYPE ISOLATED; WAITING FOR MODULE AUTHORITIES");
    }
}

bool ALBBodyShopPrototypeWorldBootstrap::BindPrototypeAuthorities(
    AActor* InBuildAuthority, AActor* InRuntime, FString& OutReason)
{
    OutReason.Reset();
    if (!IsValid(InBuildAuthority) || !IsValid(InRuntime))
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE REQUIRES BOTH BUILD AND RUNTIME AUTHORITIES");
        return false;
    }
    if (InBuildAuthority == InRuntime)
    {
        OutReason = TEXT("BODY SHOP BUILD AND RUNTIME AUTHORITIES MUST BE DISTINCT");
        return false;
    }
    if (IsForbiddenLegacyAuthorityClassName(InBuildAuthority->GetClass()->GetName())
        || IsForbiddenLegacyAuthorityClassName(InRuntime->GetClass()->GetName()))
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE CANNOT BIND A LEGACY AUTHORITY");
        return false;
    }

    BuildAuthorityActor = InBuildAuthority;
    RuntimeActor = InRuntime;
    RefreshBootstrapState();
    if (!bBootstrapConfigurationValid || !bWorldIsolationValid)
    {
        OutReason = BootstrapStatusText;
        BuildAuthorityActor = nullptr;
        RuntimeActor = nullptr;
        RefreshBootstrapState();
        return false;
    }
    OutReason = BootstrapStatusText;
    return true;
}

bool ALBBodyShopPrototypeWorldBootstrap::InitialiseRuntimeAuthorities(FString& OutReason)
{
    OutReason.Reset();
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE WORLD IS UNAVAILABLE FOR RUNTIME WIRING");
        RuntimeWiringStage = ELBBodyShopPrototypeRuntimeWiringStage::Failed;
        BootstrapStatusText = OutReason;
        return false;
    }
    if (World->GetNetMode() == NM_Client)
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE AUTHORITIES ARE SERVER-ONLY");
        return false;
    }

    TArray<ALBBodyShopBuildAuthority*> ExistingBuildAuthorities;
    TArray<ALBBodyShopPrototypeRuntime*> ExistingRuntimes;
    for (TActorIterator<ALBBodyShopBuildAuthority> It(World); It; ++It)
    {
        if (IsValid(*It) && !It->IsActorBeingDestroyed())
        {
            ExistingBuildAuthorities.Add(*It);
        }
    }
    for (TActorIterator<ALBBodyShopPrototypeRuntime> It(World); It; ++It)
    {
        if (IsValid(*It) && !It->IsActorBeingDestroyed())
        {
            ExistingRuntimes.Add(*It);
        }
    }

    // A repeated startup callback must observe the exact authorities it made;
    // it must never manufacture a duplicate runtime or duplicate cells.
    if (bRuntimeInitialisationAttempted)
    {
        const bool bExactExistingPair = ExistingBuildAuthorities.Num() == 1
            && ExistingRuntimes.Num() == 1
            && BuildAuthorityActor.Get() == ExistingBuildAuthorities[0]
            && RuntimeActor.Get() == ExistingRuntimes[0]
            && ExistingRuntimes[0]->GetBuildAuthority() == ExistingBuildAuthorities[0]
            && ArePrototypeAuthoritiesBound();
        if (bExactExistingPair && bInitialUnderbodySliceCommissioned)
        {
            OutReason = BootstrapStatusText;
            return true;
        }

        OutReason = TEXT("BODY SHOP PROTOTYPE RUNTIME WIRING WAS ALREADY ATTEMPTED");
        RuntimeWiringStage = ELBBodyShopPrototypeRuntimeWiringStage::Failed;
        BootstrapStatusText = OutReason;
        return false;
    }

    if (!bBootstrapConfigurationValid || !bWorldIsolationValid)
    {
        RefreshBootstrapState();
        OutReason = BootstrapStatusText;
        RuntimeWiringStage = ELBBodyShopPrototypeRuntimeWiringStage::Failed;
        return false;
    }
    if (!ValidateRuntimeSpawnPreconditions(bSpawnRuntimeOnBeginPlay,
            bRequestInitialUnderbodySlice, ExistingBuildAuthorities.Num(),
            ExistingRuntimes.Num(), OutReason))
    {
        RuntimeWiringStage = ELBBodyShopPrototypeRuntimeWiringStage::Failed;
        BootstrapStatusText = OutReason;
        return false;
    }

    bRuntimeInitialisationAttempted = true;
    bInitialUnderbodySliceCommissioned = false;
    RuntimeWiringStage = ELBBodyShopPrototypeRuntimeWiringStage::NotStarted;

    FActorSpawnParameters SpawnParameters;
    SpawnParameters.Owner = this;
    SpawnParameters.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    ALBBodyShopBuildAuthority* NewBuildAuthority = World->SpawnActor<ALBBodyShopBuildAuthority>(
        ALBBodyShopBuildAuthority::StaticClass(), FTransform::Identity, SpawnParameters);
    ALBBodyShopPrototypeRuntime* NewRuntime = World->SpawnActor<ALBBodyShopPrototypeRuntime>(
        ALBBodyShopPrototypeRuntime::StaticClass(), FTransform::Identity, SpawnParameters);
    if (!NewBuildAuthority || !NewRuntime)
    {
        if (NewRuntime) NewRuntime->Destroy();
        if (NewBuildAuthority) NewBuildAuthority->Destroy();
        OutReason = TEXT("BODY SHOP PROTOTYPE COULD NOT SPAWN ITS RUNTIME AUTHORITIES");
        RuntimeWiringStage = ELBBodyShopPrototypeRuntimeWiringStage::Failed;
        BootstrapStatusText = OutReason;
        return false;
    }

    // This ordering is intentionally explicit: do not bind the bootstrap or
    // construct any player-owned cell before the runtime knows its authority.
    if (!NewRuntime->BindBuildAuthority(NewBuildAuthority, OutReason))
    {
        NewRuntime->Destroy();
        NewBuildAuthority->Destroy();
        RuntimeWiringStage = ELBBodyShopPrototypeRuntimeWiringStage::Failed;
        BootstrapStatusText = OutReason;
        return false;
    }
    RuntimeWiringStage = ELBBodyShopPrototypeRuntimeWiringStage::RuntimeBoundToBuildAuthority;

    if (!BindPrototypeAuthorities(NewBuildAuthority, NewRuntime, OutReason))
    {
        NewRuntime->Destroy();
        NewBuildAuthority->Destroy();
        RuntimeWiringStage = ELBBodyShopPrototypeRuntimeWiringStage::Failed;
        BootstrapStatusText = OutReason;
        return false;
    }
    RuntimeWiringStage = ELBBodyShopPrototypeRuntimeWiringStage::AuthoritiesBoundToBootstrap;

    if (!NewRuntime->BuildAndCommissionApprovedUnderbodySlice(OutReason))
    {
        RuntimeWiringStage = ELBBodyShopPrototypeRuntimeWiringStage::Failed;
        BootstrapStatusText = OutReason;
        return false;
    }

    bInitialUnderbodySliceCommissioned = true;
    RuntimeWiringStage = ELBBodyShopPrototypeRuntimeWiringStage::UnderbodySliceCommissioned;
    BootstrapState = ELBBodyShopPrototypeBootstrapState::Ready;
    BootstrapStatusText = TEXT("BODY SHOP PROTOTYPE UNDERBODY SLICE COMMISSIONED");
    OutReason = BootstrapStatusText;
    return true;
}

bool ALBBodyShopPrototypeWorldBootstrap::ValidateBootstrapFlags(
    const bool bInPrototypeEnabled, const bool bInRejectLegacyAuthorities,
    const bool bInExperimentalSaveOnly, const bool bInRequirePrototypeGameMode,
    const float InGridSizeCm, FString& OutReason)
{
    OutReason.Reset();
    if (!bInPrototypeEnabled)
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE MAP OPT-IN IS DISABLED");
        return false;
    }
    if (!bInRejectLegacyAuthorities)
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE MUST REJECT LEGACY FACTORY AUTHORITIES");
        return false;
    }
    if (!bInExperimentalSaveOnly)
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE MUST USE EXPERIMENTAL SAVE V1 ONLY");
        return false;
    }
    if (!bInRequirePrototypeGameMode)
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE MUST REQUIRE ITS ISOLATED GAME MODE");
        return false;
    }
    if (!FMath::IsFinite(InGridSizeCm)
        || !FMath::IsNearlyEqual(InGridSizeCm, 100.0f, 0.01f))
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE REQUIRES 100 CM GRID SNAP");
        return false;
    }
    OutReason = TEXT("BODY SHOP PROTOTYPE FLAGS VALID");
    return true;
}

bool ALBBodyShopPrototypeWorldBootstrap::ValidateRuntimeSpawnPreconditions(
    const bool bInSpawnRuntimeOnBeginPlay, const bool bInRequestInitialUnderbodySlice,
    const int32 ExistingBuildAuthorityCount, const int32 ExistingRuntimeCount,
    FString& OutReason)
{
    OutReason.Reset();
    if (!bInSpawnRuntimeOnBeginPlay)
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE MUST SPAWN RUNTIME AUTHORITIES FROM BEGIN PLAY");
        return false;
    }
    if (!bInRequestInitialUnderbodySlice)
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE MUST REQUEST THE APPROVED UNDERBODY SLICE");
        return false;
    }
    if (ExistingBuildAuthorityCount != 0 || ExistingRuntimeCount != 0)
    {
        OutReason = FString::Printf(
            TEXT("BODY SHOP PROTOTYPE MAP MUST NOT BAKE RUNTIME AUTHORITIES (build=%d runtime=%d)"),
            ExistingBuildAuthorityCount, ExistingRuntimeCount);
        return false;
    }
    OutReason = TEXT("BODY SHOP PROTOTYPE RUNTIME SPAWN PREFLIGHT VALID");
    return true;
}

bool ALBBodyShopPrototypeWorldBootstrap::IsForbiddenLegacyAuthorityClassName(
    const FString& ClassName)
{
    static const TCHAR* ForbiddenFragments[] = {
        TEXT("LBGameMode"),
        TEXT("LBPressShopCampaignController"),
        TEXT("LBPressShopBuildAuthority"),
        TEXT("LBPlayerBuiltPressFlowController"),
        TEXT("LBBodyWeldLineActor"),
        TEXT("LBECoatLineActor"),
        TEXT("LBFactoryMachineBuilderSubsystem")
    };
    for (const TCHAR* Fragment : ForbiddenFragments)
    {
        if (ClassName.Contains(Fragment, ESearchCase::IgnoreCase)) return true;
    }
    return false;
}

bool ALBBodyShopPrototypeWorldBootstrap::ValidateWorldIsolation(FString& OutReason)
{
    OutReason.Reset();
    bDetectedLegacyAuthority = false;
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE WORLD IS UNAVAILABLE");
        return false;
    }

    // Clients do not own a GameMode. Their map validity remains governed by the
    // replicated/server bootstrap rather than failing because GetAuthGameMode is null.
    if (bRequirePrototypeGameMode && World->GetNetMode() != NM_Client)
    {
        const AGameModeBase* ActiveGameMode = World->GetAuthGameMode();
        if (!ActiveGameMode || !ActiveGameMode->IsA(ALBBodyShopPrototypeGameMode::StaticClass()))
        {
            OutReason = TEXT("BODY SHOP PROTOTYPE MAP IS NOT USING ALBBodyShopPrototypeGameMode");
            return false;
        }
    }

    if (bRejectLegacyAuthorities)
    {
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            if (!IsValid(*It) || *It == this) continue;
            if (IsForbiddenLegacyAuthorityClassName(It->GetClass()->GetName()))
            {
                bDetectedLegacyAuthority = true;
                OutReason = FString::Printf(
                    TEXT("BODY SHOP PROTOTYPE FOUND LEGACY AUTHORITY %s"),
                    *It->GetClass()->GetName());
                return false;
            }
        }
    }

    OutReason = TEXT("BODY SHOP PROTOTYPE MAP IS ISOLATED");
    return true;
}
