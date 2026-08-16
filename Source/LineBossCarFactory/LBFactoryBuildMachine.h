#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBFactoryProcessPortComponent.h"
#include "LBFactoryBuildMachine.generated.h"

class UBoxComponent;
class UMaterialInterface;
class UStaticMesh;
class UStaticMeshComponent;
class USceneComponent;
class ULBFactoryFloorMarkingComponent;
class ULBMachineLiveryComponent;
class ULBStatusBeaconComponent;

UENUM(BlueprintType)
enum class ELBFactoryBuildMachineType : uint8
{
    InboundDeliveryDock,
    DepackagingRobot,
    DecoilerFeeder,
    PressTrain,
    InspectionCell,
    OutboundPanelDock,
    /** PR002 wrapped-coil weighing, identity and material inspection cell. Appended for save compatibility. */
    CoilWeighInspectionCell,
    /** Complete 189 m ED / e-coat line: six 18 m tanks, 9 m drain and 72 m six-body oven. Appended for save compatibility. */
    ECoatLine,
    /** Complete body-weld shop between pressed-panel dispatch and ED. Appended for save compatibility. */
    BodyWeldLine
};

UENUM(BlueprintType)
enum class ELBFactoryMachineOperatingState : uint8
{
    Idle,
    Starved,
    Ready,
    Blocked,
    Processing,
    Fault
};

USTRUCT(BlueprintType)
struct FLBFactoryBuildMachineSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Version = 2;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName MachineId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBFactoryBuildMachineType MachineType = ELBFactoryBuildMachineType::InboundDeliveryDock;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FTransform WorldTransform = FTransform::Identity;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FName> InputUnitIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FName> OutputUnitIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FName> CompletedUnitIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 NextOutputSerial = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 MaximumInputBuffer = 4;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 MaximumOutputBuffer = 4;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBFactoryMachineOperatingState OperatingState = ELBFactoryMachineOperatingState::Idle;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FString OperatingReason;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 RequiredAutomaticProcessSteps = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 CompletedAutomaticProcessSteps = 0;
};

