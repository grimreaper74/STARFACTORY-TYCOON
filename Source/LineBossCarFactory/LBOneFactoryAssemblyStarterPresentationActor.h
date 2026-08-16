#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBOneFactoryAssemblyStarterLayout.h"
#include "LBOneFactoryAssemblyStarterPresentationActor.generated.h"

class UHierarchicalInstancedStaticMeshComponent;
class UMaterialInstanceDynamic;
class UMaterialInterface;
class USceneComponent;
class UStaticMesh;

/**
 * Eight exact native-authored Assembly meshes plus two Engine-cube semantic
 * batches.  Each enum value has one immutable HISM component.
 */
UENUM(BlueprintType)
enum class ELBOneFactoryAssemblyPresentationBatch : uint8
{
    SkilletCarrier,
    SequencedPartsCart,
    WheelTireRack,
    CockpitInstallAssist,
    HeavyMarriageGantry,
    ErgonomicLiftPlatform,
    WheelAlignmentBed,
    EOLInspectionArch,
    FloorRouteCube,
    StatusCube
};

/** One deterministic visual item derived from a validated Assembly snapshot. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryAssemblyPresentationItem
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Assembly|Presentation")
    int32 Version = 1;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Assembly|Presentation")
    FName PresentationId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Assembly|Presentation")
    FName StationId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Assembly|Presentation")
    int32 LinePosition = 0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Assembly|Presentation")
    ELBOneFactoryAssemblyPresentationBatch Batch =
        ELBOneFactoryAssemblyPresentationBatch::SkilletCarrier;

    /** Meaningful only when bOperationFixture is true. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Assembly|Presentation")
    ELBOneFactoryAssemblyOperation Operation =
        ELBOneFactoryAssemblyOperation::PaintedBodyReceive;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Assembly|Presentation")
    bool bOperationFixture = false;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Assembly|Presentation")
    FTransform WorldTransform = FTransform::Identity;

    /** Frozen false: this actor never owns, reserves or simulates a vehicle. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Assembly|Presentation")
    bool bRepresentsProcessWIP = false;
};

/**
 * Native visual-only materialisation of the configurable 24-position line.
 *
 * A complete validated data snapshot and all ten exact assets must resolve
 * before any instance is exposed.  Failed configuration therefore leaves an
 * empty actor rather than a partial or misleading production line.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBOneFactoryAssemblyStarterPresentationActor :
    public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryAssemblyStarterPresentationActor();

    UFUNCTION(BlueprintCallable,
        Category="Line Boss|OneFactory|Assembly|Presentation")
    bool ConfigureFromLayout(
        const FLBOneFactoryAssemblyLayoutState& Layout, FString& OutReason);

    UFUNCTION(BlueprintCallable,
        Category="Line Boss|OneFactory|Assembly|Presentation")
    void ClearPresentation();

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Assembly|Presentation")
    bool IsPresentationConfigured() const { return bPresentationConfigured; }

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Assembly|Presentation")
    bool RepresentsProcessWIP() const { return false; }

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Assembly|Presentation")
    int32 GetVisibleInstanceCount() const;

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Assembly|Presentation")
    int32 GetVisualBatchCount() const;

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Assembly|Presentation")
    int32 GetInstanceCountForBatch(
        ELBOneFactoryAssemblyPresentationBatch Batch) const;

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Assembly|Presentation")
    bool GetConfiguredStationTransform(
        FName StationId, FTransform& OutWorldTransform) const;

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Assembly|Presentation")
    TArray<FLBOneFactoryAssemblyPresentationItem>
        GetConfiguredItemsForOperation(
            ELBOneFactoryAssemblyOperation InOperation) const;

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Assembly|Presentation")
    FName GetConfiguredLayoutId() const { return ConfiguredLayoutId; }

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Assembly|Presentation")
    int32 GetConfiguredLayoutRevision() const
    { return ConfiguredLayoutRevision; }

    static int32 GetExpectedVisualBatchCount();
    static int32 GetExpectedVisibleInstanceCount();
    static int32 GetExpectedInstanceCountForBatch(
        ELBOneFactoryAssemblyPresentationBatch Batch);

    /** Eight authored meshes, Engine Cube and BasicShapeMaterial, exact order. */
    static TArray<FSoftObjectPath> GetRequiredNativeAssetPaths();

    /** Exact native-code class and NativeOnly asset allowlist validation seam. */
    static bool ValidateNativePresentationReferences(
        const FString& PresentationClassPath,
        const TArray<FSoftObjectPath>& AssetPaths, FString& OutReason);

    /** 24 carriers + 24 operation fixtures + 23 routes + 24 status markers. */
    static TArray<FLBOneFactoryAssemblyPresentationItem>
        BuildExpectedPresentationItems(
            const FLBOneFactoryAssemblyLayoutState& Layout);

    static bool ValidatePresentationContract(
        const FLBOneFactoryAssemblyLayoutState& Layout,
        const TArray<FLBOneFactoryAssemblyPresentationItem>& Items,
        FString& OutReason);

    static const TCHAR* GetPresentationClassPath();
    static FName GetPresentationTag();

