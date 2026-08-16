#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBOneFactoryPaintStarterLayout.h"
#include "LBOneFactoryPaintStarterPresentationActor.generated.h"

class UHierarchicalInstancedStaticMeshComponent;
class UMaterialInstanceDynamic;
class UMaterialInterface;
class USceneComponent;
class UStaticMesh;

/**
 * Exact OneFactory Paint presentation batches. The spray booth remains an
 * exterior black box; the ED route is an open, visual-only tracked process.
 */
UENUM(BlueprintType)
enum class ELBOneFactoryPaintPresentationBatch : uint8
{
    CuringOvenTunnel,
    PretreatmentWashTunnel,
    FlashOffTunnel,
    QualityLightTunnel,
    BodySkidCarrier,
    PaintServiceSet,
    AirExtractionModule,
    BlackBoxSprayBooth,
    FloorRouteCube,
    StatusCube,
    ProgrammeColourCube,
    EDTreatmentStartModule,
    EDTreatmentEndModule,
    EDLiquidDegrease,
    EDLiquidRinse1,
    EDLiquidPhosphate,
    EDLiquidRinse2,
    EDLiquidEDCoat,
    EDLiquidUFRinse,
    EDProfiledRailCube,
    EDImmersedBody,
    EDDrainInspectionModule,
    EDOvenEntryModule,
    EDOvenProcessModule,
    EDOvenExitModule
};

/** One deterministic visual item derived from a validated Paint snapshot. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryPaintPresentationItem
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Paint|Presentation")
    int32 Version = 1;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Paint|Presentation")
    FName PresentationId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Paint|Presentation")
    FName StationId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Paint|Presentation")
    ELBOneFactoryPaintStarterRole Role =
        ELBOneFactoryPaintStarterRole::BodySkidReceiving;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Paint|Presentation")
    ELBOneFactoryPaintPresentationBatch Batch =
        ELBOneFactoryPaintPresentationBatch::BodySkidCarrier;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Paint|Presentation")
    FTransform WorldTransform = FTransform::Identity;

    /** Frozen false: visible ED equipment is presentation, never hidden simulation. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Paint|Presentation")
    bool bClaimsHiddenProcessInternals = false;

    /** Frozen false: this actor never owns or reserves a vehicle body. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Paint|Presentation")
    bool bRepresentsProcessWIP = false;
};

/**
 * Visual-only native Paint materialisation. The original ten dependencies and
 * the exact project-authored ED module/material closure resolve before a single
 * HISM instance is committed.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBOneFactoryPaintStarterPresentationActor :
    public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryPaintStarterPresentationActor();

    UFUNCTION(BlueprintCallable,
        Category="Line Boss|OneFactory|Paint|Presentation")
    bool ConfigureFromLayout(
        const FLBOneFactoryPaintStarterLayoutState& Layout,
        FString& OutReason);

    UFUNCTION(BlueprintCallable,
        Category="Line Boss|OneFactory|Paint|Presentation")
    void ClearPresentation();

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Paint|Presentation")
    bool IsPresentationConfigured() const { return bPresentationConfigured; }

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Paint|Presentation")
    bool RepresentsProcessWIP() const { return false; }

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Paint|Presentation")
    bool ClaimsHiddenProcessInternals() const { return false; }

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Paint|Presentation")
    int32 GetVisibleInstanceCount() const;

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Paint|Presentation")
    int32 GetVisualBatchCount() const;

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Paint|Presentation")
    int32 GetInstanceCountForBatch(
        ELBOneFactoryPaintPresentationBatch Batch) const;

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Paint|Presentation")
    int32 GetInstanceCountForRole(
        ELBOneFactoryPaintStarterRole InRole) const;

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Paint|Presentation")
    bool GetConfiguredStationTransform(
        FName StationId, FTransform& OutWorldTransform) const;

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Paint|Presentation")
    TArray<FLBOneFactoryPaintPresentationItem> GetConfiguredItemsForRole(
        ELBOneFactoryPaintStarterRole InRole) const;

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Paint|Presentation")
    FName GetConfiguredLayoutId() const { return ConfiguredLayoutId; }

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Paint|Presentation")
    int32 GetConfiguredLayoutRevision() const
    { return ConfiguredLayoutRevision; }

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Paint|Presentation")
    ELBOneFactoryPaintColour GetConfiguredBodyColour() const
    { return ConfiguredBodyColour; }

    static int32 GetExpectedVisualBatchCount();
    static int32 GetExpectedVisibleInstanceCount();
    static int32 GetExpectedInstanceCountForBatch(
        ELBOneFactoryPaintPresentationBatch Batch);
    static int32 GetExpectedInstanceCountForRole(
        ELBOneFactoryPaintStarterRole Role);

    /** Original ten references followed by the exact 15-object ED/BIW closure. */
    static TArray<FSoftObjectPath> GetRequiredNativeAssetPaths();

    static bool ValidateNativePresentationReferences(
        const FString& PresentationClassPath,
        const TArray<FSoftObjectPath>& AssetPaths, FString& OutReason);

    /** Canonical topology plus an open six-tank, profiled-rail, drain/oven display. */
    static TArray<FLBOneFactoryPaintPresentationItem>
        BuildExpectedPresentationItems(
            const FLBOneFactoryPaintStarterLayoutState& Layout);

    static bool ValidatePresentationContract(
        const FLBOneFactoryPaintStarterLayoutState& Layout,
        const TArray<FLBOneFactoryPaintPresentationItem>& Items,
        FString& OutReason);

    static const TCHAR* GetPresentationClassPath();
    static FName GetPresentationTag();

