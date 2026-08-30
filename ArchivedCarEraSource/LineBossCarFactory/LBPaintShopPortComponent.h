#pragma once

#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "LBPaintShopTypes.h"
#include "LBPaintShopPortComponent.generated.h"

/** Typed internal Paint Shop carrier port; independent of the legacy global stage chain. */
UCLASS(ClassGroup=(LineBoss), meta=(BlueprintSpawnableComponent))
class LINEBOSSCARFACTORY_API ULBPaintShopPortComponent : public USceneComponent
{
    GENERATED_BODY()

public:
    ULBPaintShopPortComponent();

    /**
     * Applies one stable semantic port contract and its separate presentation transform.
     * Invalid input clears any previous configuration so stale routing data cannot survive.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Port")
    bool Configure(const FLBPaintShopPortDefinition& InDefinition,
        const FTransform& InLocalTransform);

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Port")
    bool IsConfigured() const { return bConfigured; }

    /** Returns NAME_None until a complete valid configuration has been applied. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Port")
    FName GetPortId() const { return bConfigured ? Definition.PortId : NAME_None; }

    /** Returns NAME_None until a complete valid configuration has been applied. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Port")
    FName GetWIPId() const { return bConfigured ? Definition.WIPId : NAME_None; }

    /** Direction has no invalid enum member, so callers must observe this boolean result. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Port")
    bool TryGetDirection(ELBPaintShopPortDirection& OutDirection) const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Port")
    bool TryGetDefinition(FLBPaintShopPortDefinition& OutDefinition) const;

    /** Returns identity until a complete valid configuration has been applied. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Port")
    FTransform GetConfiguredLocalTransform() const
    {
        return bConfigured ? ConfiguredLocalTransform : FTransform::Identity;
    }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Port")
    FString GetConfigurationFailureReason() const { return ConfigurationFailureReason; }

private:
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Paint Shop|Port")
    FLBPaintShopPortDefinition Definition;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Paint Shop|Port")
    FTransform ConfiguredLocalTransform = FTransform::Identity;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Paint Shop|Port")
    bool bConfigured = false;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Paint Shop|Port")
    FString ConfigurationFailureReason;

    void ClearConfiguration(const FString& FailureReason);
    static bool ValidateConfiguration(const FLBPaintShopPortDefinition& InDefinition,
        const FTransform& InLocalTransform, FString& OutReason);
};

