#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBOneFactoryDevStationDressingActor.generated.h"

class UInstancedStaticMeshComponent;
class USceneComponent;

/** One mesh family from the Factory Environment Collection. */
UENUM()
enum class ELBOneFactoryDressingKind : uint8
{
    /** Conveyor sections laid between consecutive stations. */
    Conveyor,
    /** Cell guarding. */
    Fence,
    /** Six-axis robot; mirrored in pairs at weld positions. */
    Robot,
    /** Control cabinet. */
    Control,
    /** Heavy machine: the press line. */
    Press,
    /** Enclosed process module: paint booths. */
    Booth,
    /** Cure oven. */
    Oven,
    /** Parts and material racking. */
    Rack,
    /** Operator bench for trim work. */
    Bench,
    /** Overhead inspection light ramp, placed at quality gates. */
    LampRamp,
    /**
     * The complete v449 press-train visual: the whole accepted v438 Train A as
     * one 306-section mesh, pinned to the Train A datum. Placed once, anchored
     * at the committed ConfigurablePressTrain station transform, exactly as the
     * detailed-press recovery design specifies for the first fidelity release.
     */
    PressTrain,
    /** Wrapped steel coil, for the inbound receiving and coil store rows. */
    Coil,
    /** Adjustable coil stand beneath each stored coil. */
    CoilStand,
    /** Panel stillage, staged at the press dispatch position. */
    Stillage,
    /** Inbound lorry, delivering coils at press receiving. */
    Lorry,
    /** S01 destacker, standing at blank preparation. */
    Destacker,
    /** Native paint kit: pretreatment wash tunnel, on the line. */
    PaintWashTunnel,
    /** Native paint kit: flash-off tunnel, standing in for the ED tunnel. */
    PaintEDTunnel,
    /** Native paint kit: the drive-through spray booth at colour coat. */
    PaintSprayBooth,
    /** Native paint kit: curing oven tunnel at the cure stage. */
    PaintCureOven,
    /** Native paint kit: quality light tunnel at paint inspection. */
    PaintQualityTunnel,
    /** Native paint kit: air extraction module beside the spray booth. */
    PaintAirExtract,
    /** Native paint kit: service set on the booth's service side. */
    PaintServiceSet,
    /** Native assembly kit: skillet carrier under each trim body. */
    AssemblySkillet,
    /** Native assembly kit: sequenced parts cart at trim stations. */
    AssemblyPartsCart,
    /** Native assembly kit: heavy gantry at powertrain marriage. */
    AssemblyMarriageGantry,
    /** Native assembly kit: ergonomic lift platform at rolling chassis. */
    AssemblyLiftPlatform,
    /** Native assembly kit: wheel and tire rack beside rolling chassis. */
    AssemblyWheelRack,
    /** Native assembly kit: end-of-line inspection arch. */
    AssemblyEOLArch,
    /** Native assembly kit: wheel alignment bed at end-of-line. */
    AssemblyAlignmentBed,
    /** Open-box pallet cart, standing in for scrap skips at PR-041. */
    ScrapSkip,
    /** Commissioned model: certified coil-scale platform at PR-002. */
    PressCoilScale,
    /** Commissioned model: the PR-041 scrap baler. */
    PressScrapBaler,
    /** Commissioned model: closure-station panel turntable. */
    WeldClosureTurntable,
    Count
};

/**
 * Dresses each configured station with real machinery from the Factory
 * Environment Collection, composed differently per department so the shops read
 * as different places rather than one repeated cell.
 *
 * The starter presentations are pinned to exact instance counts by contract -
 * 469 for Body/Weld - so this cannot be added there without a versioned v002
 * presentation and regenerated tests. It is added alongside instead, at runtime,
 * and every mesh keeps its own authored materials.
 *
 * Follows the factory visual standard: strong simple silhouettes, no pipe
 * clutter or micro-railings, and nothing placed that does not correspond to a
 * real station or its function.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBOneFactoryDevStationDressingActor : public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryDevStationDressingActor();

    /** Dresses every station in the configured route. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer")
    bool BuildFromRoute(FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Developer")
    int32 GetDressedStationCount() const { return DressedStations; }

    static FName GetDressingTag();

private:
    void Place(ELBOneFactoryDressingKind Kind, const FVector& Where,
        const FQuat& Rotation, double UniformScale = 1.0);

    UPROPERTY()
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY()
    TArray<TObjectPtr<UInstancedStaticMeshComponent>> Batches;

    /** The project's own seven-joint robot; all joints share one baked
        transform. Replaces the pack robot in every dressing spawn
        (owner, 2026-08-20: 'wrong robots not our own'). */
    UPROPERTY()
    TArray<TObjectPtr<UInstancedStaticMeshComponent>> RobotJointBatches;

    UPROPERTY()
    TObjectPtr<class UMaterialInstanceDynamic> RouteMaterial;

    /**
     * Components created per build (train meshes, apron, flow route) rather
     * than in the constructor. Destroyed and recreated on rebuild, so the
     * console rebuild path never NewObjects over a live registered component.
     */
    UPROPERTY()
    TArray<TObjectPtr<UActorComponent>> DynamicPieces;

    int32 DressedStations = 0;
    int32 PieceCount = 0;
};
