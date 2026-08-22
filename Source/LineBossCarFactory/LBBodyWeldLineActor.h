#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBFactoryBuildMachine.h"
#include "LBBodyWeldLineActor.generated.h"

class UBoxComponent;
class UHierarchicalInstancedStaticMeshComponent;
class ULBFactoryFloorMarkingComponent;
class ULBFactoryProcessPortComponent;
class ULBMachineLiveryComponent;
class ULBStatusBeaconComponent;
class UMaterialInterface;
class USceneComponent;
class UStaticMesh;
class UStaticMeshComponent;

/** Authored phases inside the first composite body-weld line. */
UENUM(BlueprintType)
enum class ELBBodyWeldPhase : uint8
{
    AwaitingRecipe,
    ReservingInputs,
    ClosurePreparation,
    Framing,
    Welding,
    GeometryCheck,
    OutputReady,
    TransferringToED
};

/** The geometry gate is deterministic; it never rolls random defects. */
UENUM(BlueprintType)
enum class ELBBodyWeldQualityState : uint8
{
    Pending,
    Good,
    ReworkRequired,
    Rejected
};

/** Exact press-authored panel identity held by a weld-side stillage lane. */
USTRUCT(BlueprintType)
struct FLBBodyWeldPanelUnit
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName PanelId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName OrderId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName VehicleModelId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName PanelTypeId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName StillageId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bReserved = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bConsumed = false;
};

/**
 * Actor-local representation of a stillage after an integration adapter has transferred
 * authority to weld. Receiving this record does not itself claim a physical FLT transfer.
 */
USTRUCT(BlueprintType)
struct FLBBodyWeldStillageInventory
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName StillageId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName OrderId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName VehicleModelId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName PanelTypeId = NAME_None;
    /** Deterministic upstream delivery sequence. Lower values are selected first. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int64 DeliverySequence = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 CapacityPanels = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FLBBodyWeldPanelUnit> PanelUnits;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bEmptyReturnQueued = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bEmptyReturnIssued = false;
};

/** Finite supplied underbody/inner-structure kit; this is inventory, not scenery. */
USTRUCT(BlueprintType)
struct FLBBodyWeldBaseKitUnit
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName KitId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName KitTypeId = TEXT("CAIRNWELL_2040_BIW_BASE_KIT");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName OrderId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName VehicleModelId = TEXT("CAIRNWELL_2040");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int64 DeliverySequence = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bReserved = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bConsumed = false;
};

/** Immutable source identity copied into a reservation and then the BIW record. */
USTRUCT(BlueprintType)
struct FLBBodyWeldPanelLineage
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName PanelId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName PanelTypeId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName StillageId = NAME_None;
};

/** All-or-nothing selection for one Cairnwell body. */
USTRUCT(BlueprintType)
struct FLBBodyWeldInputReservation
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bValid = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bConsumptionCommitted = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName ReservationId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName OrderId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName VehicleModelId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName BaseKitId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FLBBodyWeldPanelLineage> Panels;
};

/** Conditions sampled by the deterministic geometry gate. */
USTRUCT(BlueprintType)
struct FLBBodyWeldQualityConditions
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bFixtureProgramCorrect = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bRobotCalibrationInTolerance = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bServiceConditionAcceptable = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bSafetyInterlockClear = true;
};

/** Stored evidence makes a quality result reproducible after save/load. */
USTRUCT(BlueprintType)
struct FLBBodyWeldQualityEvidence
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bRecipeComplete = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bFixtureProgramCorrect = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bSpotOperationsComplete = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bMIGOperationsComplete = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bRobotCalibrationInTolerance = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bServiceConditionAcceptable = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bSafetyInterlockClear = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FName> ReasonCodes;
};

/** Deterministic work evidence; these values are not wall-clock timestamps. */
USTRUCT(BlueprintType)
struct FLBBodyWeldCycleEvidence
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float ClosurePreparationSeconds = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float FramingSeconds = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float WeldingSeconds = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float GeometryCheckSeconds = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int64 CompletionSequence = 0;
};

