#include "LBOneFactoryGameMode.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBControlRoomHUD.h"
#include "LBManagementPawn.h"
#include "LBOneFactoryBootstrap.h"
#include "LBOneFactoryProductionFlow.h"
#include "LBOneFactoryRuntimeCoordinator.h"

DEFINE_LOG_CATEGORY_STATIC(LogLineBossOneFactoryGameMode, Log, All);

namespace LBOneFactoryGameModePrivate
{
    template<typename ActorType>
    bool ResolveOrSpawnExact(UWorld& World, const FName SpawnName,
        const TCHAR* Label, ActorType*& OutActor, bool& bOutSpawned,
        FString& OutReason)
    {
        OutActor = nullptr;
        bOutSpawned = false;
        int32 Count = 0;
        for (TActorIterator<ActorType> It(&World); It; ++It)
        {
            ActorType* Candidate = *It;
            if (!IsValid(Candidate) || Candidate->IsActorBeingDestroyed())
                continue;
            ++Count;
            OutActor = Candidate;
        }
        if (Count > 1 || (Count == 1
            && OutActor->GetClass() != ActorType::StaticClass()))
        {
            OutActor = nullptr;
            OutReason = FString::Printf(
                TEXT("ONEFACTORY RUNTIME BACKBONE REQUIRES ZERO OR ONE EXACT %s; FOUND %d"),
                Label, Count);
            return false;
        }
        if (OutActor) return true;

        FActorSpawnParameters Parameters;
        Parameters.Name = SpawnName;
        Parameters.SpawnCollisionHandlingOverride =
            ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        OutActor = World.SpawnActor<ActorType>(ActorType::StaticClass(),
            FTransform::Identity, Parameters);
        bOutSpawned = IsValid(OutActor) && !OutActor->IsActorBeingDestroyed();
        if (!bOutSpawned)
        {
            OutActor = nullptr;
            OutReason = FString::Printf(
                TEXT("ONEFACTORY RUNTIME BACKBONE COULD NOT CREATE %s"), Label);
            return false;
        }
        return true;
    }
}

FName ALBOneFactoryGameMode::GetGameModeAuthorityTag()
{
    static const FName Tag(TEXT("LB.OneFactory.GameMode.v001"));
    return Tag;
}

ALBOneFactoryGameMode::ALBOneFactoryGameMode()
{
    PrimaryActorTick.bCanEverTick = false;
    DefaultPawnClass = ALBManagementPawn::StaticClass();
    HUDClass = ALBControlRoomHUD::StaticClass();
    Tags.AddUnique(GetGameModeAuthorityTag());
}

bool ALBOneFactoryGameMode::ValidateBootstrapContract(
    const int32 BootstrapCount,
    const ELBOneFactoryBootstrapState BootstrapState,
    const bool bBootstrapValidated,
    const bool bLegacyContentWouldSpawn,
    const bool bStationsWouldSeed,
    FString& OutReason)
{
    OutReason.Reset();
    if (bLegacyContentWouldSpawn || bStationsWouldSeed)
    {
        OutReason = TEXT("ONEFACTORY GAME MODE MUST REMAIN SHELL-ONLY");
        return false;
    }
    if (BootstrapCount != 1)
    {
        OutReason = FString::Printf(TEXT("ONEFACTORY GAME MODE REQUIRES ONE BOOTSTRAP (FOUND %d)"),
            BootstrapCount);
        return false;
    }
    if (!bBootstrapValidated || BootstrapState != ELBOneFactoryBootstrapState::Ready)
    {
        OutReason = TEXT("ONEFACTORY BOOTSTRAP DID NOT REACH A VALID READY STATE");
        return false;
    }
    OutReason = TEXT("MOORCROSS WORKS ONEFACTORY PLAYER SHELL READY");
    return true;
}

