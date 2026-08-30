#pragma once

#include "CoreMinimal.h"
#include "Components/PrimitiveComponent.h"
#include "GameFramework/Actor.h"
#include "LBOneFactoryPressOutlineProofActor.generated.h"

class APostProcessVolume;
class UMaterialInstanceDynamic;
class UMaterialInterface;
class USceneComponent;
class UStaticMeshComponent;
class ALBOneFactoryPressStarterPresentationActor;

/**
 * Transient, reversible custom-depth outline proof for the configured native
 * Press Shop presentation.  It deliberately owns no presentation geometry or
 * map state: Enable snapshots only currently visible press mesh components,
 * and Disable/EndPlay restores their exact render-custom-depth settings.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBOneFactoryPressOutlineProofActor : public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryPressOutlineProofActor();

    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

    /**
     * Enables the bounded outline proof against exactly one configured Press
     * presentation.  On any preflight failure it leaves the world unchanged.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Press|Outline Proof")
    bool EnableOutlineProof(FString& OutReason);

    /** Removes the transient post-process volume and restores every snapshot. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Press|Outline Proof")
    void DisableOutlineProof();

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Press|Outline Proof")
    bool IsOutlineProofEnabled() const { return bOutlineProofEnabled; }

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Press|Outline Proof")
    int32 GetOutlinedComponentCount() const { return ComponentBackups.Num(); }

    static FName GetOutlineProofTag();
    static const TCHAR* GetOutlineProofClassPath();

private:
    struct FCustomDepthBackup
    {
        TWeakObjectPtr<UStaticMeshComponent> Component;
        bool bRenderCustomDepth = false;
        int32 CustomDepthStencilValue = 0;
        ERendererStencilMask CustomDepthStencilWriteMask =
            ERendererStencilMask::ERSM_Default;
    };

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press|Outline Proof")
    TObjectPtr<USceneComponent> SceneRoot;

    /** The post-process source is native project content, never map-owned. */
    UPROPERTY(VisibleDefaultsOnly, Category="Line Boss|OneFactory|Press|Outline Proof")
    TObjectPtr<UMaterialInterface> OutlineMaterial;

    /** A deliberately conservative, management-camera-visible first proof. */
    UPROPERTY(EditDefaultsOnly, Category="Line Boss|OneFactory|Press|Outline Proof",
        meta=(ClampMin="0.25", ClampMax="8.0"))
    float OutlineThickness = 2.25f;

    UPROPERTY(Transient)
    TObjectPtr<UMaterialInstanceDynamic> OutlineMaterialInstance;

    UPROPERTY(Transient)
    TObjectPtr<APostProcessVolume> OutlinePostProcessVolume;

    TWeakObjectPtr<ALBOneFactoryPressStarterPresentationActor>
        ConfiguredPresentation;
    TArray<FCustomDepthBackup> ComponentBackups;

    /** Restored exactly on Disable, including an original mode other than 3. */
    int32 PreviousCustomDepthMode = 0;
    bool bHasPreviousCustomDepthMode = false;

    UPROPERTY(Transient)
    bool bOutlineProofEnabled = false;

    bool FindExactlyOneConfiguredPresentation(
        ALBOneFactoryPressStarterPresentationActor*& OutPresentation,
        FString& OutReason) const;
    bool ValidateOutlineMaterial(FString& OutReason) const;
    bool SnapshotVisiblePressMeshes(
        ALBOneFactoryPressStarterPresentationActor& Presentation,
        TArray<FCustomDepthBackup>& OutBackups, FString& OutReason) const;
    bool RequireStencilCustomDepth(FString& OutReason);
    void RestoreStencilCustomDepth();
    void RestoreComponentBackups();
    void DestroyOutlineVolume();
};