/** Exact body identity retained through the downstream ED acknowledgement boundary. */
USTRUCT(BlueprintType)
struct FLBBodyInWhiteRecord
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName BodyId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName VehicleModelId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName OrderId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName BaseKitId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName ReservationId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName WeldLineId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FLBBodyWeldPanelLineage> Panels;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBBodyWeldQualityState QualityState = ELBBodyWeldQualityState::Pending;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FLBBodyWeldQualityEvidence QualityEvidence;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FLBBodyWeldCycleEvidence CycleEvidence;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bEDAccepted = false;
};

/** Same-ID empty-stillage return message; no substitute container is spawned. */
USTRUCT(BlueprintType)
struct FLBBodyWeldEmptyStillageReturn
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName StillageId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName OrderId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName VehicleModelId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName PanelTypeId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int64 QueueSequence = 0;
};

/** Actor-local persistence payload ready for root save-format 18 integration. */
USTRUCT(BlueprintType)
struct FLBBodyWeldLineSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Version = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName LineId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FTransform WorldTransform = FTransform::Identity;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bEnabled = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bPaused = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bServiceHeld = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bEDAvailable = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bFaulted = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName FaultReason = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName AssignedOrderId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBFactoryMachineOperatingState OperatingState = ELBFactoryMachineOperatingState::Idle;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FString OperatingReason;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBBodyWeldPhase Phase = ELBBodyWeldPhase::AwaitingRecipe;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float PhaseProgress01 = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FLBBodyWeldStillageInventory> Stillages;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FLBBodyWeldBaseKitUnit> BaseKits;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FLBBodyWeldInputReservation ActiveReservation;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bHasOutputBody = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FLBBodyInWhiteRecord OutputBody;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bHasReworkBody = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FLBBodyInWhiteRecord ReworkBody;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FLBBodyInWhiteRecord> CompletedBodies;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FLBBodyWeldEmptyStillageReturn> PendingEmptyReturns;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FLBBodyWeldQualityConditions QualityConditions;
    /** Worst condition observed since this recipe committed; later repairs do not erase evidence. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FLBBodyWeldQualityConditions ActiveCycleQualityConditions;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FLBBodyWeldCycleEvidence ActiveCycleEvidence;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float RobotBaseWear01 = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float SpotHeadWear01 = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float MIGHeadWear01 = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 NextReservationSerial = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 NextBodySerial = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int64 NextEventSequence = 1;
};

/**
 * First isolated Body Weld runtime spine. It owns exact actor-local inventory only after
 * an integration adapter has handed it over; press flow, FLT routing and root-save ownership
 * remain external. GeneralParts on the base-kit port is a temporary compatibility class until
 * an integration owner appends a dedicated BIWBaseKit material enum.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBBodyWeldLineActor : public AActor
{
    GENERATED_BODY()

public:
    ALBBodyWeldLineActor();

    virtual void OnConstruction(const FTransform& Transform) override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Body Weld")
    bool Configure(FName InLineId);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Body Weld|State")
    void SetEnabled(bool bInEnabled);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Body Weld|State")
    bool SetAssignedOrder(FName InOrderId);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Body Weld|State")
    void SetPaused(bool bInPaused);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Body Weld|State")
    void SetServiceHeld(bool bInServiceHeld);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Body Weld|State")
    void SetEDAvailable(bool bInAvailable);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Body Weld|Quality")
    void SetQualityConditions(const FLBBodyWeldQualityConditions& InConditions);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Body Weld|Inventory")
    bool ReceivePanelStillage(const FLBBodyWeldStillageInventory& Stillage, FString& OutReason);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Body Weld|Inventory")
    bool ReceiveBaseKit(const FLBBodyWeldBaseKitUnit& BaseKit, FString& OutReason);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Body Weld|Inventory")
    bool PopEmptyStillageReturn(FLBBodyWeldEmptyStillageReturn& OutReturn);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Body Weld|Production")
    bool TryReserveRecipe(FString& OutReason);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Body Weld|Production")
    bool CommitReservedInputs(FString& OutReason);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Body Weld|Production")
    void AdvanceSimulation(float DeltaSeconds);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Body Weld|Production")
    bool RetryHeldBody(FString& OutReason);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Body Weld|Production")
    bool AcknowledgeEDTransfer(FName BodyId, FLBBodyInWhiteRecord& OutTransferredBody);

    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Recipe")
    static FName GetVehicleModelId();
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Recipe")
    static FName GetBaseKitTypeId();
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Recipe")
    static TArray<FName> GetRequiredPanelFamilies();

    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|State") FName GetLineId() const { return LineId; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|State") FName GetAssignedOrderId() const { return AssignedOrderId; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|State") ELBFactoryMachineOperatingState GetOperatingState() const { return OperatingState; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|State") FString GetOperatingReason() const { return OperatingReason; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|State") ELBBodyWeldPhase GetPhase() const { return Phase; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|State") float GetPhaseProgress01() const { return PhaseProgress01; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|State") bool IsEDAvailable() const { return bEDAvailable; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Inventory") int32 GetAvailablePanelCount() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Inventory") int32 GetReservedPanelCount() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Inventory") int32 GetAvailableBaseKitCount() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Inventory") int32 GetPendingEmptyReturnCount() const { return PendingEmptyReturns.Num(); }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Production") bool GetActiveReservation(FLBBodyWeldInputReservation& OutReservation) const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Production") bool GetOutputBody(FLBBodyInWhiteRecord& OutBody) const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Production") bool GetReworkBody(FLBBodyInWhiteRecord& OutBody) const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Production") int32 GetCompletedBodyCount() const { return CompletedBodies.Num(); }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Flow") ULBFactoryProcessPortComponent* GetStillageInputPort() const { return StillageInputPort; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Flow") ULBFactoryProcessPortComponent* GetBaseKitInputPort() const { return BaseKitInputPort; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Flow") ULBFactoryProcessPortComponent* GetBIWOutputPort() const { return BIWOutputPort; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Presentation") UBoxComponent* GetProtectedEnvelope() const { return ProtectedEnvelope; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Presentation") ULBFactoryFloorMarkingComponent* GetFloorMarkings() const { return FloorMarkings; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Presentation") ULBMachineLiveryComponent* GetMachineLivery() const { return MachineLivery; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Presentation") ULBStatusBeaconComponent* GetStatusBeacon() const { return StatusBeacon; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Presentation") int32 GetProxyPartCount() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Presentation") UStaticMeshComponent* GetFramingFixturePresentation() const { return FramingFixturePresentation; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Presentation") UStaticMeshComponent* GetBaseKitSkidPresentation() const { return BaseKitSkidPresentation; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Presentation") UStaticMeshComponent* GetBaseKitUnderbodyPresentation() const { return BaseKitUnderbodyPresentation; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Presentation") bool HasResolvedRuntimeArt() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Presentation") bool IsBaseKitWorkpiecePresented() const;

    /** Four fixed-pose visual stations replace their cube triplets independently and fail closed. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Presentation|Robots") int32 GetRobotStationCount() const { return RobotStationCount; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Presentation|Robots") int32 GetResolvedRobotStationCount() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Presentation|Robots") int32 GetFallbackRobotStationCount() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Presentation|Robots") int32 GetImportedRobotPartCount() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Presentation|Robots") int32 GetRobotProxyPartCount() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Presentation|Robots") bool HasResolvedRobotRuntimeArt() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Presentation|Robots") bool IsRobotRuntimeArtStaticPoseOnly() const { return true; }
    /** Ordered shared-base, MIG, spot-gun, panel-pick soft paths used by the guarded resolver. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Presentation|Robots") TArray<FString> GetRobotRuntimeArtPaths() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Presentation|Robots") FName GetRobotStationToolRole(int32 StationIndex) const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Presentation|Robots") UStaticMeshComponent* GetRobotBasePresentation(int32 StationIndex) const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Presentation|Robots") UStaticMeshComponent* GetRobotToolPresentation(int32 StationIndex) const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Presentation|Robots") FVector GetRobotToolFlangeRelativeLocation() const;

#if WITH_DEV_AUTOMATION_TESTS
    /** Test-only fault injection proves one missing role cannot suppress another station's fallback. */
    void SetRobotRuntimeArtReferencesForTests(const FSoftObjectPath& SharedBasePath,
        const FSoftObjectPath& MIGToolPath, const FSoftObjectPath& SpotToolPath,
        const FSoftObjectPath& PanelPickToolPath);
