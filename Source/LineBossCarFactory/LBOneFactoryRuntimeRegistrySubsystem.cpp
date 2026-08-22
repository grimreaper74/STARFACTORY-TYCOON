#include "LBOneFactoryRuntimeRegistrySubsystem.h"

#include "GameFramework/Actor.h"
#include "EngineUtils.h"
#include "LBOneFactoryProductionFlow.h"
#include "LBOneFactoryRuntimeCoordinator.h"

namespace LBOneFactoryRuntimeRegistryPrivate
{
template<typename ActorType>
bool FindExactlyOne(UWorld* World, const TCHAR* Label, ActorType*& OutActor,
    FString& OutReason)
{
    OutActor = nullptr;
    int32 Count = 0;
    if (World)
    {
        for (TActorIterator<ActorType> It(World); It; ++It)
        {
            ActorType* Candidate = *It;
            if (!IsValid(Candidate) || Candidate->IsActorBeingDestroyed())
            {
                continue;
            }
            OutActor = Candidate;
            ++Count;
        }
    }
    if (Count != 1)
    {
        OutActor = nullptr;
        OutReason = FString::Printf(
            TEXT("ONEFACTORY RUNTIME REGISTRY REQUIRES EXACTLY ONE %s; FOUND %d"),
            Label, Count);
        return false;
    }
    return true;
}
}

void ULBOneFactoryRuntimeRegistrySubsystem::Initialize(
    FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    if (UWorld* World = GetWorld())
    {
        ActorSpawnedHandle = World->AddOnActorSpawnedHandler(
            FOnActorSpawned::FDelegate::CreateUObject(this,
                &ULBOneFactoryRuntimeRegistrySubsystem::HandleActorSpawned));
    }
}

void ULBOneFactoryRuntimeRegistrySubsystem::Deinitialize()
{
    if (ActorSpawnedHandle.IsValid())
    {
        if (UWorld* World = GetWorld())
        {
            World->RemoveOnActorSpawnedHandler(ActorSpawnedHandle);
        }
        ActorSpawnedHandle.Reset();
    }
    ProductionAuthority = nullptr;
    RuntimeCoordinator = nullptr;
    Super::Deinitialize();
}

void ULBOneFactoryRuntimeRegistrySubsystem::HandleActorSpawned(
    AActor* SpawnedActor)
{
    if (Cast<ALBOneFactoryProductionFlowAuthority>(SpawnedActor)
        || Cast<ALBOneFactoryRuntimeCoordinator>(SpawnedActor))
    {
        ProductionAuthority = nullptr;
        RuntimeCoordinator = nullptr;
    }
}

bool ULBOneFactoryRuntimeRegistrySubsystem::RefreshRuntimeBackbone(
    FString& OutReason)
{
    using namespace LBOneFactoryRuntimeRegistryPrivate;

    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    if (!FindExactlyOne(GetWorld(), TEXT("PRODUCTION FLOW AUTHORITY"),
            Production, OutReason)
        || !FindExactlyOne(GetWorld(), TEXT("RUNTIME COORDINATOR"),
            Coordinator, OutReason))
    {
        ProductionAuthority = nullptr;
        RuntimeCoordinator = nullptr;
        return false;
    }
    if (!Production->ActorHasTag(
            ALBOneFactoryProductionFlowAuthority::GetAuthorityTag())
        || !Coordinator->ActorHasTag(
            ALBOneFactoryRuntimeCoordinator::GetCoordinatorTag()))
    {
        ProductionAuthority = nullptr;
        RuntimeCoordinator = nullptr;
        OutReason = TEXT("ONEFACTORY RUNTIME REGISTRY BACKBONE TAG CONTRACT FAILED");
        return false;
    }
    ProductionAuthority = Production;
    RuntimeCoordinator = Coordinator;
    return true;
}

bool ULBOneFactoryRuntimeRegistrySubsystem::ResolveRuntimeBackbone(
    ALBOneFactoryProductionFlowAuthority*& OutProduction,
    ALBOneFactoryRuntimeCoordinator*& OutCoordinator, FString& OutReason)
{
    OutProduction = nullptr;
    OutCoordinator = nullptr;
    OutReason.Reset();
    if (!IsValid(ProductionAuthority) || !IsValid(RuntimeCoordinator))
    {
        if (!RefreshRuntimeBackbone(OutReason))
        {
            return false;
        }
    }
    OutProduction = ProductionAuthority;
    OutCoordinator = RuntimeCoordinator;
    return true;
}

ALBOneFactoryProductionFlowAuthority*
ULBOneFactoryRuntimeRegistrySubsystem::GetProductionAuthority() const
{
    return IsValid(ProductionAuthority) ? ProductionAuthority.Get() : nullptr;
}

ALBOneFactoryRuntimeCoordinator*
ULBOneFactoryRuntimeRegistrySubsystem::GetRuntimeCoordinator() const
{
    return IsValid(RuntimeCoordinator) ? RuntimeCoordinator.Get() : nullptr;
}
