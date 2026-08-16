#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBOneFactoryTypes.h"
#include "LBOneFactoryBootstrap.generated.h"

class ALBPressShopBuildAuthority;
class UWorld;

UENUM(BlueprintType)
enum class ELBOneFactoryBootstrapState : uint8
{
    Unvalidated,
    Validating,
    Ready,
    Rejected
};

/**
 * Map-authored, shell-only authority for Moorcross Works.
 *
 * It validates one native hall, one peer ALBPressShopBuildAuthority and an empty
 * production floor. It never creates floors, machines, WIP, vehicles, support
 * fleets, shutters, lighting, QA fixtures or fallback presentation.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBOneFactoryBootstrap : public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryBootstrap();
    virtual void BeginPlay() override;

    /** Idempotent and fail-closed: the first result is retained for this actor lifetime. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Bootstrap")
    bool ValidateAndLockShell(FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Bootstrap")
    bool HasValidShell() const
    {
        return bValidationAttempted
            && BootstrapState == ELBOneFactoryBootstrapState::Ready;
    }

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Bootstrap")
    bool WasValidationAttempted() const { return bValidationAttempted; }

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Bootstrap")
    ELBOneFactoryBootstrapState GetBootstrapState() const { return BootstrapState; }

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Bootstrap")
    FString GetBootstrapStatus() const { return BootstrapStatus; }

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Layout")
    FLBOneFactoryLayoutDefinition GetShellLayoutSnapshot() const { return ShellLayout; }

    const FLBOneFactoryLayoutDefinition& GetShellLayout() const { return ShellLayout; }

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Bootstrap")
    ALBPressShopBuildAuthority* GetPressBuildAuthority() const
    {
        return PressBuildAuthority.Get();
    }

    /** Mutation-free live-world audit used by startup and focused automation. */
    static FLBOneFactoryWorldAudit AuditWorld(UWorld* World);

    /** Stable class/tag policy seams used without starting Unreal gameplay. */
    static bool ActorHasWIPIdentity(const AActor& Actor);
    static bool ActorIsForbiddenLegacyFixture(const AActor& Actor);
    static bool ActorUsesForbiddenProvenance(const AActor& Actor,
        FString& OutReference);

    static FName GetBootstrapAuthorityTag();
    static FName GetPressBuildAuthorityTag();
    static FName GetNativeOnlyTag();

private:
    UPROPERTY(EditInstanceOnly, Category="Line Boss|OneFactory|Layout")
    FLBOneFactoryLayoutDefinition ShellLayout;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|OneFactory|Bootstrap")
    ELBOneFactoryBootstrapState BootstrapState =
        ELBOneFactoryBootstrapState::Unvalidated;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|OneFactory|Bootstrap")
    bool bValidationAttempted = false;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|OneFactory|Bootstrap")
    FString BootstrapStatus = TEXT("ONEFACTORY SHELL NOT YET VALIDATED");

    UPROPERTY(Transient, VisibleInstanceOnly,
        Category="Line Boss|OneFactory|Bootstrap")
    TWeakObjectPtr<ALBPressShopBuildAuthority> PressBuildAuthority;
};
