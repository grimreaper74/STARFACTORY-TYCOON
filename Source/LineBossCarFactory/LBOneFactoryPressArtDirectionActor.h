#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBOneFactoryPressStarterLayout.h"
#include "LBOneFactoryPressArtDirectionActor.generated.h"

class UInstancedStaticMeshComponent;
class UMaterialInterface;
class UMeshComponent;
class USceneComponent;
class UStaticMesh;
class ULBFactoryFloorMarkingComponent;
class ALBOneFactoryPressStarterPresentationActor;

/**
 * Runtime-only art-direction layer for the native S01-S07 Press Shop.
 *
 * It owns only large-scale, management-camera-visible composition: reversible
 * exact-palette material overrides, readable floor zones, and a single static
 * overhead-handling silhouette.  It does not own WIP, routes, collision,
 * navigation, new machine geometry, or unproven press animation.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBOneFactoryPressArtDirectionActor : public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryPressArtDirectionActor();

    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

    /** Applies the isolated palette and graphic composition after the native press validates. */
    bool ConfigureFromPressPresentation(
        ALBOneFactoryPressStarterPresentationActor& Presentation,
        const FLBOneFactoryPressStarterLayoutState& Layout, FString& OutReason);

    /** Restores exact pre-override material bindings and removes only our composition. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Press|Art Direction")
    void ClearArtDirection();

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Press|Art Direction")
    bool IsArtDirectionConfigured() const { return bConfigured; }

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Press|Art Direction")
    int32 GetFloorPaintCount() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Press|Art Direction")
    int32 GetOverheadStructureInstanceCount() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Press|Art Direction")
    int32 GetOverheadAccentInstanceCount() const;

    static FName GetArtDirectionTag();
    static const TCHAR* GetArtDirectionClassPath();
    static TArray<FSoftObjectPath> GetRequiredNativeAssetPaths();
    static bool ValidateNativeArtDirectionReferences(
        const TArray<FSoftObjectPath>& AssetPaths, FString& OutReason);

private:
    struct FMaterialOverrideBackup
    {
        TWeakObjectPtr<UMeshComponent> Component;
        /** Original component override array, not resolved mesh defaults. */
        TArray<TObjectPtr<UMaterialInterface>> OverrideMaterials;
    };

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press|Art Direction")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press|Art Direction")
    TObjectPtr<ULBFactoryFloorMarkingComponent> PressFloorPaint;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press|Art Direction")
    TObjectPtr<UInstancedStaticMeshComponent> OverheadStructure;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press|Art Direction")
    TObjectPtr<UInstancedStaticMeshComponent> OverheadAccent;

    UPROPERTY(VisibleDefaultsOnly, Category="Line Boss|OneFactory|Press|Art Direction")
    TObjectPtr<UStaticMesh> PrimitiveCubeMesh;

    UPROPERTY(VisibleDefaultsOnly, Category="Line Boss|OneFactory|Press|Art Direction")
    TObjectPtr<UMaterialInterface> PaletteCairnwellGreen;

    UPROPERTY(VisibleDefaultsOnly, Category="Line Boss|OneFactory|Press|Art Direction")
    TObjectPtr<UMaterialInterface> PaletteFoundryCharcoal;

    UPROPERTY(VisibleDefaultsOnly, Category="Line Boss|OneFactory|Press|Art Direction")
    TObjectPtr<UMaterialInterface> PaletteSteelGrey;

    UPROPERTY(VisibleDefaultsOnly, Category="Line Boss|OneFactory|Press|Art Direction")
    TObjectPtr<UMaterialInterface> PaletteWarmWhite;

    UPROPERTY(VisibleDefaultsOnly, Category="Line Boss|OneFactory|Press|Art Direction")
    TObjectPtr<UMaterialInterface> PaletteSafetyYellow;

    UPROPERTY(VisibleDefaultsOnly, Category="Line Boss|OneFactory|Press|Art Direction")
    TObjectPtr<UMaterialInterface> PaletteSignalRed;

    UPROPERTY(VisibleDefaultsOnly, Category="Line Boss|OneFactory|Press|Art Direction")
    TObjectPtr<UMaterialInterface> PalettePaleGreenZone;

    TArray<FMaterialOverrideBackup> MaterialOverrideBackups;

    UPROPERTY(Transient)
    bool bConfigured = false;

    bool ValidatePaletteLibrary(FString& OutReason) const;
    bool ApplyPaletteOverrides(ALBOneFactoryPressStarterPresentationActor& Presentation,
        FString& OutReason);
    void RestorePaletteOverrides();
    void ConfigureFloorZones(const FTransform& TrainAnchor);
    void ConfigureOverheadHandling(const FTransform& TrainAnchor);
};
