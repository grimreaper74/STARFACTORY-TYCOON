#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBFactoryAGVInfrastructure.generated.h"

class UBoxComponent;
class UStaticMeshComponent;
class ULBFactoryFloorMarkingComponent;

UENUM(BlueprintType)
enum class ELBFactoryAGVInfrastructureType : uint8
{
    ChargingStation,
    WaitPoint,
    RouteWaypoint,
    PressTrainHandoff,
    AGVRouteSegment,
    PedestrianWalkway,
    PedestrianCrossing,
    SafetyFence
};

/** Records who owns the current layout without changing the infrastructure's stable id. */
UENUM(BlueprintType)
enum class ELBFactoryInfrastructureProvenance : uint8
{
    PlayerPlaced,
    Automatic,
    PlayerEditedAutomatic
};

USTRUCT(BlueprintType)
struct FLBFactoryAGVInfrastructureSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Version = 2;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName InfrastructureId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBFactoryAGVInfrastructureType Type = ELBFactoryAGVInfrastructureType::RouteWaypoint;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FTransform WorldTransform = FTransform::Identity;
    /** 0-3 for Train A-D handoffs; INDEX_NONE for every other type. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 TrainIndex = INDEX_NONE;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBFactoryInfrastructureProvenance Provenance = ELBFactoryInfrastructureProvenance::PlayerPlaced;
};

/** Saved, player-placeable AGV infrastructure marker. Visual meshes remain replaceable catalogue presentation. */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBFactoryAGVInfrastructure : public AActor
{
    GENERATED_BODY()

public:
    ALBFactoryAGVInfrastructure();

    /** Single dimensional authority shared by placement previews, validation and instances. */
    static FVector GetPlacementHalfExtentForType(ELBFactoryAGVInfrastructureType Type);

    bool Configure(FName InId, ELBFactoryAGVInfrastructureType InType, int32 InTrainIndex = INDEX_NONE);
    FLBFactoryAGVInfrastructureSaveState CaptureSaveState() const;
    bool RestoreSaveState(const FLBFactoryAGVInfrastructureSaveState& State);

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|AGV") FName GetInfrastructureId() const { return InfrastructureId; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|AGV") ELBFactoryAGVInfrastructureType GetInfrastructureType() const { return InfrastructureType; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|AGV") int32 GetTrainIndex() const { return TrainIndex; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|AGV") ELBFactoryInfrastructureProvenance GetProvenance() const { return Provenance; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|AGV") FName GetTrainLabel() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|AGV|Floor Paint") bool HasFloorMarkingPresentation() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|AGV|Floor Paint") FVector GetFloorMarkingDimensionsCm() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Infrastructure") FVector GetPlacementHalfExtentCm() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Infrastructure") UBoxComponent* GetPlacementEnvelope() const { return PlacementEnvelope; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|AGV|Floor Paint") FLinearColor GetFloorMarkingColour() const { return FloorMarkingColour; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|AGV|Floor Paint") ULBFactoryFloorMarkingComponent* GetSafetyMarkings() const { return SafetyMarkings; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|AGV|Selection") UBoxComponent* GetSelectionProxy() const { return SelectionProxy; }

    void MarkAutomaticallyGenerated();
    void MarkPlayerEdited();
    void SetSelectionHighlighted(bool bHighlighted);

private:
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> SceneRoot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> MarkerBody;
    /** Non-colliding paint/decal proxy driven by the saved player placement; never baked as a fixed route. */
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> FloorMarking;
    /** Instanced edges, zebra bars and keep-clear paint layered over the base route tile. */
    UPROPERTY(VisibleAnywhere) TObjectPtr<ULBFactoryFloorMarkingComponent> SafetyMarkings;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> PlacementEnvelope;
    /** Query-only click target. Floor placement traces explicitly filter this actor out. */
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> SelectionProxy;
    UPROPERTY(VisibleInstanceOnly) FLinearColor FloorMarkingColour = FLinearColor(0.0152f, 0.1356f, 0.3763f, 1.0f);
    UPROPERTY(VisibleInstanceOnly) FName InfrastructureId = NAME_None;
    UPROPERTY(VisibleInstanceOnly) ELBFactoryAGVInfrastructureType InfrastructureType = ELBFactoryAGVInfrastructureType::RouteWaypoint;
    UPROPERTY(VisibleInstanceOnly) int32 TrainIndex = INDEX_NONE;
    UPROPERTY(VisibleInstanceOnly) ELBFactoryInfrastructureProvenance Provenance = ELBFactoryInfrastructureProvenance::PlayerPlaced;

    void RefreshProvenanceTags();
};