private:
    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> CuringOvenBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> PretreatmentBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> FlashOffBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> QualityLightBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> BodySkidBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> ServiceSetBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> AirExtractionBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> SprayBoothBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> FloorRouteBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> StatusBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> ProgrammeColourBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> EDTreatmentStartBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> EDTreatmentEndBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> EDLiquidDegreaseBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> EDLiquidRinse1Batch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> EDLiquidPhosphateBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> EDLiquidRinse2Batch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> EDLiquidEDCoatBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> EDLiquidUFRinseBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> EDProfiledRailBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> EDImmersedBodyBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> EDDrainInspectionBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> EDOvenEntryBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> EDOvenProcessBatch;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Paint|Presentation")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> EDOvenExitBatch;

    UPROPERTY(Transient)
    TSoftObjectPtr<UStaticMesh> CuringOvenMesh;

    UPROPERTY(Transient)
    TSoftObjectPtr<UStaticMesh> PretreatmentMesh;

    UPROPERTY(Transient)
    TSoftObjectPtr<UStaticMesh> FlashOffMesh;

    UPROPERTY(Transient)
    TSoftObjectPtr<UStaticMesh> QualityLightMesh;

    UPROPERTY(Transient)
    TSoftObjectPtr<UStaticMesh> BodySkidMesh;

    UPROPERTY(Transient)
    TSoftObjectPtr<UStaticMesh> ServiceSetMesh;

    UPROPERTY(Transient)
    TSoftObjectPtr<UStaticMesh> AirExtractionMesh;

    UPROPERTY(Transient)
    TSoftObjectPtr<UStaticMesh> SprayBoothMesh;

    UPROPERTY(Transient)
    TSoftObjectPtr<UStaticMesh> CubeMesh;

    UPROPERTY(Transient)
    TSoftObjectPtr<UMaterialInterface> SemanticBaseMaterial;

    /** Native CDO hard references make the exact ED closure cook-reachable. */
    UPROPERTY()
    TObjectPtr<UStaticMesh> EDTreatmentStartMesh;

    UPROPERTY()
    TObjectPtr<UStaticMesh> EDTreatmentEndMesh;

    UPROPERTY()
    TObjectPtr<UStaticMesh> EDDrainInspectionMesh;

    UPROPERTY()
    TObjectPtr<UStaticMesh> EDOvenEntryMesh;

    UPROPERTY()
    TObjectPtr<UStaticMesh> EDOvenProcessMesh;

    UPROPERTY()
    TObjectPtr<UStaticMesh> EDOvenExitMesh;

    UPROPERTY()
    TObjectPtr<UStaticMesh> EDTreatmentLiquidMesh;

    UPROPERTY()
    TObjectPtr<UStaticMesh> EDImmersedBIWMesh;

    UPROPERTY()
    TObjectPtr<UMaterialInterface> EDImmersedBIWMaterial;

    UPROPERTY()
    TArray<TObjectPtr<UMaterialInterface>> EDTreatmentLiquidMaterials;

    UPROPERTY(Transient)
    TArray<TObjectPtr<UMaterialInstanceDynamic>> SemanticMaterials;

    UPROPERTY(Transient)
    TArray<FLBOneFactoryPaintPresentationItem> ConfiguredItems;

    UPROPERTY(Transient)
    TMap<FName, FTransform> ConfiguredStationTransforms;

    UPROPERTY(Transient)
    FName ConfiguredLayoutId = NAME_None;

    UPROPERTY(Transient)
    int32 ConfiguredLayoutRevision = INDEX_NONE;

    UPROPERTY(Transient)
    ELBOneFactoryPaintColour ConfiguredBodyColour =
        ELBOneFactoryPaintColour::BodyInWhite;

    UPROPERTY(Transient)
    bool bPresentationConfigured = false;

    UHierarchicalInstancedStaticMeshComponent* FindBatchComponent(
        ELBOneFactoryPaintPresentationBatch Batch) const;
    TArray<UHierarchicalInstancedStaticMeshComponent*> GetAllBatches() const;
    static void ConfigureVisualBatch(
        UHierarchicalInstancedStaticMeshComponent* Component);
};
