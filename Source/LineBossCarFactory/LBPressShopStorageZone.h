#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBPressShopBuildAuthority.h"
#include "LBPressShopStorageZone.generated.h"

class USceneComponent;
class UBoxComponent;
class UHierarchicalInstancedStaticMeshComponent;
class UMaterialInterface;
class ULBFactoryProcessPortComponent;
class ULBFactoryFloorMarkingComponent;
class UStaticMesh;

USTRUCT(BlueprintType)
struct FLBPressShopStorageZoneSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Version = 4;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName ZoneId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBPressShopStorageType StorageType = ELBPressShopStorageType::BareCoils;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FTransform WorldTransform;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FVector ZoneHalfExtent = FVector::ZeroVector;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Capacity = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Occupancy = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 ReorderPoint = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 ReplenishmentBatchSize = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 MaximumOutstandingReplenishmentLoads = 2;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 RequestedReplenishmentUnits = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 LayoutColumns = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 LayoutRows = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FVector2D StorageUnitPitchCm = FVector2D::ZeroVector;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float BoundaryClearanceCm = 0.0f;
    /** One for legacy/non-stillage stores; three for newly placed panel-stillage stores. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 MaximumStackLevels = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float StackLevelPitchCm = 0.0f;
    /** Explicit visual/physical tier for every occupied unit, in deterministic fill order. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<int32> OccupiedStackLevels;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FName> StoredUnitIds;
};

/** Functional player-built material buffer with explicit logistics interfaces. */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBPressShopStorageZone : public AActor
{
    GENERATED_BODY()

public:
    ALBPressShopStorageZone();

    static constexpr int32 PanelStillageMaximumStackLevels = 3;
    static constexpr float PanelStillageStackPitchCm = 145.0f;
    static constexpr float PanelStillageMinimumZoneHalfHeightCm = 235.0f;

    static bool IsPanelStillageStorageType(ELBPressShopStorageType InStorageType);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Storage")
    bool Configure(FName InZoneId, ELBPressShopStorageType InStorageType,
        int32 InCapacity, const FVector& InHalfExtent);

    /** Configures vertical capacity before ConfigureLayout; legacy/restored zones may remain one-high. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Storage")
    bool ConfigureStacking(int32 InMaximumStackLevels, float InStackLevelPitchCm);

    /** Installs the deterministic slot grid generated from the player's dragged footprint. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Storage")
    bool ConfigureLayout(int32 InColumns, int32 InRows,
        const FVector2D& InStorageUnitPitchCm, float InBoundaryClearanceCm);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Storage")
    bool TryStore(int32 Quantity);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Storage")
    bool TryWithdraw(int32 Quantity);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Storage|Traceability")
    bool TryStoreIdentifiedUnit(FName UnitId);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Storage|Traceability")
    bool TryWithdrawIdentifiedUnit(FName& OutUnitId);

    /** Transactional selector used when only a ready WIP stillage may leave the buffer. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Storage|Traceability")
    bool TryWithdrawIdentifiedUnitById(FName UnitId);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Automatic Replenishment")
    bool ConfigureReplenishment(int32 InReorderPoint, int32 InBatchSize, int32 InMaximumOutstandingLoads = 2);

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Automatic Replenishment")
    int32 GetRequestedReplenishmentUnits() const { return RequestedReplenishmentUnits; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Automatic Replenishment")
    int32 GetOutstandingReplenishmentLoads() const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Automatic Replenishment")
    bool IsStarved() const { return Occupancy == 0; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Automatic Replenishment")
    bool IsBlocked() const { return Capacity > 0 && Occupancy >= Capacity; }

    FLBPressShopStorageZoneSaveState CaptureSaveState() const;
    bool RestoreSaveState(const FLBPressShopStorageZoneSaveState& State);

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Storage")
    int32 GetAvailableCapacity() const { return Capacity - Occupancy; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Storage")
    FName GetZoneId() const { return ZoneId; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Storage")
    ELBPressShopStorageType GetStorageType() const { return StorageType; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Storage")
    int32 GetCapacity() const { return Capacity; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Storage")
    int32 GetOccupancy() const { return Occupancy; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Storage")
    FVector GetZoneHalfExtent() const { return ZoneHalfExtent; }

    /** Green/white bay paint (or red hatch for controlled stores) generated from this footprint. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Storage|Floor Paint")
    ULBFactoryFloorMarkingComponent* GetFloorMarkings() const { return FloorMarkings; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Storage")
    int32 GetLayoutColumns() const { return LayoutColumns; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Storage")
    int32 GetLayoutRows() const { return LayoutRows; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Storage")
    int32 GetFloorPositionCount() const { return LayoutColumns * LayoutRows; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Storage")
    int32 GetMaximumStackLevels() const { return MaximumStackLevels; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Storage")
    float GetStackLevelPitchCm() const { return StackLevelPitchCm; }

    /**
     * Resolves the same compact, tier-major address used by inventory visuals and saves.
     * Index zero is bay one/tier one; after every floor bay, filling continues at
     * bay one/tier two and then bay one/tier three. The returned pad identity is
     * stable across save/reload and is shared by the three vertical tiers at a bay.
     */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Storage|Stacking")
    bool GetStackAddressForStorageIndex(int32 StorageIndex,
        FName& OutStackPadId, int32& OutStackTier) const;

    /** Inverse of GetStackAddressForStorageIndex; rejects foreign or malformed pad IDs. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Storage|Stacking")
    bool GetStorageIndexForStackAddress(FName StackPadId,
        int32 StackTier, int32& OutStorageIndex) const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Storage")
    int32 GetGeneratedStandCount() const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Storage")
    int32 GetVisibleStoredUnitCount() const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Storage|Visuals")
    float GetFirstStandBottomWorldZ() const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Storage|Visuals")
    float GetFirstStoredUnitBottomWorldZ() const;

    /** Test/UI diagnostic for the actual bottom of any visible stored-unit instance. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Storage|Visuals")
    float GetVisibleStoredUnitBottomWorldZ(int32 VisibleUnitIndex) const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Storage|Traceability")
    int32 GetIdentifiedUnitCount() const { return StoredUnitIds.Num(); }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Storage|Traceability")
    bool ContainsIdentifiedUnit(FName UnitId) const { return StoredUnitIds.Contains(UnitId); }

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Factory Builder|Storage")
    TObjectPtr<ULBFactoryProcessPortComponent> IngressPoint;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Factory Builder|Storage")
    TObjectPtr<ULBFactoryProcessPortComponent> EgressPoint;

private:
    UPROPERTY(VisibleAnywhere, Category="Cairnwell|Factory Builder|Storage")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Storage|Traceability")
    TArray<FName> StoredUnitIds;

    UPROPERTY(VisibleAnywhere, Category="Cairnwell|Factory Builder|Storage")
    TObjectPtr<UBoxComponent> ZoneVolume;

    UPROPERTY(VisibleAnywhere, Category="Cairnwell|Factory Builder|Storage|Floor Paint")
    TObjectPtr<ULBFactoryFloorMarkingComponent> FloorMarkings;

    UPROPERTY(VisibleAnywhere, Category="Cairnwell|Factory Builder|Storage|Visuals")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> StandBases;

    UPROPERTY(VisibleAnywhere, Category="Cairnwell|Factory Builder|Storage|Visuals")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> StandSaddles;

    UPROPERTY(VisibleAnywhere, Category="Cairnwell|Factory Builder|Storage|Visuals")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> StoredUnits;

    UPROPERTY(VisibleAnywhere, Category="Cairnwell|Factory Builder|Storage|Visuals")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> StoredLoads;

    UPROPERTY(Transient) TObjectPtr<UStaticMesh> PrimitiveCubeMesh;
    UPROPERTY(Transient) TObjectPtr<UStaticMesh> ApprovedCoilStandMesh;
    UPROPERTY(Transient) TObjectPtr<UStaticMesh> ApprovedWrappedCoilMesh;
    /** Clean low-poly derivative of the supplied Meshy three-high panel stillage. */
    UPROPERTY(Transient) TObjectPtr<UStaticMesh> ApprovedPanelStillageMesh;
    UPROPERTY(Transient) TObjectPtr<UMaterialInterface> FactoryGreenMaterial;
    UPROPERTY(Transient) TObjectPtr<UMaterialInterface> FactoryCharcoalMaterial;
    UPROPERTY(Transient) TObjectPtr<UMaterialInterface> FactoryYellowMaterial;
    UPROPERTY(Transient) TObjectPtr<UMaterialInterface> FactorySteelMaterial;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Storage")
    FName ZoneId = NAME_None;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Storage")
    ELBPressShopStorageType StorageType = ELBPressShopStorageType::BareCoils;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Storage")
    int32 Capacity = 0;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Storage")
    int32 Occupancy = 0;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Automatic Replenishment")
    int32 ReorderPoint = 0;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Automatic Replenishment")
    int32 ReplenishmentBatchSize = 1;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Automatic Replenishment")
    int32 MaximumOutstandingReplenishmentLoads = 2;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Automatic Replenishment")
    int32 RequestedReplenishmentUnits = 0;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Storage")
    FVector ZoneHalfExtent = FVector::ZeroVector;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Storage")
    int32 LayoutColumns = 0;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Storage")
    int32 LayoutRows = 0;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Storage")
    FVector2D StorageUnitPitchCm = FVector2D::ZeroVector;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Storage")
    float BoundaryClearanceCm = 0.0f;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Storage")
    int32 MaximumStackLevels = 1;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Storage")
    float StackLevelPitchCm = 0.0f;

    void EvaluateReplenishmentDemand();
    void RebuildFloorMarkings();
    void RebuildStorageVisuals();
    void RefreshStoredUnitVisuals();
    FVector GetSlotLocation(int32 SlotIndex) const;
};
