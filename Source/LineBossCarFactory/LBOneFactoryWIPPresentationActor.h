#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBOneFactoryProductionFlow.h"
#include "LBOneFactoryWIPPresentationActor.generated.h"

class ALBOneFactoryRuntimeCoordinator;
class UInstancedStaticMeshComponent;
class UMaterialInstanceDynamic;
class USceneComponent;
struct FLBOneFactoryRuntimeStationStep;

/**
 * Visual families for work in progress. Each value maps to one instanced
 * batch, so a unit's appearance changes as it earns its next stage.
 */
UENUM(BlueprintType)
enum class ELBOneFactoryWIPVisual : uint8
{
    /** Inbound steel coil, before anything has been cut. */
    Coil,
    /** Cut blanks and pressed panels waiting in stillage. */
    PanelStack,
    /** Bare welded shell: body framing through body inspection. */
    BodyInWhite,
    /** Pretreated and e-coated shell, before colour. */
    PrimedBody,
    /** Colour coat through paint inspection. */
    PaintedBody,
    /** Trimmed and married car through dispatch. */
    FinishedCar
};

/**
 * Presentation-only view of the production ledger.
 *
 * The OneFactory production-flow contract states that a WIP presentation actor
 * "reads the ledger and binds the clean-room VehicleWIPNativeKit_v001 layers.
 * It owns no genealogy and is never saved." This is that actor.
 *
 * It creates no logical WIP, allocates no UnitId, and writes nothing back. It
 * reads `CaptureLedger()` plus the coordinator's configured route, and draws one
 * instance per live unit at its current station. If the ledger disagrees with
 * the route it simply draws less, never more.
 *
 * The batches resolve the authored meshes: the wrapped coil, the panel
 * stillage, the body-in-white skeleton, the ED-coated and painted Cairnwell
 * shells and the finished car. Plain instanced components are used rather
 * than hierarchical ones deliberately - the batches are rebuilt whenever the
 * ledger's membership changes, and an HISM's async cluster tree never settles
 * under that pattern.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBOneFactoryWIPPresentationActor : public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryWIPPresentationActor();

    virtual void Tick(float DeltaSeconds) override;

    /** Rebuilds every instance from the live ledger. Safe to call each frame. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|WIP")
    bool RefreshFromLedger(FString& OutReason);

    /** Removes every instance without touching any authority. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|WIP")
    void ClearPresentation();

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|WIP")
    int32 GetVisibleUnitCount() const { return VisibleUnitCount; }

    /** This actor is a view of WIP; it is never the authority for it. */
    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|WIP")
    static bool OwnsProcessWIP() { return false; }

    static ELBOneFactoryWIPVisual VisualForStage(
        ELBOneFactoryVehicleStage Stage);

    static FName GetPresentationTag();

private:
    UPROPERTY()
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY()
    TArray<TObjectPtr<UInstancedStaticMeshComponent>> Batches;
    /** FinishedCar units also render rolling gear, so a car leaving GA
     *  stops looking identical to the painted shell entering it. */
    UPROPERTY() TObjectPtr<UInstancedStaticMeshComponent> GearBatch;

    UPROPERTY()
    TArray<TObjectPtr<UMaterialInstanceDynamic>> BatchMaterials;

    /**
     * Places one unit. While a station cycles the car stands on it; over the
     * last fifth of the cycle it slides to the next station, so the line reads
     * as flowing rather than teleporting. A unit held at a quality gate does not
     * drift: it waits where it is until a result is submitted.
     */
    bool ComputeUnitTransform(
        const TArray<FLBOneFactoryRuntimeStationStep>& Route,
        const TMap<FName, FTransform>& StationTransforms,
        ALBOneFactoryRuntimeCoordinator* Coordinator,
        const FLBOneFactoryVehicleUnitState& Unit,
        FTransform& OutTransform) const;

    /**
     * Where each live unit's instance sits, so a car can be moved every frame
     * without rebuilding the batches. Membership changes rarely; position
     * changes constantly.
     */
    struct FInstanceRef
    {
        FName UnitId;
        int32 BatchIndex = INDEX_NONE;
        int32 InstanceIndex = INDEX_NONE;
    };
    TArray<FInstanceRef> InstanceRefs;

    bool bMaterialsResolved = false;
    bool bHasBuiltOnce = false;
    uint32 LastSignature = 0;
    int32 VisibleUnitCount = 0;
    int32 LastLoggedUnitCount = INDEX_NONE;
};
