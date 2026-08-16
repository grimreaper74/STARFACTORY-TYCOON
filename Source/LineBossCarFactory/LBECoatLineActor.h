#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBBodyWeldLineActor.h"
#include "UObject/SoftObjectPtr.h"
#include "LBECoatLineActor.generated.h"

class UBoxComponent;
class ULBFactoryFloorMarkingComponent;
class ULBFactoryProcessPortComponent;
class ULBStatusBeaconComponent;
class UHierarchicalInstancedStaticMeshComponent;
class UMaterialInterface;
class UPointLightComponent;
class URectLightComponent;
class USceneComponent;
class USpotLightComponent;
class UStaticMesh;
class UStaticMeshComponent;

/** The production meaning of one logical process bay in the ED / e-coat line. */
UENUM(BlueprintType)
enum class ELBECoatBayType : uint8
{
    Degrease,
    Rinse1,
    Phosphate,
    Rinse2,
    EDCoat,
    UFRinse,
    DrainInspection,
    OvenEntry,
    OvenCure,
    OvenExit
};

/** High-level line authority. Bay flags provide the more precise reason for a stop. */
UENUM(BlueprintType)
enum class ELBECoatOperatingState : uint8
{
    Stopped,
    Starting,
    Running,
    Paused,
    Starved,
    Faulted,
    Maintenance,
    EmergencyStop
};

/** Readable carrier stages used by animation, audio, effects, UI and automation. */
UENUM(BlueprintType)
enum class ELBECoatCarrierStage : uint8
{
    DryTravel,
    Descending,
    Immersed,
    Rising,
    Draining,
    OvenEntry,
    OvenCure,
    OvenExit,
    Complete
};

USTRUCT(BlueprintType)
struct FLBECoatBayDescriptor
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) int32 BayIndex = INDEX_NONE;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) FName BayId = NAME_None;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) ELBECoatBayType BayType = ELBECoatBayType::Degrease;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) float StartXCm = 0.0f;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) float EndXCm = 0.0f;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) bool bHasLiquid = false;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) bool bEnclosed = false;
};

USTRUCT(BlueprintType)
struct FLBECoatBayOperatingState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 BayIndex = INDEX_NONE;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bEnabled = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bFaulted = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bStarved = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float ProcessValue01 = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float TemperatureC = 20.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float LiquidLevel01 = 1.0f;
};

