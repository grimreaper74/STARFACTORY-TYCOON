#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "LBOneFactoryRuntimeRegistrySubsystem.generated.h"

class ALBOneFactoryProductionFlowAuthority;
class ALBOneFactoryRuntimeCoordinator;

/**
 * Read-only runtime-backbone registry for the live One Factory world.
 *
 * The factory simulation retains its exact-one authority contract.  Clients
 * query that contract here instead of independently iterating every actor in
 * the world whenever HUD, UI, player input or presentation needs it.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ULBOneFactoryRuntimeRegistrySubsystem final
    : public UWorldSubsystem
{
    GENERATED_BODY()

public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    bool ResolveRuntimeBackbone(ALBOneFactoryProductionFlowAuthority*& OutProduction,
        ALBOneFactoryRuntimeCoordinator*& OutCoordinator,
        FString& OutReason);

    ALBOneFactoryProductionFlowAuthority* GetProductionAuthority() const;
    ALBOneFactoryRuntimeCoordinator* GetRuntimeCoordinator() const;

private:
    bool RefreshRuntimeBackbone(FString& OutReason);
    void HandleActorSpawned(AActor* SpawnedActor);

    FDelegateHandle ActorSpawnedHandle;

    UPROPERTY(Transient)
    TObjectPtr<ALBOneFactoryProductionFlowAuthority> ProductionAuthority;

    UPROPERTY(Transient)
    TObjectPtr<ALBOneFactoryRuntimeCoordinator> RuntimeCoordinator;
};
