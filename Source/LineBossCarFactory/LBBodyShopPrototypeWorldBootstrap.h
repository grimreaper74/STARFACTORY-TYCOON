#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Info.h"
#include "LBBodyShopPrototypeWorldBootstrap.generated.h"

class ALBBodyShopBuildAuthority;
class ALBBodyShopPrototypeGameMode;
class ALBBodyShopPrototypeRuntime;

UENUM(BlueprintType)
enum class ELBBodyShopPrototypeBootstrapState : uint8
{
    Uninitialised,
    WaitingForRuntime,
    Ready,
    Incompatible
};

/** Observable order for the map-local, runtime-only underbody-slice wiring. */
UENUM(BlueprintType)
enum class ELBBodyShopPrototypeRuntimeWiringStage : uint8
{
    NotStarted,
    RuntimeBoundToBuildAuthority,
    AuthoritiesBoundToBootstrap,
    UnderbodySliceCommissioned,
    Failed
};

/**
 * Map-local opt-in and isolation guard for the experimental Body Shop.
 *
 * This actor has no campaign migration role and never spawns legacy factory
 * actors. The authored map contains this bootstrap only: its two authorities
 * are spawned and connected at runtime by the isolated prototype GameMode.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBBodyShopPrototypeWorldBootstrap : public AInfo
{
    GENERATED_BODY()

public:
    ALBBodyShopPrototypeWorldBootstrap();

    virtual void BeginPlay() override;

    /** Re-evaluates the map-local prototype contract without changing the world. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Prototype")
    void RefreshBootstrapState();

    /**
     * Temporary wiring seam for ALBBodyShopBuildAuthority and
     * ALBBodyShopPrototypeRuntime. Their concrete methods remain outside this
     * bootstrap until their public APIs are frozen.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Prototype")
    bool BindPrototypeAuthorities(AActor* InBuildAuthority, AActor* InRuntime,
        FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    bool IsBootstrapConfigurationValid() const { return bBootstrapConfigurationValid; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    bool HasDetectedLegacyAuthority() const { return bDetectedLegacyAuthority; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    bool IsWorldIsolationValid() const { return bWorldIsolationValid; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    bool ArePrototypeAuthoritiesBound() const
    {
        return IsValid(BuildAuthorityActor.Get()) && IsValid(RuntimeActor.Get());
    }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    bool HasCommissionedInitialUnderbodySlice() const
    {
        return bInitialUnderbodySliceCommissioned;
    }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    ELBBodyShopPrototypeRuntimeWiringStage GetRuntimeWiringStage() const
    {
        return RuntimeWiringStage;
    }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    ELBBodyShopPrototypeBootstrapState GetBootstrapState() const { return BootstrapState; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    FString GetBootstrapStatusText() const { return BootstrapStatusText; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    FVector GetPrototypeBuildOrigin() const { return PrototypeBuildOrigin; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    float GetPrototypeGridSizeCm() const { return PrototypeGridSizeCm; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    bool ShouldRequestInitialUnderbodySlice() const
    {
        return bRequestInitialUnderbodySlice;
    }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    bool ShouldSpawnRuntimeOnBeginPlay() const { return bSpawnRuntimeOnBeginPlay; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    bool ShouldShowPrototypeHUD() const { return bShowPrototypeHUD; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    AActor* GetBuildAuthorityActor() const { return BuildAuthorityActor.Get(); }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    AActor* GetRuntimeActor() const { return RuntimeActor.Get(); }

    /** Pure flag gate, retained for setup tooling and focused automation. */
    static bool ValidateBootstrapFlags(bool bInPrototypeEnabled,
        bool bInRejectLegacyAuthorities, bool bInExperimentalSaveOnly,
        bool bInRequirePrototypeGameMode, float InGridSizeCm, FString& OutReason);

    /** Pure preflight used before spawning any authority into an isolated map. */
    static bool ValidateRuntimeSpawnPreconditions(bool bInSpawnRuntimeOnBeginPlay,
        bool bInRequestInitialUnderbodySlice, int32 ExistingBuildAuthorityCount,
        int32 ExistingRuntimeCount, FString& OutReason);

    /** Class-name gate deliberately avoids dependencies on legacy runtime classes. */
    static bool IsForbiddenLegacyAuthorityClassName(const FString& ClassName);