USTRUCT(BlueprintType)
struct FLBECoatCarrierPose
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) float DistanceCm = 0.0f;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) int32 BayIndex = INDEX_NONE;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) ELBECoatCarrierStage Stage = ELBECoatCarrierStage::DryTravel;
    /** Exact trolley pose on the overhead rail. Treatment rails dip with the body. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) FVector TrolleyRootLocationCm = FVector::ZeroVector;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) FRotator TrolleyRotation = FRotator::ZeroRotator;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) FVector BodyRootLocationCm = FVector::ZeroVector;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) FRotator BodyRotation = FRotator::ZeroRotator;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) float Immersion01 = 0.0f;
};

USTRUCT(BlueprintType)
struct FLBECoatCarrierSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName CarrierId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float DistanceCm = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bEnabled = true;
    /** False only for legacy/proxy carriers created before exact weld-to-ED lineage existed. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bHasBodyInWhite = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FLBBodyInWhiteRecord BodyInWhite;
};

USTRUCT(BlueprintType)
struct FLBECoatLineSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Version = 3;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName LineId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FTransform WorldTransform = FTransform::Identity;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBECoatOperatingState OperatingState = ELBECoatOperatingState::Stopped;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName StateReason = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float TargetLineSpeedCmPerSecond = 75.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bLoopCarriers = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FLBECoatBayOperatingState> BayStates;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FLBECoatCarrierSaveState> Carriers;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FLBECoatOperatingStateChanged,
    ELBECoatOperatingState, PreviousState, ELBECoatOperatingState, NewState, FName, Reason);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_FourParams(FLBECoatCarrierStageChanged,
    FName, CarrierId, int32, BayIndex, ELBECoatCarrierStage, PreviousStage,
    ELBECoatCarrierStage, NewStage);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_FiveParams(FLBECoatBayStateChanged,
    int32, BayIndex, ELBECoatBayType, BayType, bool, bEnabled, bool, bFaulted, bool, bStarved);

USTRUCT()
struct FLBECoatCarrierRuntimeEntry
{
    GENERATED_BODY()

    UPROPERTY() FLBECoatCarrierSaveState State;
    UPROPERTY(Transient) TObjectPtr<USceneComponent> PresentationRoot;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Trolley;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Hoist;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Hanger;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> VehicleBody;
    UPROPERTY(Transient) int32 LastBayIndex = INDEX_NONE;
    UPROPERTY(Transient) ELBECoatCarrierStage LastStage = ELBECoatCarrierStage::DryTravel;
};

/**
 * Runtime authority for the complete modular 189 m ED / e-coat line.
 *
 * The actor's local origin is the line entry at finished-floor Z=0. Production flows in +X.
 * The six liquid-process bays are 1800 cm long and use two reusable 900 cm visual modules.
 * The drain and eight oven modules retain the 900 cm production pitch. Until final assets are
 * imported, low-cost engine primitives preserve all gameplay datums, dipping rails, liquids,
 * carrier poses and placement bounds.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBECoatLineActor : public AActor
{
    GENERATED_BODY()

public:
    ALBECoatLineActor();

    virtual void OnConstruction(const FTransform& Transform) override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Paint Shop|ED Line")
    bool Configure(FName InLineId);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Paint Shop|ED Line")
    void RebuildLineVisuals();

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Paint Shop|ED Line|State")
    bool SetOperatingState(ELBECoatOperatingState NewState, FName Reason = NAME_None);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Paint Shop|ED Line|State")
    bool SetBayOperatingState(int32 BayIndex, bool bEnabled, bool bFaulted,
        bool bStarved, float ProcessValue01, float TemperatureC);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Paint Shop|ED Line|State")
    bool SetLiquidLevel01(int32 TreatmentBayIndex, float NewLevel01);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Paint Shop|ED Line|Carrier")
    bool AddCarrier(FName CarrierId, float InitialDistanceCm = 0.0f);

    /**
     * Atomically accepts one quality-approved weld body into an ED carrier and acknowledges
     * the source line. Every validation runs before either actor mutates; a failed weld
     * acknowledgement rolls the ED actor back to its byte-equivalent pre-call state.
     */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Paint Shop|ED Line|Flow")
    bool AcceptAndAcknowledgeBodyInWhite(ALBBodyWeldLineActor* SourceLine,
        FName BodyId, FName CarrierId, FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Paint Shop|ED Line|Carrier")
    bool RemoveCarrier(FName CarrierId);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Paint Shop|ED Line|Carrier")
    void ClearCarriers();

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Paint Shop|ED Line|Carrier")
    bool SetCarrierProgress(FName CarrierId, float DistanceCm);

    /** Deterministic simulation entry point used by Tick, replay, automation and time controls. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Paint Shop|ED Line|Carrier")
    void AdvanceSimulation(float DeltaSeconds);

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Carrier")
    bool EvaluateCarrierPoseAtDistance(float DistanceCm, FLBECoatCarrierPose& OutPose) const;

    /** Samples the continuous rollercoaster rail used by both trolley presentation and tests. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Carrier")
    bool EvaluateTrackPoseAtDistance(float DistanceCm, FVector& OutTrolleyLocationCm,
        FRotator& OutTrolleyRotation) const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Carrier")
    bool GetCarrierState(FName CarrierId, FLBECoatCarrierSaveState& OutState) const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Carrier")
    bool GetCarrierBodyInWhite(FName CarrierId, FLBBodyInWhiteRecord& OutBody) const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Layout")
    bool GetBayDescriptor(int32 BayIndex, FLBECoatBayDescriptor& OutDescriptor) const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|State")
    bool GetBayOperatingState(int32 BayIndex, FLBECoatBayOperatingState& OutState) const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|State")
    bool GetLiquidSurfacePresentation(int32 TreatmentBayIndex,
        FVector& OutActorLocalLocation, bool& bOutVisible) const;

    /** Computes stable module and service socket transforms without requiring imported mesh sockets. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Layout")
    bool GetBaySocketTransform(int32 BayIndex, FName SocketSemantic,
        FTransform& OutActorLocalTransform) const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Layout")
    FName GetLineId() const { return LineId; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Layout")
    int32 GetBayCount() const { return BayDescriptors.Num(); }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Layout")
    int32 GetTreatmentBayCount() const { return TreatmentBayCount; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Layout")
    int32 GetOvenProcessBayCount() const { return OvenProcessBayCount; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Layout")
    int32 GetCarrierCount() const { return Carriers.Num(); }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Layout")
    int32 GetLiquidSurfaceCount() const { return LiquidSurfaces.Num(); }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Layout")
    int32 GetTreatmentVisualModuleCount() const { return TreatmentBayCount * TreatmentModulesPerBay; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Layout")
    int32 GetPhysicalVisualModuleCount() const { return TreatmentBayCount * TreatmentModulesPerBay + 1 + 8; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Layout")
    int32 GetBuiltTreatmentVisualInstanceCount() const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Layout")
    int32 GetBuiltRailSegmentInstanceCount() const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Layout")
    float GetModulePitchCm() const { return ModulePitchCm; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Layout")
    float GetTotalLengthCm() const { return TotalLengthCm; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Layout")
    FVector GetProtectedEnvelopeHalfExtentCm() const { return ProtectedEnvelopeHalfExtentCm; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Layout")
    FVector GetProtectedEnvelopeRelativeCentreCm() const { return ProtectedEnvelopeRelativeCentreCm; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Layout")
    UBoxComponent* GetProtectedEnvelope() const { return ProtectedEnvelope; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Layout")
    ULBFactoryFloorMarkingComponent* GetFloorMarkings() const { return FloorMarkings; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Flow")
    ULBFactoryProcessPortComponent* GetInputPort() const { return InputPort; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Flow")
    ULBFactoryProcessPortComponent* GetOutputPort() const { return OutputPort; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|State")
    ELBECoatOperatingState GetOperatingState() const { return OperatingState; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|State")
    FName GetStateReason() const { return StateReason; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Operations")
    ULBStatusBeaconComponent* GetEntryBeacon() const { return EntryBeacon; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Operations")
    ULBStatusBeaconComponent* GetExitBeacon() const { return ExitBeacon; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Operations")
    int32 GetTreatmentServiceLightCount() const { return TreatmentServiceLights.Num(); }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Operations")
    int32 GetOvenInteriorLightCount() const { return OvenInteriorLights.Num(); }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Operations")
    int32 GetPortalSpotLightCount() const { return PortalSpotLights.Num(); }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Operations")
    int32 GetOvenFanCount() const { return OvenFans.Num(); }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Operations")
    float GetFanRotationDegrees() const { return FanRotationDegrees; }

    /** Testable truth: only a lineage-backed carrier may expose a vehicle body mesh. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Carrier")
    bool IsCarrierBodyPresented(FName CarrierId) const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Operations")
    bool AreOperationalLightsRegisteredAndVisible() const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Paint Shop|ED Line|Persistence")
    FLBECoatLineSaveState CaptureSaveState() const;

    /** Pure contract gate shared by actor restore and whole-campaign preflight. */
    static bool IsSaveStateContractValid(const FLBECoatLineSaveState& State);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Paint Shop|ED Line|Persistence")
    bool RestoreSaveState(const FLBECoatLineSaveState& State);

    UPROPERTY(BlueprintAssignable, Category="Cairnwell|Paint Shop|ED Line|Events")
    FLBECoatOperatingStateChanged OnOperatingStateChanged;

    UPROPERTY(BlueprintAssignable, Category="Cairnwell|Paint Shop|ED Line|Events")
    FLBECoatCarrierStageChanged OnCarrierStageChanged;

    UPROPERTY(BlueprintAssignable, Category="Cairnwell|Paint Shop|ED Line|Events")
    FLBECoatBayStateChanged OnBayStateChanged;

    /** Whole-body process ports used by automatic factory flow linking. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Flow")
    TObjectPtr<ULBFactoryProcessPortComponent> InputPort;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Flow")
    TObjectPtr<ULBFactoryProcessPortComponent> OutputPort;

    /** Exact line speed; external time controls should call AdvanceSimulation with scaled delta time. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Paint Shop|ED Line|Simulation",
        meta=(ClampMin="1.0", ClampMax="1000.0", Units="cm/s"))
    float TargetLineSpeedCmPerSecond = 75.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Paint Shop|ED Line|Simulation")
    bool bLoopCarriers = false;

    /** If true, unresolved soft mesh references are loaded when visuals are rebuilt. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Paint Shop|ED Line|Visuals")
    bool bLoadReferencedMeshesSynchronously = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Visuals")
    TSoftObjectPtr<UStaticMesh> TreatmentBayMesh;
    /** Rail-free second half of each 18 m vessel; paired with TreatmentBayMesh at X+1350 cm. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Visuals")
    TSoftObjectPtr<UStaticMesh> TreatmentBayEndMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Visuals")
    TSoftObjectPtr<UStaticMesh> DrainInspectionMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Visuals")
    TSoftObjectPtr<UStaticMesh> OvenEntryMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Visuals")
    TSoftObjectPtr<UStaticMesh> OvenProcessBayMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Visuals")
    TSoftObjectPtr<UStaticMesh> OvenExitMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Visuals")
    TSoftObjectPtr<UStaticMesh> OverheadRailModuleMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Visuals")
    TSoftObjectPtr<UStaticMesh> LiquidSurfaceMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Visuals")
    TSoftObjectPtr<UStaticMesh> CarrierTrolleyMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Visuals")
    TSoftObjectPtr<UStaticMesh> CarrierHoistMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Visuals")
    TSoftObjectPtr<UStaticMesh> CarrierHangerMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Visuals")
    TSoftObjectPtr<UStaticMesh> VehicleShellMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Visuals")
    TSoftObjectPtr<UStaticMesh> OvenFanMesh;
    /** Optional future rotor-only mesh; the imported fan assembly remains a static housing. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Visuals")
    TSoftObjectPtr<UStaticMesh> OvenFanRotorMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Visuals")
    TSoftObjectPtr<UStaticMesh> OvenServiceDoorMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Visuals")
    TSoftObjectPtr<UStaticMesh> OvenServiceLightHousingMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Visuals")
    TSoftObjectPtr<UStaticMesh> BeaconBaseMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Visuals")
    TSoftObjectPtr<UStaticMesh> BeaconGreenLensMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Visuals")
    TSoftObjectPtr<UStaticMesh> BeaconAmberLensMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Visuals")
    TSoftObjectPtr<UStaticMesh> BeaconRedLensMesh;
    /** Per-process liquid materials in treatment-bay order; surfaces remain separate components. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Paint Shop|ED Line|Visuals")
    TArray<TSoftObjectPtr<UMaterialInterface>> TreatmentLiquidMaterials;

private:
    static constexpr int32 TreatmentBayCount = 6;
    static constexpr int32 TreatmentModulesPerBay = 2;
    static constexpr int32 OvenProcessBayCount = 6;
    static constexpr int32 OvenVisualModuleCount = OvenProcessBayCount + 2;
    static constexpr int32 TotalBayCount = 15;
    static constexpr float ModulePitchCm = 900.0f;
    static constexpr float TreatmentBayLengthCm = 1800.0f;
    static constexpr float TreatmentSectionLengthCm = TreatmentBayCount * TreatmentBayLengthCm;
    static constexpr float DrainInspectionLengthCm = ModulePitchCm;
    static constexpr float OvenSectionStartCm = TreatmentSectionLengthCm + DrainInspectionLengthCm;
    static constexpr float TotalLengthCm = 18900.0f;
    static constexpr float LegacyTotalLengthCm = 13500.0f;
    static constexpr float RailOffsetYCm = 300.0f;
    static constexpr float RailHeightCm = 800.0f;
    static constexpr float TreatmentLowRailHeightCm = 545.0f;
    static constexpr float HangerRootZCm = 735.0f;
    static constexpr float TankRimZCm = 305.0f;
    static constexpr float LiquidSurfaceZCm = 285.0f;
    static constexpr float DryBodyRootZCm = 430.0f;
    static constexpr float DescendBodyRootZCm = 335.0f;
    static constexpr float DippedBodyRootZCm = 175.0f;
    static const FVector ProtectedEnvelopeHalfExtentCm;
    static const FVector ProtectedEnvelopeRelativeCentreCm;

    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> SceneRoot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> ProtectedEnvelope;
    UPROPERTY(VisibleAnywhere) TObjectPtr<ULBFactoryFloorMarkingComponent> FloorMarkings;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> StructureInstances;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> RailInstances;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> TreatmentModuleInstances;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> TreatmentEndModuleInstances;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> TankFallbackInstances;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> CatwalkFallbackInstances;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> DrainInspectionPresentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> OvenProcessInstances;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> OvenEntryPresentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> OvenExitPresentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> OvenFallbackInstances;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> OvenServiceDoorInstances;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> OvenServiceLightHousingInstances;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> OvenFanHousingInstances;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> BeaconBaseInstances;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> BeaconGreenLensInstances;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> BeaconAmberLensInstances;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> BeaconRedLensInstances;
    UPROPERTY(VisibleAnywhere) TArray<TObjectPtr<UStaticMeshComponent>> LiquidSurfaces;
    UPROPERTY(VisibleAnywhere) TArray<TObjectPtr<UPointLightComponent>> TreatmentServiceLights;
    UPROPERTY(VisibleAnywhere) TArray<TObjectPtr<URectLightComponent>> OvenInteriorLights;
    UPROPERTY(VisibleAnywhere) TArray<TObjectPtr<USpotLightComponent>> PortalSpotLights;
    UPROPERTY(VisibleAnywhere) TArray<TObjectPtr<UStaticMeshComponent>> OvenFans;
    UPROPERTY(VisibleAnywhere) TObjectPtr<ULBStatusBeaconComponent> EntryBeacon;
    UPROPERTY(VisibleAnywhere) TObjectPtr<ULBStatusBeaconComponent> ExitBeacon;

    UPROPERTY(Transient) TObjectPtr<UStaticMesh> CubeFallbackMesh;
    UPROPERTY(Transient) TArray<FLBECoatCarrierRuntimeEntry> Carriers;
    UPROPERTY(VisibleInstanceOnly) FName LineId = NAME_None;
    UPROPERTY(VisibleInstanceOnly) ELBECoatOperatingState OperatingState = ELBECoatOperatingState::Stopped;
    UPROPERTY(VisibleInstanceOnly) FName StateReason = NAME_None;
    UPROPERTY(VisibleInstanceOnly) TArray<FLBECoatBayDescriptor> BayDescriptors;
    UPROPERTY(VisibleInstanceOnly) TArray<FLBECoatBayOperatingState> BayOperatingStates;
    UPROPERTY(VisibleInstanceOnly) float FanRotationDegrees = 0.0f;

    void InitializeBayDefinitions();
    int32 FindBayIndexAtDistance(float DistanceCm) const;
    static float MigrateLegacyCarrierDistance(float LegacyDistanceCm);
    UStaticMesh* ResolveMesh(const TSoftObjectPtr<UStaticMesh>& Reference) const;
    UMaterialInterface* ResolveMaterial(const TSoftObjectPtr<UMaterialInterface>& Reference) const;
    bool HasImportedModuleForBay(int32 BayIndex) const;
    void AddBoxInstance(UHierarchicalInstancedStaticMeshComponent* Component,
        const FVector& CentreCm, const FVector& SizeCm) const;
    void BuildFallbackStructure();
    void RefreshOperationalPresentation();
    void AdvanceFanPresentation(float DeltaSeconds);
    void RefreshLiquidSurface(int32 TreatmentBayIndex);
    void RefreshAllCarrierPresentations();
    void RefreshCarrierPresentation(FLBECoatCarrierRuntimeEntry& Carrier);
    void CreateCarrierPresentation(FLBECoatCarrierRuntimeEntry& Carrier);
    void DestroyCarrierPresentation(FLBECoatCarrierRuntimeEntry& Carrier);
    int32 FindCarrierIndex(FName CarrierId) const;
    bool CanCarrierAdvance(const FLBECoatCarrierRuntimeEntry& Carrier) const;
};
