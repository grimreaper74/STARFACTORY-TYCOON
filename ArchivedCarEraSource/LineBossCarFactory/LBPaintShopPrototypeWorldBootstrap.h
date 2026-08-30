#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Info.h"
#include "LBPaintShopPrototypeWorldBootstrap.generated.h"

class ALBPaintShopBuildAuthority;
class ALBPaintShopPrototypeRuntime;

UENUM(BlueprintType)
enum class ELBPaintShopPrototypeBootstrapState : uint8
{
    Uninitialized,
    Initializing,
    Ready,
    Failed
};

/**
 * The only startup owner for the isolated Paint Shop vertical slice. It creates exactly
 * one Paint build authority and runtime and has no dependency on any legacy factory chain.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBPaintShopPrototypeWorldBootstrap : public AInfo
{
    GENERATED_BODY()

public:
    ALBPaintShopPrototypeWorldBootstrap();

    virtual void BeginPlay() override;

    /** Spawn, bind and initialize the exact one-cell Paint prototype transactionally. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Prototype")
    bool InitializePrototypeWorld(FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Prototype")
    bool IsReady() const { return BootstrapState == ELBPaintShopPrototypeBootstrapState::Ready; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Prototype")
    bool HasFailed() const { return BootstrapState == ELBPaintShopPrototypeBootstrapState::Failed; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Prototype")
    ELBPaintShopPrototypeBootstrapState GetBootstrapState() const { return BootstrapState; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Prototype")
    FString GetBootstrapReason() const { return BootstrapReason; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Prototype")
    ALBPaintShopBuildAuthority* GetBuildAuthority() const { return BuildAuthority; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Prototype")
    ALBPaintShopPrototypeRuntime* GetRuntime() const { return Runtime; }

    /** Pure exact-count gate used before this bootstrap mutates its isolated world. */
    static bool ValidateSpawnPreconditions(int32 ExistingBuildAuthorityCount,
        int32 ExistingRuntimeCount, FString& OutReason);

private:
    UPROPERTY(Transient)
    TObjectPtr<ALBPaintShopBuildAuthority> BuildAuthority;

    UPROPERTY(Transient)
    TObjectPtr<ALBPaintShopPrototypeRuntime> Runtime;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Paint Shop|Prototype")
    ELBPaintShopPrototypeBootstrapState BootstrapState =
        ELBPaintShopPrototypeBootstrapState::Uninitialized;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Paint Shop|Prototype")
    FString BootstrapReason = TEXT("PAINT SHOP PROTOTYPE HAS NOT BEEN INITIALIZED");

    bool HasCoherentReadyState(FString& OutReason) const;
    bool FailInitialization(ALBPaintShopBuildAuthority* StagedBuildAuthority,
        ALBPaintShopPrototypeRuntime* StagedRuntime, const FString& FailureReason,
        FString& OutReason);
};