#endif

    UFUNCTION(BlueprintPure, Category="Cairnwell|Body Weld|Persistence")
    FLBBodyWeldLineSaveState CaptureSaveState() const;
    static bool IsSaveStateContractValid(const FLBBodyWeldLineSaveState& State);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Body Weld|Persistence")
    bool RestoreSaveState(const FLBBodyWeldLineSaveState& State);

private:
    static constexpr int32 MaximumPendingEmptyReturns = 32;
    static constexpr float ClosurePreparationDurationSeconds = 5.0f;
    static constexpr float FramingDurationSeconds = 6.0f;
    static constexpr float WeldingDurationSeconds = 8.0f;
    static constexpr float GeometryCheckDurationSeconds = 3.0f;
    static constexpr int32 RobotStationCount = 4;

    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> SceneRoot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> ProtectedEnvelope;
    UPROPERTY(VisibleAnywhere) TObjectPtr<ULBFactoryFloorMarkingComponent> FloorMarkings;
    UPROPERTY(VisibleAnywhere) TObjectPtr<ULBMachineLiveryComponent> MachineLivery;
    UPROPERTY(VisibleAnywhere) TObjectPtr<ULBStatusBeaconComponent> StatusBeacon;
    UPROPERTY(VisibleAnywhere) TObjectPtr<ULBFactoryProcessPortComponent> StillageInputPort;
    UPROPERTY(VisibleAnywhere) TObjectPtr<ULBFactoryProcessPortComponent> BaseKitInputPort;
    UPROPERTY(VisibleAnywhere) TObjectPtr<ULBFactoryProcessPortComponent> BIWOutputPort;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> PrimaryMachineInstances;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> SecondaryMachineInstances;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> SafetyInstances;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> BIWProxyInstances;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> BIWProxy;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> FramingFixturePresentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> BaseKitWorkpieceRoot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> BaseKitSkidPresentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> BaseKitUnderbodyPresentation;
    UPROPERTY(VisibleAnywhere) TArray<TObjectPtr<UStaticMeshComponent>> RobotBasePresentations;
    UPROPERTY(VisibleAnywhere) TArray<TObjectPtr<UStaticMeshComponent>> RobotToolPresentations;
    UPROPERTY(Transient) TObjectPtr<UStaticMesh> CubeFallbackMesh;
    UPROPERTY(Transient) TObjectPtr<UMaterialInterface> BasicPresentationMaterial;

    /** Fresh, independently validated modular runtime art; never points at raw Meshy authorities. */
    UPROPERTY(EditAnywhere, Category="Cairnwell|Body Weld|Presentation")
    TSoftObjectPtr<UStaticMesh> FramingFixtureMesh;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Body Weld|Presentation")
    TSoftObjectPtr<UStaticMesh> BaseKitSkidMesh;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Body Weld|Presentation")
    TSoftObjectPtr<UStaticMesh> BaseKitUnderbodyMesh;
    /** Validated static-pose candidate only; no skeletal animation or semantic repaint is implied. */
    UPROPERTY(EditAnywhere, Category="Cairnwell|Body Weld|Presentation|Robots")
    TSoftObjectPtr<UStaticMesh> WeldRobotSharedBaseMesh;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Body Weld|Presentation|Robots")
    TSoftObjectPtr<UStaticMesh> WeldRobotMIGToolMesh;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Body Weld|Presentation|Robots")
    TSoftObjectPtr<UStaticMesh> WeldRobotSpotToolMesh;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Body Weld|Presentation|Robots")
    TSoftObjectPtr<UStaticMesh> WeldRobotPanelPickToolMesh;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Body Weld|Presentation")
    bool bLoadReferencedMeshesSynchronously = true;

    UPROPERTY(VisibleInstanceOnly) FName LineId = NAME_None;
    UPROPERTY(VisibleInstanceOnly) FName AssignedOrderId = NAME_None;
    UPROPERTY(VisibleInstanceOnly) ELBFactoryMachineOperatingState OperatingState = ELBFactoryMachineOperatingState::Idle;
    UPROPERTY(VisibleInstanceOnly) FString OperatingReason;
    UPROPERTY(VisibleInstanceOnly) ELBBodyWeldPhase Phase = ELBBodyWeldPhase::AwaitingRecipe;
    UPROPERTY(VisibleInstanceOnly) float PhaseProgress01 = 0.0f;
    UPROPERTY(VisibleInstanceOnly) bool bEnabled = true;
    UPROPERTY(VisibleInstanceOnly) bool bPaused = false;
    UPROPERTY(VisibleInstanceOnly) bool bServiceHeld = false;
    UPROPERTY(VisibleInstanceOnly) bool bEDAvailable = false;
    UPROPERTY(VisibleInstanceOnly) bool bFaulted = false;
    UPROPERTY(VisibleInstanceOnly) FName FaultReason = NAME_None;
    UPROPERTY(VisibleInstanceOnly) TArray<FLBBodyWeldStillageInventory> Stillages;
    UPROPERTY(VisibleInstanceOnly) TArray<FLBBodyWeldBaseKitUnit> BaseKits;
    UPROPERTY(VisibleInstanceOnly) FLBBodyWeldInputReservation ActiveReservation;
    UPROPERTY(VisibleInstanceOnly) bool bHasOutputBody = false;
    UPROPERTY(VisibleInstanceOnly) FLBBodyInWhiteRecord OutputBody;
    UPROPERTY(VisibleInstanceOnly) bool bHasReworkBody = false;
    UPROPERTY(VisibleInstanceOnly) FLBBodyInWhiteRecord ReworkBody;
    UPROPERTY(VisibleInstanceOnly) TArray<FLBBodyInWhiteRecord> CompletedBodies;
    UPROPERTY(VisibleInstanceOnly) TArray<FLBBodyWeldEmptyStillageReturn> PendingEmptyReturns;
    UPROPERTY(VisibleInstanceOnly) FLBBodyWeldQualityConditions QualityConditions;
    UPROPERTY(VisibleInstanceOnly) FLBBodyWeldQualityConditions ActiveCycleQualityConditions;
    UPROPERTY(VisibleInstanceOnly) FLBBodyWeldCycleEvidence ActiveCycleEvidence;
    UPROPERTY(VisibleInstanceOnly) float RobotBaseWear01 = 0.0f;
    UPROPERTY(VisibleInstanceOnly) float SpotHeadWear01 = 0.0f;
    UPROPERTY(VisibleInstanceOnly) float MIGHeadWear01 = 0.0f;
    UPROPERTY(VisibleInstanceOnly) int32 NextReservationSerial = 1;
    UPROPERTY(VisibleInstanceOnly) int32 NextBodySerial = 1;
    UPROPERTY(VisibleInstanceOnly) int64 NextEventSequence = 1;

    void RebuildProxyVisuals();
    void ResolveRuntimeVisuals();
    void ResolveRobotRuntimeVisuals();
    bool IsRobotStationUsingRuntimeArt(int32 StationIndex) const;
    void ApplyRuntimeArtMaterials(UStaticMeshComponent* Component);
    UStaticMesh* ResolveMesh(const TSoftObjectPtr<UStaticMesh>& Reference) const;
    void RefreshOperatingState();
    void RefreshPresentation();
    bool FindFirstMissingRecipeItem(FString& OutReason) const;
    bool FindFirstMissingRecipeItemForModel(FName ModelId, FString& OutReason) const;
    bool ResolveReservableModel(FName& OutModelId, TArray<FName>& OutPanelFamilies,
        FName& OutBaseKitTypeId, FString& OutReason) const;
    bool ValidateActiveReservationReferences(bool bExpectConsumed) const;
    bool WouldCommitOverflowEmptyReturnQueue() const;
    void SetFault(FName Reason);
    void AdvanceToNextPhase();
    void FinalizeGeometryGate();
    FLBBodyWeldQualityEvidence BuildQualityEvidence() const;
    static ELBBodyWeldQualityState EvaluateQuality(const FLBBodyWeldQualityEvidence& Evidence);
    static bool IsBodyRecordContractValid(const FLBBodyInWhiteRecord& Body);
    static bool IsStillageContractValid(const FLBBodyWeldStillageInventory& Stillage);
    static bool IsBaseKitContractValid(const FLBBodyWeldBaseKitUnit& BaseKit);
    static FString StableIdentityToken(FName Source);
    void AddBoxInstance(UHierarchicalInstancedStaticMeshComponent* Component,
        const FVector& CentreCm, const FVector& SizeCm) const;
};
