#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBBodyShopTypes.h"
#include "LBBodyShopCellActor.generated.h"

class UBoxComponent;
class UHierarchicalInstancedStaticMeshComponent;
class ULBBodyShopPortComponent;
class UMaterialInterface;
class USceneComponent;
class UStaticMesh;
class UStaticMeshComponent;

/**
 * One placeable fixture-based module. Robots are configured only in authored slots;
 * fencing, services, overlays and visual equipment are deterministic children.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBBodyShopCellActor : public AActor
{
    GENERATED_BODY()

public:
    ALBBodyShopCellActor();

    virtual void OnConstruction(const FTransform& Transform) override;

    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Cell")
    bool ConfigureCell(FName InCellId, FName InDefinitionId, FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Cell")
    bool ApplyRobotAssignments(const TArray<FLBBodyShopRobotAssignment>& InAssignments,
        FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Cell")
    bool SetCommissioned(bool bInCommissioned, FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Cell")
    void SetRobotConfigurationOverlayVisible(bool bVisible);

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    FName GetCellId() const { return CellId; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    FName GetDefinitionId() const { return DefinitionId; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    ELBBodyShopCellState GetCellState() const { return CellState; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    bool IsCommissioned() const { return bCommissioned; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    bool IsRobotConfigurationOverlayVisible() const { return bOverlayVisible; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    int32 GetConfiguredRobotCount() const { return RobotAssignments.Num(); }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    int32 GetAuthoredRobotSlotCount() const { return Definition.RobotSlots.Num(); }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    int32 GetAutoAssembledFenceSegmentCount() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    int32 GetAutoAssembledServiceCount() const;

    /** Exact primary presentation path used by visual validation and the build UI. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    FString GetMainPresentationAssetPath() const;

    /** True when the generated safety presentation uses open posts/rails, not opaque walls. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    bool UsesOpenRailSafetyPresentation() const;

    /** Static cell art never owns live skid/workpiece WIP in the underbody fixture. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    bool HasStaticCarrierOrWorkpiecePresentation() const;

    /** Live stillages are runtime WIP and must never be baked into a cell presentation. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    bool HasStaticStillagePresentation() const;

    /** Exact legacy/current mesh-name recognition used by the duplicate-static-WIP guard. */
    static bool IsRuntimeStillagePresentationMeshName(FName MeshName);

    /** True when this cell contributes the automatic skid-conveyor dressing. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    bool HasAutomotiveSkidConveyorPresentation() const;

    /** Local longitudinal span; authored to overlap the connected port positions. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    float GetSkidConveyorPresentationSpanCm() const
    {
        return SkidConveyorPresentationSpanCm;
    }

    /** Centre-to-centre spacing of the two powered roller tracks. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    float GetSkidConveyorTrackGaugeCm() const
    {
        return SkidConveyorTrackGaugeCm;
    }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    int32 GetSkidConveyorStructureInstanceCount() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    int32 GetSkidConveyorRollerInstanceCount() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    int32 GetSkidConveyorSafetyInstanceCount() const;

    /** True when the underbody cell owns its visual-only painted working zone. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    bool HasPaintedUnderbodyWorkZone() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    int32 GetCellFloorWorkingZoneInstanceCount() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    int32 GetCellFloorSafetyMarkingInstanceCount() const;

    /** Clear concrete corridor beneath the continuous skid conveyor. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    float GetCellFloorNeutralConveyorLaneWidthCm() const
    {
        return CellFloorNeutralConveyorLaneWidthCm;
    }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    FLinearColor GetCellFloorWorkingZoneColour() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    FLinearColor GetCellFloorSafetyMarkingColour() const;

    /** False when a required dedicated mesh cannot resolve every semantic material slot. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    bool HasValidPresentationMaterialContract() const
    {
        return bPresentationMaterialContractValid;
    }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    FString GetPresentationMaterialContractFailureReason() const
    {
        return PresentationMaterialContractFailureReason;
    }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    ULBBodyShopPortComponent* FindPort(FName PortId) const;

    const FLBBodyShopCellDefinition& GetDefinition() const { return Definition; }
    const TArray<FLBBodyShopRobotAssignment>& GetRobotAssignments() const
    {
        return RobotAssignments;
    }

    FLBBodyShopPlacedCellSaveState CaptureSaveState() const;
    static bool ValidateSaveState(const FLBBodyShopPlacedCellSaveState& State,
        FString& OutReason);
    bool RestoreSaveState(const FLBBodyShopPlacedCellSaveState& State, FString& OutReason);

    void SetRuntimeState(ELBBodyShopCellState InState, float InProcessProgress01,
        const TArray<FName>& InQueuedWIPIds, FName InActiveWIPId);

    const TArray<FName>& GetQueuedWIPIds() const { return QueuedWIPIds; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    FName GetActiveWIPId() const { return ActiveWIPId; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Cell")
    float GetProcessProgress01() const { return ProcessProgress01; }

private:
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> SceneRoot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> Footprint;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> MaintenanceEnvelope;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> MainPresentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> WorkpiecePresentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> CarrierPresentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> AutoFence;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> AutoServices;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> SkidConveyorStructure;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> SkidConveyorRollers;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> SkidConveyorSafety;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> CellFloorWorkingZone;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> CellFloorSafetyMarking;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> ReachOverlay;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> SweepOverlay;
    UPROPERTY(Transient) TArray<TObjectPtr<ULBBodyShopPortComponent>> Ports;

    UPROPERTY(VisibleInstanceOnly) FName CellId = NAME_None;
    UPROPERTY(VisibleInstanceOnly) FName DefinitionId = NAME_None;
    UPROPERTY(VisibleInstanceOnly) ELBBodyShopCellState CellState = ELBBodyShopCellState::Planned;
    UPROPERTY(VisibleInstanceOnly) bool bCommissioned = false;
    UPROPERTY(VisibleInstanceOnly) bool bOverlayVisible = false;
    UPROPERTY(VisibleInstanceOnly) FLBBodyShopCellDefinition Definition;
    UPROPERTY(VisibleInstanceOnly) TArray<FLBBodyShopRobotAssignment> RobotAssignments;
    UPROPERTY(VisibleInstanceOnly) TArray<FName> QueuedWIPIds;
    UPROPERTY(VisibleInstanceOnly) FName ActiveWIPId = NAME_None;
    UPROPERTY(VisibleInstanceOnly) float ProcessProgress01 = 0.0f;
    UPROPERTY(VisibleInstanceOnly) bool bPresentationMaterialContractValid = true;
    UPROPERTY(VisibleInstanceOnly) FString PresentationMaterialContractFailureReason;
    UPROPERTY(VisibleInstanceOnly) float SkidConveyorPresentationSpanCm = 0.0f;
    UPROPERTY(VisibleInstanceOnly) float SkidConveyorTrackGaugeCm = 0.0f;
    UPROPERTY(VisibleInstanceOnly) float CellFloorNeutralConveyorLaneWidthCm = 0.0f;

    UPROPERTY() TSoftObjectPtr<UStaticMesh> CubeMesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> CylinderMesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> FramingFixtureMesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> VisionGateRuntimeMesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> RobotBaseMesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> SpotToolMesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> PanelPickToolMesh;
    UPROPERTY() TSoftObjectPtr<UMaterialInterface> BaseMaterial;

    void RebuildConfiguredPresentation();
    void RebuildPorts();
    void RebuildAutoSafetyAndServices();
    void RebuildSkidConveyorPresentation(UStaticMesh* Cube, UStaticMesh* Cylinder);
    void RebuildCellFloorPresentation(UStaticMesh* Cube, UMaterialInterface* Material);
    void RebuildOverlays();
    void ConfigurePresentationMesh(UStaticMeshComponent* Component, UStaticMesh* Mesh,
        const FVector& RelativeLocation, const FVector& Scale, const FRotator& Rotation,
        const FLinearColor& Colour, bool bCollision, bool bPreserveSourceMaterials,
        bool bRequireSemanticPalette);
    void AddBoxInstance(UHierarchicalInstancedStaticMeshComponent* Component,
        const FVector& Centre, const FVector& Dimensions, const FRotator& Rotation = FRotator::ZeroRotator);
};