private:
    friend class ALBBodyShopPrototypeGameMode;

    /**
     * Called only by ALBBodyShopPrototypeGameMode::BeginPlay. It spawns one
     * fresh BuildAuthority and PrototypeRuntime in the fixed safe order:
     * Runtime.BindBuildAuthority -> Bootstrap.BindPrototypeAuthorities ->
     * Runtime.BuildAndCommissionApprovedUnderbodySlice. It refuses pre-baked
     * authorities so the saved map remains an empty experimental shell.
     */
    bool InitialiseRuntimeAuthorities(FString& OutReason);

    /** Explicit map opt-in; turning this off disables the experimental bootstrap. */
    UPROPERTY(EditInstanceOnly, Category="Line Boss|Body Shop|Prototype|Isolation")
    bool bPrototypeEnabled = true;

    /** The prototype must never share its map with v18 / Press Shop authorities. */
    UPROPERTY(EditInstanceOnly, Category="Line Boss|Body Shop|Prototype|Isolation")
    bool bRejectLegacyAuthorities = true;

    /** Experimental Body Shop persistence remains separate from campaign save v18. */
    UPROPERTY(EditInstanceOnly, Category="Line Boss|Body Shop|Prototype|Isolation")
    bool bUseExperimentalSaveOnly = true;

    /** Server-side map validation requires ALBBodyShopPrototypeGameMode. */
    UPROPERTY(EditInstanceOnly, Category="Line Boss|Body Shop|Prototype|Isolation")
    bool bRequirePrototypeGameMode = true;

    /** Runtime authority may build this slice only after all configuration gates pass. */
    UPROPERTY(EditInstanceOnly, Category="Line Boss|Body Shop|Prototype|Slice")
    bool bRequestInitialUnderbodySlice = true;

    /** Keeps the saved map empty: authorities are created by the GameMode BeginPlay only. */
    UPROPERTY(EditInstanceOnly, Category="Line Boss|Body Shop|Prototype|Slice")
    bool bSpawnRuntimeOnBeginPlay = true;

    UPROPERTY(EditInstanceOnly, Category="Line Boss|Body Shop|Prototype|Presentation")
    bool bShowPrototypeHUD = true;

    UPROPERTY(EditInstanceOnly, Category="Line Boss|Body Shop|Prototype|Layout")
    FVector PrototypeBuildOrigin = FVector::ZeroVector;

    UPROPERTY(EditInstanceOnly, Category="Line Boss|Body Shop|Prototype|Layout",
        meta=(ClampMin="100.0", ClampMax="100.0"))
    float PrototypeGridSizeCm = 100.0f;

    /** Generic isolation handles; root will bind the strongly typed authorities after their APIs settle. */
    UPROPERTY(Transient, VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype")
    TObjectPtr<AActor> BuildAuthorityActor;

    UPROPERTY(Transient, VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype")
    TObjectPtr<AActor> RuntimeActor;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype")
    ELBBodyShopPrototypeBootstrapState BootstrapState = ELBBodyShopPrototypeBootstrapState::Uninitialised;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype")
    bool bBootstrapConfigurationValid = false;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype")
    bool bDetectedLegacyAuthority = false;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype")
    bool bWorldIsolationValid = false;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype")
    FString BootstrapStatusText;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype")
    ELBBodyShopPrototypeRuntimeWiringStage RuntimeWiringStage =
        ELBBodyShopPrototypeRuntimeWiringStage::NotStarted;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype")
    bool bInitialUnderbodySliceCommissioned = false;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype")
    bool bRuntimeInitialisationAttempted = false;

    bool ValidateWorldIsolation(FString& OutReason);
};
