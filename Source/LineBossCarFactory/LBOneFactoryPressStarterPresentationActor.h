#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBOneFactoryPressStarterLayout.h"
#include "LBOneFactoryPressStarterPresentationActor.generated.h"

class USceneComponent;
class UStaticMesh;
class UStaticMeshComponent;
class UInstancedStaticMeshComponent;
class UMaterialInterface;
class UTextRenderComponent;

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
 * Visual-only materialisation of a native, modular S01-S07 press train.
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

    virtual void Tick(float DeltaSeconds) override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

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

    /** Semantic visual bundles after commit; zero while never configured/cleared. */
    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    int32 GetVisualBatchCount() const;

    /** Native Unreal motion rig: S01, S02-S06, transfer and S07 mechanisms. */
    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    int32 GetAnimatedMechanismCount() const;

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    bool IsMechanismAnimationActive() const { return bMechanismAnimationActive; }

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

    /** Exact legacy aggregate/material closure plus authored runtime modules. */
    static TArray<FSoftObjectPath> GetRequiredNativeAssetPaths();

    /** Exact local class and owned native asset closure contract. */
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
     * Visible authored S02 modules. They are intentionally outside the
     * two-element legacy staging-buffer API: that API remains an exact rollback
     * invariant. The Ram reuses the existing PressRam_02 motion seam.
     */
    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMeshComponent> S02DeepDrawPresentation;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMeshComponent> S02DeepDrawBlankholderPresentation;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMeshComponent> S02DeepDrawBolsterPresentation;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMeshComponent> S02DeepDrawFlywheelPresentation;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMeshComponent> S02DeepDrawSafetyGatePresentation;

    /**
     * Static, source-provenanced S03-S06 station packages.  Each station has
     * one frame and one operator-side cue component at the same authored root;
     * the shared slide/bolster/die exports remain deliberately unbound until
     * authored in-press poses are supplied.
     */
    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Presentation")
    TArray<TObjectPtr<UStaticMeshComponent>> S03S06StagePackFrames;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Presentation")
    TArray<TObjectPtr<UStaticMeshComponent>> S03S06StagePackCues;

    /**
     * Native MaterialFlow v002 endpoint dressing.  These ten source-provenanced
     * components replace the generic S01/S07 placeholder shells only when the
     * exact UE-native asset closure has bound successfully.  The two mover
     * meshes retain their authored pivots and documented parked offsets; they
     * deliberately do not join the existing eleven-mechanism animation array.
     */
    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMeshComponent> S01CoilCartMover;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMeshComponent> S01CoilRackPresentation;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMeshComponent> S01DecoilerBasePresentation;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMeshComponent> S01DecoilerSpindleMover;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMeshComponent> S01StraightenerFeedPresentation;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMeshComponent> S01FeedBridgePresentation;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMeshComponent> S07ExitConveyorBeltPresentation;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMeshComponent> S07ExitConveyorFramePresentation;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMeshComponent> S07InspectionCellPresentation;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMeshComponent> S07OutboundDunnagePresentation;

    /**
     * Native-CDO hard reference: keeps the exact aggregate and its thirteen hard
     * material dependencies in packaged cooks without a map-owned reference.
     */
    UPROPERTY(VisibleDefaultsOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMesh> DetailedPresentationMesh;

    /** Cooked, hand-authored S02 RuntimePrep v003 module references. */
    UPROPERTY(VisibleDefaultsOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMesh> S02DeepDrawStaticMesh;

    UPROPERTY(VisibleDefaultsOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMesh> S02DeepDrawRamMesh;

    UPROPERTY(VisibleDefaultsOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMesh> S02DeepDrawBlankholderMesh;

    UPROPERTY(VisibleDefaultsOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMesh> S02DeepDrawBolsterMesh;

    UPROPERTY(VisibleDefaultsOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMesh> S02DeepDrawFlywheelMesh;

    UPROPERTY(VisibleDefaultsOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UStaticMesh> S02DeepDrawSafetyGateMesh;

    /**
     * The v003 PBR master and its per-module material instances are held as
     * CDO hard references so every texture/AO dependency is present in a cook
     * without relying on a map-owned component override.
     */
    UPROPERTY(VisibleDefaultsOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UMaterialInterface> S02DeepDrawMaterialMaster;

    UPROPERTY(VisibleDefaultsOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    TArray<TObjectPtr<UMaterialInterface>> S02DeepDrawMaterialLibrary;

    /** Cooked, static-only S03-S06 StagePack RuntimePrep v001 mesh closure. */
    UPROPERTY(VisibleDefaultsOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    TArray<TObjectPtr<UStaticMesh>> S03S06StagePackFrameMeshes;

    UPROPERTY(VisibleDefaultsOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    TArray<TObjectPtr<UStaticMesh>> S03S06StagePackCueMeshes;

    /** Shared PBR master plus one semantic material instance per supplied family. */
    UPROPERTY(VisibleDefaultsOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    TObjectPtr<UMaterialInterface> S03S06StagePackMaterialMaster;

    UPROPERTY(VisibleDefaultsOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    TArray<TObjectPtr<UMaterialInterface>> S03S06StagePackMaterialLibrary;

    /** Cooked UE-native MaterialFlow v002 mesh and material closure. */
    UPROPERTY(VisibleDefaultsOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    TArray<TObjectPtr<UStaticMesh>> MaterialFlowMeshLibrary;

    UPROPERTY(VisibleDefaultsOnly,
        Category="Line Boss|OneFactory|Press Starter|Presentation")
    TArray<TObjectPtr<UMaterialInterface>> MaterialFlowMaterialLibrary;

    /** Native modular train: press shells, transfer, services, access and labels. */
    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Native Train")
    TObjectPtr<UInstancedStaticMeshComponent> StationBases;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Native Train")
    TObjectPtr<UInstancedStaticMeshComponent> StationColumns;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Native Train")
    TObjectPtr<UInstancedStaticMeshComponent> StationCrowns;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Native Train")
    TObjectPtr<UInstancedStaticMeshComponent> StationTables;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Native Train")
    TObjectPtr<UInstancedStaticMeshComponent> SafetyFrames;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Native Train")
    TObjectPtr<UInstancedStaticMeshComponent> TransferRails;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Native Train")
    TObjectPtr<UInstancedStaticMeshComponent> ServiceRuns;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Native Train")
    TObjectPtr<UInstancedStaticMeshComponent> AccessPlatforms;

    /** Operator-side HMI pedestals, one per station. */
    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Native Train")
    TObjectPtr<UInstancedStaticMeshComponent> ControlKiosks;

    /** Yellow stack-light columns make the running train readable at distance. */
    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Native Train")
    TObjectPtr<UInstancedStaticMeshComponent> SignalLights;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Starter|Native Train")
    TArray<TObjectPtr<UTextRenderComponent>> StationLabels;

    /**
     * Deliberately separate, movable Unreal components.  The detailed press body
     * is a retained native aggregate, while these are the first production-ready
     * animation seam for the S02-S06 rams and the panel transfer system shown in
     * the supplied Cairnwell reference sheets.
     */
    UPROPERTY(VisibleAnywhere,
        Category="Line Boss|OneFactory|Press Starter|Motion")
    TObjectPtr<UStaticMeshComponent> TransferCarriage;

    UPROPERTY(VisibleAnywhere,
        Category="Line Boss|OneFactory|Press Starter|Motion")
    TObjectPtr<UStaticMeshComponent> TransferBeam;

    UPROPERTY(VisibleAnywhere,
        Category="Line Boss|OneFactory|Press Starter|Motion")
    TObjectPtr<UStaticMeshComponent> TransferGripperFrame;

    UPROPERTY(VisibleAnywhere,
        Category="Line Boss|OneFactory|Press Starter|Motion")
    TObjectPtr<UStaticMeshComponent> DestackLift;

    UPROPERTY(VisibleAnywhere,
        Category="Line Boss|OneFactory|Press Starter|Motion")
    TObjectPtr<UStaticMeshComponent> UnloadRobotArm;

    UPROPERTY(VisibleAnywhere,
        Category="Line Boss|OneFactory|Press Starter|Motion")
    TObjectPtr<UStaticMeshComponent> UnloadRobotGripper;

    UPROPERTY(VisibleAnywhere,
        Category="Line Boss|OneFactory|Press Starter|Motion")
    TArray<TObjectPtr<UStaticMeshComponent>> PressRams;

    UPROPERTY(Transient)
    TObjectPtr<UStaticMesh> MotionPrimitiveMesh;

    UPROPERTY(Transient)
    TArray<FTransform> MechanismRestTransforms;

    UPROPERTY(Transient)
    bool bMechanismAnimationActive = false;

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
    TArray<UStaticMeshComponent*> GetS02DeepDrawPresentationComponents() const;
    TArray<UStaticMeshComponent*> GetS03S06StagePackPresentationComponents() const;
    TArray<UStaticMeshComponent*> GetMaterialFlowPresentationComponents() const;
    static void ConfigureDetailedPresentationComponent(
        UStaticMeshComponent* Component);
    static void ConfigureMotionComponent(UStaticMeshComponent* Component);
    static void ConfigureNativeBatchComponent(UInstancedStaticMeshComponent* Component);
    void ConfigureNativeTrainModules();
    void ClearNativeTrainModules();
    TArray<UStaticMeshComponent*> GetMotionComponents() const;
    void ConfigureMechanismAnimation(const FTransform& S02DeepDrawWorldTransform);
    void ClearMechanismAnimation();
    void EnsureS02DeepDrawRuntimeVisibility();
    void ApplyS02DeepDrawMaterialBindings(UStaticMeshComponent* Component) const;
    void EnsureS03S06StagePackRuntimeVisibility();
    void ApplyS03S06StagePackMaterialBindings(UStaticMeshComponent* Component) const;
    bool IsS03S06StagePackStationReady(int32 StationIndex) const;
    void EnsureMaterialFlowRuntimeVisibility();
    bool IsMaterialFlowStationReady(bool bS01) const;
    static bool ValidateDetailedMeshAsset(
        const UStaticMesh* Mesh, FString& OutReason);
    static bool ValidateS02DeepDrawMeshAssets(
        const UStaticMesh* StaticMesh, const UStaticMesh* RamMesh,
        const UStaticMesh* BlankholderMesh, const UStaticMesh* BolsterMesh,
        const UStaticMesh* FlywheelMesh, const UStaticMesh* SafetyGateMesh,
        FString& OutReason);
    static bool ValidateS02DeepDrawMaterialAssets(
        const UMaterialInterface* Master,
        const TArray<TObjectPtr<UMaterialInterface>>& Materials,
        FString& OutReason);
    static bool ValidateS03S06StagePackMaterialAssets(
        const UMaterialInterface* Master,
        const TArray<TObjectPtr<UMaterialInterface>>& Materials,
        FString& OutReason);
    static bool ValidateMaterialFlowMeshAssets(
        const TArray<TObjectPtr<UStaticMesh>>& Meshes, FString& OutReason);
    static bool ValidateMaterialFlowMaterialAssets(
        const TArray<TObjectPtr<UMaterialInterface>>& Materials,
        FString& OutReason);
    static bool BuildDetailedAggregateWorldTransform(
        const FLBOneFactoryPressStarterLayoutState& Layout,
        FTransform& OutWorldTransform, FString& OutReason);
    static bool BuildS02DeepDrawWorldTransform(
        const FLBOneFactoryPressStarterLayoutState& Layout,
        FTransform& OutWorldTransform, FString& OutReason);
    static bool BuildS02DeepDrawModuleWorldTransform(
        const FTransform& CellWorldTransform, const FVector& ModulePlacementCm,
        FTransform& OutWorldTransform, FString& OutReason);
    static bool BuildMaterialFlowStationWorldTransforms(
        const FLBOneFactoryPressStarterLayoutState& Layout,
        FTransform& OutS01WorldTransform, FTransform& OutS07WorldTransform,
        FString& OutReason);
    static bool BuildMaterialFlowMoverWorldTransform(
        const FTransform& StationWorldTransform, const FVector& ParkedOffsetCm,
        FTransform& OutWorldTransform, FString& OutReason);
};