void ALBOneFactoryGameMode::BeginPlay()
{
    Super::BeginPlay();
    bOneFactoryShellValid = false;
    OneFactoryBootstrap.Reset();
    OneFactoryProductionFlow.Reset();
    OneFactoryRuntimeCoordinator.Reset();

    UWorld* World = GetWorld();
    if (!World)
    {
        OneFactoryStartupStatus = TEXT("ONEFACTORY GAME MODE WORLD IS UNAVAILABLE");
        UE_LOG(LogLineBossOneFactoryGameMode, Error, TEXT("%s"),
            *OneFactoryStartupStatus);
        return;
    }

    TArray<ALBOneFactoryBootstrap*> Bootstraps;
    for (TActorIterator<ALBOneFactoryBootstrap> It(World); It; ++It)
    {
        if (IsValid(*It) && !It->IsActorBeingDestroyed()) Bootstraps.Add(*It);
    }

    FString BootstrapReason;
    bool bBootstrapValidated = false;
    ELBOneFactoryBootstrapState State = ELBOneFactoryBootstrapState::Rejected;
    if (Bootstraps.Num() == 1)
    {
        OneFactoryBootstrap = Bootstraps[0];
        bBootstrapValidated = Bootstraps[0]->ValidateAndLockShell(BootstrapReason);
        State = Bootstraps[0]->GetBootstrapState();
    }

    FString ContractReason;
    const bool bShellContractValid = ValidateBootstrapContract(
        Bootstraps.Num(), State,
        bBootstrapValidated, SpawnsLegacyFactoryContent(), SeedsProductionStations(),
        ContractReason);
    FString RuntimeReason;
    const bool bRuntimeBackboneValid = bShellContractValid
        && EnsureRuntimeBackbone(RuntimeReason);
    bOneFactoryShellValid = bShellContractValid && bRuntimeBackboneValid;
    OneFactoryStartupStatus = bOneFactoryShellValid
        ? ContractReason + TEXT(" | ") + RuntimeReason
        : !bShellContractValid
            ? (!BootstrapReason.IsEmpty() ? BootstrapReason : ContractReason)
            : RuntimeReason;
    if (bOneFactoryShellValid)
    {
        UE_LOG(LogLineBossOneFactoryGameMode, Display,
            TEXT("LINE_BOSS_ONEFACTORY_GAMEMODE valid=1 bootstrap_count=%d status=%s"),
            Bootstraps.Num(), *OneFactoryStartupStatus);
    }
    else
    {
        UE_LOG(LogLineBossOneFactoryGameMode, Error,
            TEXT("LINE_BOSS_ONEFACTORY_GAMEMODE valid=0 bootstrap_count=%d status=%s"),
            Bootstraps.Num(), *OneFactoryStartupStatus);
    }
}

bool ALBOneFactoryGameMode::EnsureRuntimeBackbone(FString& OutReason)
{
    using namespace LBOneFactoryGameModePrivate;
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("ONEFACTORY RUNTIME BACKBONE HAS NO WORLD");
        return false;
    }

    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    bool bProductionSpawned = false;
    bool bCoordinatorSpawned = false;
    if (!ResolveOrSpawnExact(*World,
            TEXT("LB_OneFactory_ProductionFlowAuthority_v001"),
            TEXT("PRODUCTION FLOW AUTHORITY"), Production,
            bProductionSpawned, OutReason)
        || !ResolveOrSpawnExact(*World,
            TEXT("LB_OneFactory_RuntimeCoordinator_v001"),
            TEXT("RUNTIME COORDINATOR"), Coordinator,
            bCoordinatorSpawned, OutReason)
        || !Production->ActorHasTag(
            ALBOneFactoryProductionFlowAuthority::GetAuthorityTag())
        || !Coordinator->ActorHasTag(
            ALBOneFactoryRuntimeCoordinator::GetCoordinatorTag()))
    {
        if (bCoordinatorSpawned && IsValid(Coordinator)) Coordinator->Destroy();
        if (bProductionSpawned && IsValid(Production)) Production->Destroy();
        if (OutReason.IsEmpty())
            OutReason = TEXT(
                "ONEFACTORY RUNTIME BACKBONE IDENTITY TAG CONTRACT FAILED");
        return false;
    }

    OneFactoryProductionFlow = Production;
    OneFactoryRuntimeCoordinator = Coordinator;
    OutReason = TEXT(
        "EXACTLY ONE PRODUCTION FLOW AUTHORITY AND ONE RUNTIME COORDINATOR READY");
    return true;
}
