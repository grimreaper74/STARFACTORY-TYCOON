#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "LBOneFactoryBootstrap.h"
#include "LBOneFactoryGameMode.generated.h"

class ALBOneFactoryBootstrap;
class ALBOneFactoryPlayerController;
class ALBOneFactoryProductionFlowAuthority;
class ALBOneFactoryRuntimeCoordinator;

/**
 * Local map override for Moorcross Works.
 *
 * This intentionally derives directly from AGameModeBase. It reuses the proven
 * management pawn and UMG ControlRoom HUD, but none of ALBGameMode's legacy
 * envelope, inbound, Coil AGV, support-fleet or presentation bootstrap.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBOneFactoryGameMode : public AGameModeBase
{
    GENERATED_BODY()

public:
    ALBOneFactoryGameMode();
    virtual void BeginPlay() override;
    virtual void PostLogin(APlayerController* NewPlayer) override;

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory")
    bool HasValidOneFactoryShell() const { return bOneFactoryShellValid; }

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory")
    FString GetOneFactoryStartupStatus() const { return OneFactoryStartupStatus; }

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory")
    ALBOneFactoryBootstrap* GetOneFactoryBootstrap() const
    {
        return OneFactoryBootstrap.Get();
    }

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory")
    bool HasValidRuntimeBackbone() const
    {
        return OneFactoryProductionFlow.IsValid()
            && OneFactoryRuntimeCoordinator.IsValid();
    }

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory")
    ALBOneFactoryProductionFlowAuthority* GetOneFactoryProductionFlow() const
    { return OneFactoryProductionFlow.Get(); }

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory")
    ALBOneFactoryRuntimeCoordinator* GetOneFactoryRuntimeCoordinator() const
    { return OneFactoryRuntimeCoordinator.Get(); }

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory")
    static FString GetFactoryDisplayName() { return TEXT("Moorcross Works"); }

    /** Explicit source/test seam: this mode owns no legacy spawn path. */
    static constexpr bool SpawnsLegacyFactoryContent() { return false; }

    /** Station construction remains a later player/runtime milestone. */
    static constexpr bool SeedsProductionStations() { return false; }

    static FName GetGameModeAuthorityTag();

    /** Pure startup contract shared with focused automation. */
    static bool ValidateBootstrapContract(int32 BootstrapCount,
        ELBOneFactoryBootstrapState BootstrapState, bool bBootstrapValidated,
        bool bLegacyContentWouldSpawn, bool bStationsWouldSeed,
        FString& OutReason);

private:
    bool EnsureRuntimeBackbone(FString& OutReason);
    void ActivatePrebuiltFactory(ALBOneFactoryPlayerController* Controller);

    UPROPERTY(Transient)
    TWeakObjectPtr<ALBOneFactoryBootstrap> OneFactoryBootstrap;

    UPROPERTY(Transient)
    TWeakObjectPtr<ALBOneFactoryProductionFlowAuthority>
        OneFactoryProductionFlow;

    UPROPERTY(Transient)
    TWeakObjectPtr<ALBOneFactoryRuntimeCoordinator>
        OneFactoryRuntimeCoordinator;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|OneFactory")
    bool bOneFactoryShellValid = false;

    /** Prevent duplicate construction if BeginPlay and PostLogin overlap. */
    bool bPrebuiltFactoryActivated = false;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|OneFactory")
    FString OneFactoryStartupStatus = TEXT("ONEFACTORY STARTUP NOT YET VALIDATED");
};
