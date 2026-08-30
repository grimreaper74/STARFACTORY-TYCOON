#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Info.h"
#include "LBBodyShopTypes.h"
#include "LBBodyShopBuildAuthority.generated.h"

class ALBBodyShopCellActor;
class UBoxComponent;
class USceneComponent;

USTRUCT(BlueprintType)
struct FLBBodyShopPortAddress
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite) FName CellId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FName PortId = NAME_None;

    bool IsValid() const { return !CellId.IsNone() && !PortId.IsNone(); }
    FString ToStableString() const { return CellId.ToString() + TEXT("/") + PortId.ToString(); }
    bool operator==(const FLBBodyShopPortAddress& Other) const
    {
        return CellId == Other.CellId && PortId == Other.PortId;
    }
};

USTRUCT(BlueprintType)
struct FLBBodyShopValidationReport
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) bool bValid = false;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TArray<FString> Errors;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TArray<FString> Warnings;
};

/** One authored 100 cm-snap placement used only by the deterministic prototype demo. */
USTRUCT(BlueprintType)
struct FLBBodyShopApprovedLayoutItem
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) FName DefinitionId = NAME_None;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) FTransform WorldTransform = FTransform::Identity;
};

/**
 * Isolated Body Shop placement authority. It owns the experimental build grid and topology
 * only; it never discovers or mutates legacy Press, campaign or composite Body Weld actors.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBBodyShopBuildAuthority : public AInfo
{
    GENERATED_BODY()

public:
    ALBBodyShopBuildAuthority();

    virtual void OnConstruction(const FTransform& Transform) override;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Build")
    float GetPlacementGridCm() const { return PlacementGridCm; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Build")
    FVector GetBuildAreaHalfExtentCm() const { return BuildAreaHalfExtentCm; }

    bool ValidateModulePlacement(FName DefinitionId, const FTransform& Transform,
        FString& OutReason, const ALBBodyShopCellActor* IgnoredCell = nullptr) const;

    /** Read-only reflected placement preflight used by the player preview and runtime validation. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Build")
    void ValidateModulePlacementForValidation(FName DefinitionId, const FTransform& Transform,
        bool& bOutValid, FString& OutReason) const;

    bool PlaceModule(FName DefinitionId, const FTransform& Transform,
        ALBBodyShopCellActor*& OutCell, FString& OutReason);
    bool MoveModule(FName CellId, const FTransform& Transform, FString& OutReason);
    bool RemoveModule(FName CellId, FString& OutReason);

    bool AssignRobotToSlot(FName CellId, FName SlotId, ELBBodyShopRobotRole InRobotRole,
        ELBBodyShopToolType InTool, FString& OutReason);
    bool ClearRobotSlot(FName CellId, FName SlotId, FString& OutReason);

    bool CanConnect(const FLBBodyShopPortAddress& Source, const FLBBodyShopPortAddress& Target,
        FString& OutReason) const;
    bool Connect(const FLBBodyShopPortAddress& Source, const FLBBodyShopPortAddress& Target,
        FName& OutConnectionId, FString& OutReason);
    bool Disconnect(FName ConnectionId, FString& OutReason);

    bool ValidateCommissioning(FName CellId, FLBBodyShopValidationReport& OutReport) const;
    bool CommissionModule(FName CellId, FString& OutReason);
    bool ValidateUnderbodySlice(FLBBodyShopValidationReport& OutReport) const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Build")
    ALBBodyShopCellActor* FindCell(FName CellId) const;

    const TArray<ALBBodyShopCellActor*>& GetPlacedCells() const { return PlacedCells; }

    const TArray<FLBBodyShopConnectionSaveState>& GetConnections() const { return Connections; }

    FLBBodyShopExperimentalSaveState CaptureTopologySaveState() const;
    bool RestoreTopologySaveState(const FLBBodyShopExperimentalSaveState& State,
        FString& OutReason);

    /** Development-only deterministic layout. It places no production cells in the authored map. */
    bool BuildApprovedUnderbodySliceLayout(FString& OutReason);

    /** Pure, testable 100 cm placement contract for the six-cell underbody slice. */
    static TArray<FLBBodyShopApprovedLayoutItem> GetApprovedUnderbodySliceLayout();

private:
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> SceneRoot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> BuildArea;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> PedestrianExclusion;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> FLTRouteExclusion;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> NorthServiceExclusion;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> SouthServiceExclusion;

    UPROPERTY(EditAnywhere, Category="Line Boss|Body Shop|Build", meta=(ClampMin="1.0"))
    float PlacementGridCm = 100.0f;

    UPROPERTY(EditAnywhere, Category="Line Boss|Body Shop|Build")
    FVector BuildAreaHalfExtentCm = FVector(7600.0f, 2600.0f, 1000.0f);

    UPROPERTY(Transient) TArray<TObjectPtr<ALBBodyShopCellActor>> OwnedCells;
    UPROPERTY(Transient) TArray<ALBBodyShopCellActor*> PlacedCells;
    UPROPERTY(VisibleInstanceOnly) TArray<FLBBodyShopConnectionSaveState> Connections;
    UPROPERTY(VisibleInstanceOnly) int32 NextCellSerial = 1;
    UPROPERTY(VisibleInstanceOnly) int32 NextConnectionSerial = 1;

    FName AllocateCellId();
    FName AllocateConnectionId();
    bool IsTransformGridAligned(const FTransform& Transform) const;
    bool IsWithinBuildArea(const FLBBodyShopCellDefinition& Definition,
        const FTransform& Transform) const;
    bool IntersectsProtectedZone(const FBox& FootprintWorld) const;
    bool IntersectsOtherCell(const FLBBodyShopCellDefinition& Definition,
        const FTransform& Transform, const ALBBodyShopCellActor* IgnoredCell) const;
    static FBox GetWorldFootprint(const FLBBodyShopCellDefinition& Definition,
        const FTransform& Transform);
    bool IsEndpointConnected(const FLBBodyShopPortAddress& Address) const;
    bool HasExactConnection(const FName SourceDefinition, const FName SourcePort,
        const FName TargetDefinition, const FName TargetPort) const;
};