/** Runtime shell and process authority for a player-placed factory machine package. */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBFactoryBuildMachine : public AActor
{
    GENERATED_BODY()

public:
    ALBFactoryBuildMachine();

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Machine")
    bool Configure(FName InMachineId, ELBFactoryBuildMachineType InMachineType);

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine")
    FName GetMachineId() const { return MachineId; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine")
    ELBFactoryBuildMachineType GetMachineType() const { return MachineType; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine")
    FVector GetMachineHalfExtent() const { return MachineHalfExtent; }

    /** Full player-placement exclusion box, which can be larger and offset from the machine body. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine")
    FVector GetProtectedEnvelopeHalfExtent() const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine")
    FVector GetProtectedEnvelopeRelativeCentre() const;

    /** Placement-driven safety paint. It follows this actor and is rebuilt on load/configure. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Floor Paint")
    ULBFactoryFloorMarkingComponent* GetFloorMarkings() const { return FloorMarkings; }

    /** Height of the actor pivot above the selected floor point. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine")
    float GetPlacementRootHeightCm() const { return PlacementRootHeightCm; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine")
    UStaticMeshComponent* GetApprovedVisualComponent() const { return ApprovedVisual; }

    /** Explicit player-livery authority; approved art remains opt-in per authored slot. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Presentation")
    ULBMachineLiveryComponent* GetMachineLiveryComponent() const { return MachineLivery; }

    /** Engine-native, clearly provisional modules used only where owner-approved art is pending. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Presentation")
    int32 GetVisiblePlaceholderPartCount() const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Presentation")
    bool IsUsingModularPlaceholder() const { return GetVisiblePlaceholderPartCount() > 0; }

    /** Resolved imported PR005-PR010 modules currently shown by the compact preparation package. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Presentation")
    int32 GetVisibleCoilPreparationArtPartCount() const;

    /** Six only when every PR005-PR010 station resolved atomically; failed stations use local fallback art. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Presentation")
    int32 GetResolvedCoilPreparationStationCount() const
    { return ResolvedCoilPreparationStationCount; }

    /** Native soft-reference contract used by cooking and focused asset-path automation. */
    const TArray<TSoftObjectPtr<UStaticMesh>>& GetCoilPreparationVisualAssetReferences() const
    { return CoilPreparationVisualAssets; }

    const TMap<FName, TSoftObjectPtr<UMaterialInterface>>& GetCoilPreparationPaletteMaterialReferences() const
    { return CoilPreparationPaletteMaterials; }

    /** Presentation pool exposed read-only so automation can distinguish imported art from fallback primitives. */
    const TArray<TObjectPtr<UStaticMeshComponent>>& GetCoilPreparationVisualComponents() const
    { return PlaceholderParts; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Inbound")
    int32 GetVisibleTrailerCoilCount() const;

    /**
     * Reuses the dock authority and keep-clear envelope while removing every retained
     * lorry, trailer-coil and coil-handler visual. The separately proved native AGV is
     * then the only inbound vehicle presentation.
     */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Machine|Inbound")
    bool ConfigureNativeAGVArrivalPresentation(FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Inbound")
    bool IsUsingNativeAGVArrivalPresentation() const
    { return bUsingNativeAGVArrivalPresentation; }

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Machine|Inbound")
    bool SetTrailerCoilVisible(int32 CoilIndex, bool bVisible);

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Inbound")
    UStaticMeshComponent* GetInboundCraneBridgeComponent() const { return InboundCraneBridgeVisual; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Inbound")
    UStaticMeshComponent* GetInboundCHookComponent() const { return InboundCHookVisual; }

    /** Save-compatible component aliases for the crane-replacement coil-handler AGV. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Inbound")
    UStaticMeshComponent* GetInboundCoilHandlerChassisComponent() const { return InboundCraneRunwayVisual; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Inbound")
    UStaticMeshComponent* GetInboundCoilHandlerMastComponent() const { return InboundCraneBridgeVisual; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Inbound")
    UStaticMeshComponent* GetInboundCoilHandlerCarriageComponent() const { return InboundCraneTrolleyVisual; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Inbound")
    UStaticMeshComponent* GetInboundCoilHandlerBackrestComponent() const { return InboundCraneHoistVisual; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Inbound")
    UStaticMeshComponent* GetInboundCoilHandlerRamComponent() const { return InboundCHookVisual; }

    /**
     * The approved CHF01 body is presently one textured mesh, so its wheels cannot be
     * separated without replacing owner-approved art. These explicit axle roots preserve
     * the correct fixed-front/rear-steer hierarchy and are the binding points for a later
     * surgically separated wheel set.
     */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Inbound|Steering")
    USceneComponent* GetInboundCoilHandlerFixedFrontAxleRoot() const
    { return InboundCoilHandlerFixedFrontAxleRoot; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Inbound|Steering")
    USceneComponent* GetInboundCoilHandlerRearSteeringRoot() const
    { return InboundCoilHandlerRearSteeringRoot; }
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Machine|Inbound|Steering")
    void SetInboundCoilHandlerRearSteerAngleDegrees(float AngleDegrees);

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Inbound")
    UStaticMeshComponent* GetTrailerCoilComponent(int32 CoilIndex) const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Inbound")
    FVector GetReceivingSaddleLoadPoint() const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|PR002")
    bool IsPR002PayloadVisible() const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|PR002")
    UStaticMeshComponent* GetPR002StationVisualComponent() const { return PR002StationVisual; }

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Machine|PR002")
    bool SetPR002PayloadVisible(bool bVisible);

    FLBFactoryBuildMachineSaveState CaptureSaveState() const;
    bool RestoreSaveState(const FLBFactoryBuildMachineSaveState& State);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Machine|Flow")
    bool ReceiveDeliveredUnit(FName UnitId);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Machine|Flow")
    bool AcceptInputUnit(FName UnitId);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Machine|Flow")
    bool ProcessNextUnit(FName& OutUnitId);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Machine|Flow")
    bool ReleaseOutputUnit(FName& OutUnitId);

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Flow")
    int32 GetInputUnitCount() const { return InputUnitIds.Num(); }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Flow")
    int32 GetOutputUnitCount() const { return OutputUnitIds.Num(); }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Flow")
    int32 GetCompletedUnitCount() const { return CompletedUnitIds.Num(); }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Flow")
    int32 GetMaximumInputBuffer() const { return MaximumInputBuffer; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Flow")
    int32 GetMaximumOutputBuffer() const { return MaximumOutputBuffer; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Flow")
    bool CanAcceptInputUnit() const { return MachineType != ELBFactoryBuildMachineType::InboundDeliveryDock && InputUnitIds.Num() < MaximumInputBuffer; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Flow")
    ELBFactoryMachineOperatingState GetOperatingState() const { return OperatingState; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Flow")
    FString GetOperatingReason() const { return OperatingReason; }

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Machine|Flow")
    bool ConfigureGameplayBuffers(int32 InMaximumInputBuffer, int32 InMaximumOutputBuffer);

    /** Advances gameplay timing without claiming a real engineering cycle time. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Machine|Flow")
    bool AdvanceAutomaticProcess(FName& OutUnitId, bool& bOutCompleted);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Machine|Flow")
    bool ConfigureGameplayProcessSteps(int32 InRequiredSteps);

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Flow")
    int32 GetRequiredAutomaticProcessSteps() const { return RequiredAutomaticProcessSteps; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machine|Flow")
    int32 GetCompletedAutomaticProcessSteps() const { return CompletedAutomaticProcessSteps; }

    void RefreshOperatingState();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Factory Builder|Machine")
    TObjectPtr<ULBFactoryProcessPortComponent> InputPort;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Factory Builder|Machine")
    TObjectPtr<ULBFactoryProcessPortComponent> OutputPort;

private:
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> SceneRoot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> MachineBody;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> MachineBase;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> ApprovedVisual;
    UPROPERTY(VisibleAnywhere) TArray<TObjectPtr<UStaticMeshComponent>> TrailerStandVisuals;
    UPROPERTY(VisibleAnywhere) TArray<TObjectPtr<UStaticMeshComponent>> TrailerCoilVisuals;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> InboundCraneRunwayVisual;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> InboundCraneBridgeVisual;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> InboundCraneTrolleyVisual;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> InboundCraneHoistVisual;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> InboundCHookVisual;
    /** Front/load axle never yaws; the CHF01 steers only at its counterweight end. */
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> InboundCoilHandlerFixedFrontAxleRoot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> InboundCoilHandlerRearSteeringRoot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> ReceivingSaddleRailAVisual;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> ReceivingSaddleRailBVisual;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> PR002StationVisual;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> PR002PayloadVisual;
    /**
     * PR005-only, additive operator-console art. It deliberately stays out of the
     * shared coil-preparation asset pool so it cannot alter the 75-part station,
     * save, collision, or material-flow contract.
     */
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> PR005DetailedHMIVisual;
    /** Shared presentation pool: imported preparation art or clearly provisional Engine primitives, never both per station. */
    UPROPERTY(VisibleAnywhere) TArray<TObjectPtr<UStaticMeshComponent>> PlaceholderParts;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> ProtectedEnvelope;
    UPROPERTY(VisibleAnywhere) TObjectPtr<ULBFactoryFloorMarkingComponent> FloorMarkings;
    UPROPERTY(VisibleAnywhere) TObjectPtr<ULBMachineLiveryComponent> MachineLivery;
    /** Runtime state stack kept separate from replaceable machine artwork. */
    UPROPERTY(VisibleAnywhere) TObjectPtr<ULBStatusBeaconComponent> StatusBeacon;
    UPROPERTY(Transient) TObjectPtr<UStaticMesh> PlaceholderCubeMesh;
    UPROPERTY(Transient) TObjectPtr<UStaticMesh> PlaceholderCylinderMesh;
    UPROPERTY(Transient) TObjectPtr<UStaticMesh> ApprovedInboundLorryMesh;
    UPROPERTY(Transient) TObjectPtr<UStaticMesh> ApprovedCoilHandlerBodyMesh;
    UPROPERTY(Transient) TObjectPtr<UStaticMesh> ApprovedCoilHandlerLiftMesh;
    UPROPERTY(Transient) TObjectPtr<UStaticMesh> ApprovedPR004CompleteCellMesh;
    UPROPERTY(Transient) TObjectPtr<UStaticMesh> ApprovedCoilSaddleMesh;
    /** Textured Meshy master imported as a visual-only PR005 candidate. */
    UPROPERTY(Transient) TObjectPtr<UStaticMesh> PR005DetailedHMIMesh;
    UPROPERTY(Transient) TObjectPtr<UMaterialInterface> PlaceholderGreenMaterial;
    UPROPERTY(Transient) TObjectPtr<UMaterialInterface> PlaceholderCharcoalMaterial;
    UPROPERTY(Transient) TObjectPtr<UMaterialInterface> PlaceholderYellowMaterial;
    UPROPERTY(Transient) TObjectPtr<UMaterialInterface> PlaceholderSteelMaterial;
    UPROPERTY(Transient) TObjectPtr<UMaterialInterface> GenericLiveryMaterialParent;
    /** Production-suitable imported station modules. Native CDO soft references make the cook dependency explicit. */
    UPROPERTY(VisibleDefaultsOnly, Category="Cairnwell|Factory Builder|Machine|Presentation")
    TArray<TSoftObjectPtr<UStaticMesh>> CoilPreparationVisualAssets;
    /** Authored station palettes needed to reproduce the accepted in-map material treatment. */
    UPROPERTY(VisibleDefaultsOnly, Category="Cairnwell|Factory Builder|Machine|Presentation")
    TMap<FName, TSoftObjectPtr<UMaterialInterface>> CoilPreparationPaletteMaterials;
    UPROPERTY(VisibleInstanceOnly) int32 ResolvedCoilPreparationStationCount = 0;
    UPROPERTY(VisibleInstanceOnly) FName MachineId = NAME_None;
    UPROPERTY(VisibleInstanceOnly) ELBFactoryBuildMachineType MachineType = ELBFactoryBuildMachineType::InboundDeliveryDock;
    bool bUsingNativeAGVArrivalPresentation = false;
    UPROPERTY(VisibleInstanceOnly) FVector MachineHalfExtent = FVector::ZeroVector;
    UPROPERTY(VisibleInstanceOnly) float PlacementRootHeightCm = 0.0f;
    UPROPERTY(VisibleInstanceOnly) TArray<FName> InputUnitIds;
    UPROPERTY(VisibleInstanceOnly) TArray<FName> OutputUnitIds;
    UPROPERTY(VisibleInstanceOnly) TArray<FName> CompletedUnitIds;
    UPROPERTY(VisibleInstanceOnly) int32 NextOutputSerial = 1;
    UPROPERTY(VisibleInstanceOnly) int32 MaximumInputBuffer = 4;
    UPROPERTY(VisibleInstanceOnly) int32 MaximumOutputBuffer = 4;
    UPROPERTY(VisibleInstanceOnly) ELBFactoryMachineOperatingState OperatingState = ELBFactoryMachineOperatingState::Idle;
    UPROPERTY(VisibleInstanceOnly) FString OperatingReason;
    UPROPERTY(VisibleInstanceOnly) int32 RequiredAutomaticProcessSteps = 1;
    UPROPERTY(VisibleInstanceOnly) int32 CompletedAutomaticProcessSteps = 0;
    void RebuildFloorMarkings();
    void UpdateStatusBeacon();
};
