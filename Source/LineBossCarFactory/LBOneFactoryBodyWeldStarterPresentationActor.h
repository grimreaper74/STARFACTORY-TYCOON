#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBOneFactoryBodyWeldStarterLayout.h"
#include "LBOneFactoryBodyWeldStarterPresentationActor.generated.h"

class UHierarchicalInstancedStaticMeshComponent;
class UMaterialInstanceDynamic;
class UMaterialInterface;
class USceneComponent;
class UStaticMesh;

/**
 * Twenty native-authored mesh bindings and four Engine-cube semantic batches.
 * Every enum value maps to one immutable HISM component.
 */
UENUM(BlueprintType)
enum class ELBOneFactoryBodyWeldPresentationBatch : uint8
{
    RobotBase,
    RobotJ1,
    RobotJ2,
    RobotJ3,
    RobotJ4,
    RobotJ5,
    RobotJ6,
    RobotOpenCGun,
    ComponentServicePallet,
    ElectricalCabinet,
    EmptyReturnCart,
    ExtractionPedestal,
    GuardGate,
    GuardPanel,
    HMIPedestal,
    PanelStillageEmpty,
    PanelStillageFull,
    SmallPartsBinOpen,
    SmallPartsCrateOpen,
    UtilityPedestal,
    ProgrammeFixtureCube,
    FloorRouteCube,
    RobotRoleCube,
    StatusCube,
    BatchCount UMETA(Hidden)
};

/** One deterministic visual item derived from a validated data snapshot. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryBodyWeldPresentationItem
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    int32 Version = 1;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    FName PresentationId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    FName StationId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    int32 LinePosition = 0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    ELBOneFactoryBodyWeldPresentationBatch Batch =
        ELBOneFactoryBodyWeldPresentationBatch::RobotBase;

    /** Meaningful only when bProgrammeFixture is true. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    ELBOneFactoryBodyWeldProgramme Programme =
        ELBOneFactoryBodyWeldProgramme::PressedPanelReceive;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    bool bProgrammeFixture = false;

    /** Meaningful only for robot parts and robot-role markers. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    ELBOneFactoryBodyWeldRobotSide RobotSide =
        ELBOneFactoryBodyWeldRobotSide::Left;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    ELBOneFactoryBodyWeldRobotRole RobotRole =
        ELBOneFactoryBodyWeldRobotRole::None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    bool bRobotPart = false;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    FTransform WorldTransform = FTransform::Identity;

    /** Frozen false: visual dressing never owns, reserves or simulates a BIW. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    bool bRepresentsProcessWIP = false;
};

/**
 * Visual-only materialisation of the configurable 18-position Body/Weld line.
 * A complete snapshot and every exact dependency resolve before any instance
 * is exposed; failed configuration clears the actor atomically.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBOneFactoryBodyWeldStarterPresentationActor :
    public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryBodyWeldStarterPresentationActor();

    UFUNCTION(BlueprintCallable,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    bool ConfigureFromLayout(
        const FLBOneFactoryBodyWeldLayoutState& Layout, FString& OutReason);

    UFUNCTION(BlueprintCallable,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    void ClearPresentation();

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    bool IsPresentationConfigured() const { return bPresentationConfigured; }

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    bool RepresentsProcessWIP() const { return false; }

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    int32 GetVisibleInstanceCount() const;

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    int32 GetVisualBatchCount() const;

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    int32 GetInstanceCountForBatch(
        ELBOneFactoryBodyWeldPresentationBatch Batch) const;

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    bool GetConfiguredStationTransform(
        FName StationId, FTransform& OutWorldTransform) const;

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    TArray<FLBOneFactoryBodyWeldPresentationItem>
        GetConfiguredItemsForProgramme(
            ELBOneFactoryBodyWeldProgramme InProgramme) const;

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    TArray<FLBOneFactoryBodyWeldPresentationItem> GetConfiguredRobotItems(
        FName StationId, ELBOneFactoryBodyWeldRobotSide InRobotSide) const;

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    FName GetConfiguredLayoutId() const { return ConfiguredLayoutId; }

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    int32 GetConfiguredLayoutRevision() const
    { return ConfiguredLayoutRevision; }

    static int32 GetExpectedVisualBatchCount();
    static int32 GetCanonicalVisibleInstanceCount();
    static int32 GetExpectedVisibleInstanceCount(
        const FLBOneFactoryBodyWeldLayoutState& Layout);
    static int32 GetExpectedInstanceCountForBatch(
        const FLBOneFactoryBodyWeldLayoutState& Layout,
        ELBOneFactoryBodyWeldPresentationBatch Batch);

    /** 24 ordered mesh bindings plus one semantic material binding. */
    static TArray<FSoftObjectPath> GetRequiredNativeAssetPaths();

    /** Exact native-code class and NativeOnly asset allowlist validation seam. */
    static bool ValidateNativePresentationReferences(
        const FString& PresentationClassPath,
        const TArray<FSoftObjectPath>& AssetPaths, FString& OutReason);

    static TArray<FLBOneFactoryBodyWeldPresentationItem>
        BuildExpectedPresentationItems(
            const FLBOneFactoryBodyWeldLayoutState& Layout);

    static bool ValidatePresentationContract(
        const FLBOneFactoryBodyWeldLayoutState& Layout,
        const TArray<FLBOneFactoryBodyWeldPresentationItem>& Items,
        FString& OutReason);

    static const TCHAR* GetPresentationClassPath();
    static FName GetPresentationTag();

private:
    UPROPERTY(VisibleAnywhere,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere,
        Category="Line Boss|OneFactory|Body Weld|Presentation")
    TArray<TObjectPtr<UHierarchicalInstancedStaticMeshComponent>>
        VisualBatches;

    UPROPERTY(Transient)
    TArray<TSoftObjectPtr<UStaticMesh>> MeshBindings;

    UPROPERTY(Transient)
    TSoftObjectPtr<UMaterialInterface> SemanticBaseMaterial;

    UPROPERTY(Transient)
    TArray<TObjectPtr<UMaterialInstanceDynamic>> SemanticMaterials;

    UPROPERTY(Transient)
    TArray<FLBOneFactoryBodyWeldPresentationItem> ConfiguredItems;

    UPROPERTY(Transient)
    TMap<FName, FTransform> ConfiguredStationTransforms;

    UPROPERTY(Transient)
    FName ConfiguredLayoutId = NAME_None;

    UPROPERTY(Transient)
    int32 ConfiguredLayoutRevision = INDEX_NONE;

    UPROPERTY(Transient)
    bool bPresentationConfigured = false;

    UHierarchicalInstancedStaticMeshComponent* FindBatchComponent(
        ELBOneFactoryBodyWeldPresentationBatch Batch) const;
    TArray<UHierarchicalInstancedStaticMeshComponent*> GetAllBatches() const;
    static void ConfigureVisualBatch(
        UHierarchicalInstancedStaticMeshComponent* Component);
};
