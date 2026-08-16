#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "LBFactoryBrandSubsystem.h"
#include "LBMachineLiveryComponent.generated.h"

class UMaterialInstanceDynamic;
class UMaterialInterface;
class UMeshComponent;

/** Only these cosmetic roles may consume the player machine livery. */
UENUM(BlueprintType)
enum class ELBMachineLiveryRole : uint8
{
    PrimaryBody,
    SecondaryFrame
};

USTRUCT()
struct FLBMachineLiveryMaterialBinding
{
    GENERATED_BODY()

    UPROPERTY(Transient)
    TObjectPtr<UMeshComponent> MeshComponent;

    UPROPERTY(Transient)
    int32 MaterialIndex = INDEX_NONE;

    UPROPERTY(Transient)
    ELBMachineLiveryRole Role = ELBMachineLiveryRole::PrimaryBody;

    UPROPERTY(Transient)
    FName TintParameter = TEXT("BaseColorTint");

    /** Null for approved art: its current textured material remains the MID parent. */
    UPROPERTY(Transient)
    TObjectPtr<UMaterialInterface> ExplicitTintableParent;

    UPROPERTY(Transient)
    TObjectPtr<UMaterialInterface> OriginalMaterial;

    UPROPERTY(Transient)
    TObjectPtr<UMaterialInstanceDynamic> DynamicMaterial;
};

/**
 * Explicit, opt-in machine paint binding.
 *
 * Approved Meshy/runtime art registers only author-approved body/frame material slots
 * whose master exposes a tint vector. The component creates a MID from that existing
 * textured parent, so normal/roughness/metal/wear/label detail is retained. Safety
 * paint, warning red, status lenses, liquids and floor markings are never discovered
 * or recoloured automatically.
 */
UCLASS(ClassGroup=(LineBoss), meta=(BlueprintSpawnableComponent))
class LINEBOSSCARFACTORY_API ULBMachineLiveryComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    ULBMachineLiveryComponent();

    /**
     * Approved-art hook. The existing material remains the parent; TintParameter must
     * be deliberately authored into that material (normally BaseColorTint/LiveryTint).
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Machine Livery")
    bool RegisterTexturedMaterialBinding(UMeshComponent* MeshComponent, int32 MaterialIndex,
        ELBMachineLiveryRole Role, FName TintParameter);

    /** C++ hook for engine-native generic shapes which use a known tintable parent. */
    bool RegisterGenericMaterialBinding(UMeshComponent* MeshComponent, int32 MaterialIndex,
        ELBMachineLiveryRole Role, UMaterialInterface* TintableParent,
        FName TintParameter = TEXT("Color"));

    /** Restores every slot to the material it had before this component registered it. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Machine Livery")
    void ClearMaterialBindings();

    UFUNCTION(BlueprintCallable, Category="Line Boss|Machine Livery")
    void RefreshFromFactoryBrand();

    UFUNCTION(BlueprintPure, Category="Line Boss|Machine Livery")
    int32 GetMaterialBindingCount() const { return MaterialBindings.Num(); }

    UMaterialInstanceDynamic* GetDynamicMaterialForBinding(int32 BindingIndex) const;

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
    UPROPERTY(Transient)
    TArray<FLBMachineLiveryMaterialBinding> MaterialBindings;

    FDelegateHandle LiveryChangedHandle;

    bool RegisterBinding(UMeshComponent* MeshComponent, int32 MaterialIndex,
        ELBMachineLiveryRole Role, FName TintParameter, UMaterialInterface* ExplicitTintableParent);
    void ApplyMachineLivery(const FLBFactoryMachineLivery& Livery);
    void HandleMachineLiveryChanged(const FLBFactoryMachineLivery& Livery);
    void SubscribeToFactoryBrand();
    void UnsubscribeFromFactoryBrand();
};
