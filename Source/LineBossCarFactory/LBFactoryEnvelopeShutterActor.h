#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBFactoryEnvelopeShutterActor.generated.h"

class AStaticMeshActor;
class UBoxComponent;
class UMaterialInterface;
class USceneComponent;
class UStaticMesh;
class UStaticMeshComponent;

/**
 * Runtime-only architecture authority for the first approved factory-envelope shutter.
 *
 * Activation is deliberately atomic: every imported asset and the one durable clean-shell
 * west-wall target must be present before the original wall is hidden.  A missing or ambiguous
 * dependency therefore keeps the complete authored clean shell rather than opening a fake hole.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBFactoryEnvelopeShutterActor : public AActor
{
    GENERATED_BODY()

public:
    ALBFactoryEnvelopeShutterActor();

    /** Fixed west-wall datum aligning the opening with the inbound Y=-1000 logistics axis. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Envelope|Shutter")
    static FTransform GetAuthoredWorldTransform();

    /** Imported leaf's closed top-centre after Blender-to-Unreal handedness conversion. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Envelope|Shutter")
    static FVector GetClosedLeafRelativeLocation();

    /** Axis-aligned clear aperture in the authored world transform. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Envelope|Shutter")
    static FBox GetAuthoredClearOpeningWorldBounds();

    /** Complete-or-fallback replacement of the durable v913 clean-shell west wall. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Envelope|Shutter")
    bool ActivateCleanShellWestWallReplacement();

    /** Moves the leaf through its concealed +Z pocket; only the exact closed state blocks queries. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Envelope|Shutter")
    bool SetShutterOpenFraction(float InOpenFraction);

    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Envelope|Shutter")
    bool IsReplacementActive() const { return bReplacementActive; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Envelope|Shutter")
    float GetShutterOpenFraction() const { return ShutterOpenFraction; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Envelope|Shutter")
    AStaticMeshActor* GetSupersededWall() const { return SupersededWall.Get(); }

    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Envelope|Shutter")
    UStaticMeshComponent* GetStaticWallPresentation() const { return StaticWallPresentation; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Envelope|Shutter")
    UStaticMeshComponent* GetFramePresentation() const { return FramePresentation; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Envelope|Shutter")
    UStaticMeshComponent* GetLeafPresentation() const { return LeafPresentation; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Envelope|Shutter")
    UBoxComponent* GetLeafBarrier() const { return LeafBarrier; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Envelope|Shutter")
    int32 GetReplacementInfillCount() const { return ReplacementInfill.Num(); }

    const TArray<TObjectPtr<UStaticMeshComponent>>& GetReplacementInfill() const
    {
        return ReplacementInfill;
    }

    /** Stable soft-path evidence used by automation and packaged cook/load smoke checks. */
    TArray<FSoftObjectPath> GetRuntimeAssetPaths() const;

#if WITH_DEV_AUTOMATION_TESTS
    void SetUseRuntimeAssetsForTests(bool bInUseRuntimeAssets)
    {
        bUseRuntimeAssetsForTests = bInUseRuntimeAssets;
    }

    void SetRuntimeAssetReferencesForTests(const FSoftObjectPath& StaticWallPath,
        const FSoftObjectPath& FramePath, const FSoftObjectPath& LeafPath,
        const FSoftObjectPath& CubePath, const FSoftObjectPath& WarmWallMaterialPath,
        const FSoftObjectPath& GraphiteMaterialPath);
#endif

private:
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Factory Envelope|Shutter")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Factory Envelope|Shutter")
    TObjectPtr<UStaticMeshComponent> StaticWallPresentation;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Factory Envelope|Shutter")
    TObjectPtr<UStaticMeshComponent> FramePresentation;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Factory Envelope|Shutter")
    TObjectPtr<USceneComponent> LeafMotionRoot;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Factory Envelope|Shutter")
    TObjectPtr<UStaticMeshComponent> LeafPresentation;

    /** Runtime-owned thin query barrier; the imported leaf intentionally has no collision. */
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Factory Envelope|Shutter")
    TObjectPtr<UBoxComponent> LeafBarrier;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Factory Envelope|Shutter")
    TArray<TObjectPtr<UStaticMeshComponent>> ReplacementInfill;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Factory Envelope|Shutter")
    bool bReplacementActive = false;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Factory Envelope|Shutter")
    float ShutterOpenFraction = 0.0f;

    UPROPERTY(Transient)
    TWeakObjectPtr<AStaticMeshActor> SupersededWall;

    UPROPERTY()
    TSoftObjectPtr<UStaticMesh> StaticWallMesh;

    UPROPERTY()
    TSoftObjectPtr<UStaticMesh> FrameMesh;

    UPROPERTY()
    TSoftObjectPtr<UStaticMesh> LeafMesh;

    UPROPERTY()
    TSoftObjectPtr<UStaticMesh> InfillCubeMesh;

    UPROPERTY()
    TSoftObjectPtr<UMaterialInterface> WarmWallMaterial;

    UPROPERTY()
    TSoftObjectPtr<UMaterialInterface> GraphiteMaterial;

#if WITH_DEV_AUTOMATION_TESTS
    bool bUseRuntimeAssetsForTests = false;
#endif

    UStaticMeshComponent* CreateInfillComponent(const TCHAR* Name,
        const FVector& RelativeLocation, const FVector& DimensionsCm,
        bool bUseGraphiteMaterial);
    void SetReplacementPresentationEnabled(bool bEnabled);
    AStaticMeshActor* FindUniqueCleanShellWestWall() const;
    bool IsDurableCleanShellWestWall(const AStaticMeshActor& Candidate) const;
};
