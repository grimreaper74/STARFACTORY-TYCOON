#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBOneFactoryPressStarterLayout.h"
#include "LBOneFactoryPressStarterPresentationActor.generated.h"

class USceneComponent;
class UStaticMesh;
class UStaticMeshComponent;

/**
 * Frozen logical semantics for the 268-item station contract.  The detailed
 * pre-Meshy aggregate is one render batch, but these values remain the stable
 * selection/role metadata consumed by the existing builder API.
 */
UENUM(BlueprintType)
enum class ELBOneFactoryPressPresentationBatch : uint8
{
    GraphiteCube,
    TealStructureCube,
    SteelCube,
    SafetyCube,
    StatusCube,
    GraphiteCylinder,
    SteelCylinder,
    FloorRouteCube
};

/** One immutable logical visual record bound to a stable Press starter station. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryPressPresentationItem
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    int32 Version = 1;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    FName PresentationId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    FName StationId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    ELBOneFactoryPressStarterRole Role =
        ELBOneFactoryPressStarterRole::InboundCoilReceiving;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    ELBOneFactoryPressPresentationBatch Batch =
        ELBOneFactoryPressPresentationBatch::GraphiteCube;

    /** World transform derived from the layout authority's stable station transform. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    FTransform WorldTransform = FTransform::Identity;

    /** Frozen false: primitives are signage/dressing, never production inventory. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    bool bRepresentsProcessWIP = false;
};

/**
 * Visual-only materialisation of the verified pre-Meshy v449 Press aggregate.
 *
 * The actor consumes a complete validated layout snapshot in one transaction. It
 * never creates process ports, machines, reservations, inventory or SaveGame state.
 * Two private static-mesh components provide double-buffered commit/rollback;
 * failed validation preserves the prior committed presentation exactly.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBOneFactoryPressStarterPresentationActor :
    public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryPressStarterPresentationActor();

    /** Fail-closed visual commit from one coherent layout-authority snapshot. */
    UFUNCTION(BlueprintCallable,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    bool ConfigureFromLayout(
        const FLBOneFactoryPressStarterLayoutState& Layout, FString& OutReason);

    UFUNCTION(BlueprintCallable,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    void ClearPresentation();

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    bool IsPresentationConfigured() const { return bPresentationConfigured; }

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    bool RepresentsProcessWIP() const { return false; }

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    int32 GetVisibleInstanceCount() const;

    /** Exactly one detailed aggregate after commit; zero while never configured/cleared. */
    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    int32 GetVisualBatchCount() const;

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    int32 GetInstanceCountForRole(ELBOneFactoryPressStarterRole InRole) const;

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    int32 GetInstanceCountForBatch(
        ELBOneFactoryPressPresentationBatch Batch) const;

    /** Stable-ID lookup for management selection/highlighting. */
    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    bool GetConfiguredStationTransform(
        FName StationId, FTransform& OutWorldTransform) const;

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    TArray<FLBOneFactoryPressPresentationItem> GetConfiguredItemsForRole(
        ELBOneFactoryPressStarterRole InRole) const;

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    FName GetConfiguredLayoutId() const { return ConfiguredLayoutId; }

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    int32 GetConfiguredLayoutRevision() const { return ConfiguredLayoutRevision; }

    static int32 GetExpectedVisualBatchCount();
    static int32 GetExpectedVisibleInstanceCount();
    static int32 GetExpectedInstanceCountForRole(
        ELBOneFactoryPressStarterRole InRole);
    static int32 GetExpectedInstanceCountForBatch(
        ELBOneFactoryPressPresentationBatch Batch);

    /** Exact owned aggregate plus thirteen accepted PBR materials, immutable order. */
    static TArray<FSoftObjectPath> GetRequiredNativeAssetPaths();

    /** Exact local class and owned verified-pre-Meshy asset closure contract. */
    static bool ValidateNativePresentationReferences(
        const FString& PresentationClassPath,
        const TArray<FSoftObjectPath>& AssetPaths, FString& OutReason);

    /** Deterministic 268-item logical contract retained for selection and WIP gates. */
    static TArray<FLBOneFactoryPressPresentationItem>
        BuildExpectedPresentationItems(
            const FLBOneFactoryPressStarterLayoutState& Layout);

    /** Exact inventory/identity/role/batch/transform and zero-WIP validation seam. */
    static bool ValidatePresentationContract(
        const FLBOneFactoryPressStarterLayoutState& Layout,
        const TArray<FLBOneFactoryPressPresentationItem>& Items,
        FString& OutReason);

    static const TCHAR* GetPresentationClassPath();
    static FName GetPresentationTag();

private:
    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMeshComponent> DetailedPresentationA;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMeshComponent> DetailedPresentationB;

    /**
     * Native-CDO hard reference: keeps the exact aggregate and its thirteen hard
     * material dependencies in packaged cooks without a map-owned reference.
     */
    UPROPERTY(VisibleDefaultsOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMesh> DetailedPresentationMesh;

    /** Presentation-only cache; intentionally not SaveGame and contains no unit IDs. */
    UPROPERTY(Transient)
    TArray<FLBOneFactoryPressPresentationItem> ConfiguredItems;

    UPROPERTY(Transient)
    TMap<FName, FTransform> ConfiguredStationTransforms;

    UPROPERTY(Transient)
    FName ConfiguredLayoutId = NAME_None;

    UPROPERTY(Transient)
    int32 ConfiguredLayoutRevision = INDEX_NONE;

    UPROPERTY(Transient)
    bool bPresentationConfigured = false;

    UPROPERTY(Transient)
    int32 ActiveDetailedPresentationIndex = INDEX_NONE;

    TArray<UStaticMeshComponent*> GetDetailedPresentationComponents() const;
    UStaticMeshComponent* GetDetailedPresentationComponent(int32 Index) const;
    static void ConfigureDetailedPresentationComponent(
        UStaticMeshComponent* Component);
    static bool ValidateDetailedMeshAsset(
        const UStaticMesh* Mesh, FString& OutReason);
    static bool BuildDetailedAggregateWorldTransform(
        const FLBOneFactoryPressStarterLayoutState& Layout,
        FTransform& OutWorldTransform, FString& OutReason);
};