private:
    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Assembly|Presentation")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Assembly|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> SkilletCarrierBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Assembly|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> SequencedPartsCartBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Assembly|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> WheelTireRackBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Assembly|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> CockpitInstallAssistBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Assembly|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> HeavyMarriageGantryBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Assembly|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> ErgonomicLiftPlatformBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Assembly|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> WheelAlignmentBedBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Assembly|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> EOLInspectionArchBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Assembly|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> FloorRouteCubeBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Assembly|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> StatusCubeBatch;

    UPROPERTY(Transient)
    TSoftObjectPtr<UStaticMesh> SkilletCarrierMesh;

    UPROPERTY(Transient)
    TSoftObjectPtr<UStaticMesh> SequencedPartsCartMesh;

    UPROPERTY(Transient)
    TSoftObjectPtr<UStaticMesh> WheelTireRackMesh;

    UPROPERTY(Transient)
    TSoftObjectPtr<UStaticMesh> CockpitInstallAssistMesh;

    UPROPERTY(Transient)
    TSoftObjectPtr<UStaticMesh> HeavyMarriageGantryMesh;

    UPROPERTY(Transient)
    TSoftObjectPtr<UStaticMesh> ErgonomicLiftPlatformMesh;

    UPROPERTY(Transient)
    TSoftObjectPtr<UStaticMesh> WheelAlignmentBedMesh;

    UPROPERTY(Transient)
    TSoftObjectPtr<UStaticMesh> EOLInspectionArchMesh;

    UPROPERTY(Transient)
    TSoftObjectPtr<UStaticMesh> CubeMesh;

    UPROPERTY(Transient)
    TSoftObjectPtr<UMaterialInterface> SemanticBaseMaterial;

    UPROPERTY(Transient)
    TArray<TObjectPtr<UMaterialInstanceDynamic>> SemanticMaterials;

    UPROPERTY(Transient)
    TArray<FLBOneFactoryAssemblyPresentationItem> ConfiguredItems;

    UPROPERTY(Transient)
    TMap<FName, FTransform> ConfiguredStationTransforms;

    UPROPERTY(Transient)
    FName ConfiguredLayoutId = NAME_None;

    UPROPERTY(Transient)
    int32 ConfiguredLayoutRevision = INDEX_NONE;

    UPROPERTY(Transient)
    bool bPresentationConfigured = false;

    UHierarchicalInstancedStaticMeshComponent* FindBatchComponent(
        ELBOneFactoryAssemblyPresentationBatch Batch) const;
    TArray<UHierarchicalInstancedStaticMeshComponent*> GetAllBatches() const;
    static void ConfigureVisualBatch(
        UHierarchicalInstancedStaticMeshComponent* Component);
};

