#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBPR004Station.generated.h"

class USceneComponent;
class UStaticMeshComponent;
class UTextRenderComponent;
class UWidgetComponent;

UENUM(BlueprintType)
enum class ELBPR004State : uint8
{
    Unsurveyed,
    Isolated,
    SafeForAccess,
    AwaitingCoil,
    CoilLoaded,
    AwaitingAuthorisation,
    Scanning,
    Securing,
    AwaitingRobotClearance,
    LocatingBands,
    RemovingBands,
    RemovingEdgeProtectors,
    RemovingWrap,
    Inspecting,
    AwaitingDisposition,
    ReadyForHandoff,
    QualityHold,
    Rejected,
    AwaitingRejectRemoval,
    Fault
};

UENUM(BlueprintType)
enum class ELBPR004Fault : uint8
{
    None,
    WrongCoilIdentity,
    PackagingScanFault,
    CoilNotSeated,
    CradleNotLocked,
    CHookNotWithdrawn,
    GateOrSafetyInterlockOpen,
    RobotNotHealthy,
    BandNotLocated,
    BandEndNotCaptured,
    BandSprungAfterCut,
    BandWithdrawalJam,
    BandWinderJam,
    BandGuardOpen,
    BandCoilEjectionFault,
    EdgeProtectorJam,
    ProtectorGuardOpen,
    ProtectorWasteStreamFault,
    WrapSeamNotFound,
    WrapTabNotCaptured,
    FilmSpindleNotHealthy,
    FilmSpindleGripFailed,
    FilmTensionHighOrLost,
    DancerTravelLimit,
    CradleSpindleSyncFault,
    RobotNotClearForFilmIndex,
    FilmStripOffFailed,
    WrapTornOrFragmented,
    WrapTrappedBeneathCoil,
    ManualRecoveryRequired,
    RecoveryFragmentsUnaccounted,
    TrappedKeyNotRestored,
    WrapTornOrJammed,
    PlasticCompactorJam,
    PlasticGuardOpen,
    PlasticBaleEjectionFault,
    InspectionVisionFault,
    WasteBinFull,
    SurfaceCorrosion,
    SurfaceDamage,
    CraneHandoffNotClear,
    PowerLossReconciliationRequired,
    InFlightMaterialOwnershipUnclear
};

UENUM(BlueprintType)
enum class ELBPR004Disposition : uint8
{
    Unknown,
    Ready,
    QualityHold,
    Reject
};

UENUM(BlueprintType)
enum class ELBPR004WasteStream : uint8
{
    None,
    SteelBand,
    EdgeProtector,
    PlasticWrap
};

UENUM(BlueprintType)
enum class ELBPR004ActionSubstage : uint8
{
    None,
    SourceSecured,
    SourceDetached,
    SpindleGripConfirmed,
    RobotClearForIndex,
    CradleSpindleSynchronized,
    TensionControlledWindComplete,
    WasteTransferAccepted,
    WasteProcessed,
    WasteEjected
};

UENUM(BlueprintType)
enum class ELBPR004TrappedKeyState : uint8
{
    Installed,
    RemovedAndRetained,
    Restored
};

UENUM(BlueprintType)
enum class ELBPR004MaterialOwner : uint8
{
    None,
    Coil,
    Robot,
    WasteModule,
    WasteBin
};

USTRUCT(BlueprintType)
struct FLBPR004WasteStreamStatus
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bEquipmentHealthy = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bGuardClosed = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bBinPresent = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bCapacityAvailable = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bEjectReady = false;
};

USTRUCT(BlueprintType)
struct FLBPR004FilmDewrapStatus
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bSpindleHealthy = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bDancerAndTensionHealthy = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bCradleSpindleSynchronized = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bRobotClearForIndex = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bSpindleGripConfirmed = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bTransferChuteClear = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bStripperReady = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bFragmentCameraClear = false;
};

USTRUCT(BlueprintType)
struct FLBPR004ActiveAction
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bIsActive = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 ActionToken = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName ComponentType = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 ComponentIndex = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName ActionContract = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBPR004WasteStream WasteStream = ELBPR004WasteStream::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBPR004ActionSubstage LastAcknowledgedSubstage = ELBPR004ActionSubstage::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBPR004ActionSubstage TerminalSubstage = ELBPR004ActionSubstage::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBPR004MaterialOwner MaterialOwner = ELBPR004MaterialOwner::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName LastEvidenceId = NAME_None;
};

USTRUCT(BlueprintType)
struct FLBPR004WasteRecord
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName RecordId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 CycleSerial = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 ActionToken = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FString CoilId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBPR004WasteStream WasteStream = ELBPR004WasteStream::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName WasteType = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName SourceComponentType = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 SourceComponentIndex = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 AcceptedSourceMask = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName EvidenceId = NAME_None;
};

USTRUCT(BlueprintType)
struct FLBPR004PackagingScanReport
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName ReportId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FString CoilId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName RecipeId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 DetectedBandMask = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 DetectedProtectorMask = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 DetectedWrapMask = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bScannerHealthy = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bIdentityReadable = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bDimensionsWithinRecipe = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bPackagingClassificationComplete = false;
};

USTRUCT(BlueprintType)
struct FLBPR004InspectionReport
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName ReportId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FString CoilId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bVisionHealthy = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bFaceInspectionPassed = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bBoreInspectionPassed = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bEdgeInspectionPassed = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bCoilTailSecuredObserved = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bSurfaceCorrosionDetected = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bSurfaceDamageDetected = false;
};

USTRUCT(BlueprintType)
struct FLBPR004SaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 SaveVersion = 4;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBPR004State State = ELBPR004State::Unsurveyed;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBPR004State StateBeforeFault = ELBPR004State::AwaitingAuthorisation;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBPR004State StateBeforePowerLoss = ELBPR004State::AwaitingAuthorisation;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBPR004Fault ActiveFault = ELBPR004Fault::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBPR004Disposition Disposition = ELBPR004Disposition::Unknown;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FString CoilId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FString HeatId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FString SupplierLotId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FString TraceabilityBarcode;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FString ExpectedCoilId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName RecipeId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 ActiveCycleSerial = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 NextCycleSerial = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 NextActionToken = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 NextReportRequestToken = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 ActiveScanRequestToken = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 ActiveInspectionRequestToken = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 RemainingBandMask = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 RemainingProtectorMask = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 RemainingWrapMask = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 AcceptedWrapMask = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FLBPR004ActiveAction ActiveAction;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBPR004WasteRecord> WasteLedger;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FLBPR004PackagingScanReport PackagingScanReport;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FLBPR004InspectionReport InspectionReport;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FLBPR004WasteStreamStatus BandStreamStatus;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FLBPR004WasteStreamStatus ProtectorStreamStatus;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FLBPR004WasteStreamStatus PlasticStreamStatus;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FLBPR004FilmDewrapStatus FilmDewrapStatus;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 CompactedBandCoilCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 CompactedPlasticBaleCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FName> UnrecoveredWrapFragmentIds;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FName> RecoveredWrapFragmentIds;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bManualWrapRecoveryRequired = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bManualWrapRecoveryInProgress = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bRecoveryZeroMotionVerified = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBPR004TrappedKeyState TrappedKeyState = ELBPR004TrappedKeyState::Installed;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName ManualRecoveryPermitId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName LastManualRecoveryEvidenceId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bControlPowerOn = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bCellCommissioned = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bCoilPresent = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bIdentityVerified = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bPackagingScanAccepted = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bInspectionReportAccepted = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bCoilTailSecured = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName CoilTailEvidenceId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bCradleLocked = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bCHookWithdrawn = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bGatesClosed = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bSafetyCircuitHealthy = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bPersonnelClear = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bRobotHealthy = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bPackagingScannerHealthy = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bInspectionSystemHealthy = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bPowerLossReconciliationRequired = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName ActiveHandoffTransactionId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName LastCompletedHandoffTransactionId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName ActiveRejectRemovalTransactionId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName LastCompletedRejectRemovalTransactionId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName LastRejectArchiveRecordId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FString LastCompletedCoilId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 LastCompletedCycleSerial = 0;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBPR004StateChanged, ELBPR004State, PreviousState, ELBPR004State, NewState);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FLBPR004FaultRaised, ELBPR004Fault, Fault);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FLBPR004PackagingScanRequested, int64, RequestToken, FString, CoilId, FName, RecipeId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBPR004PackagingScanAccepted, int64, RequestToken, FName, ReportId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_FourParams(FLBPR004PackagingActionRequested, int64, ActionToken, FName, ComponentType, int32, ComponentIndex, FName, ActionContract);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FLBPR004PackagingActionAdvanced, int64, ActionToken, ELBPR004ActionSubstage, Substage, ELBPR004MaterialOwner, MaterialOwner);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FLBPR004PackagingRemoved, int64, ActionToken, FName, ComponentType, int32, ComponentIndex);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FLBPR004WasteRecordAppended, FLBPR004WasteRecord, Record);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBPR004InspectionRequested, int64, RequestToken, FString, CoilId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBPR004InspectionAccepted, int64, RequestToken, FName, ReportId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBPR004DispositionChanged, FString, CoilId, ELBPR004Disposition, Disposition);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBPR004TransferCommand, FString, CoilId, FName, TransactionId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FLBPR004RejectArchived, FString, CoilId, FName, TransactionId, FName, ArchiveRecordId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBPR004FilmDriveCommand, bool, bCradleIndexEnabled, bool, bFilmSpindleEnabled);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBPR004ManualRecoveryChanged, bool, bRecoveryRequired, ELBPR004TrappedKeyState, KeyState);

UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBPR004Station : public AActor
{
    GENERATED_BODY()

public:
    ALBPR004Station();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Commissioning")
    bool SetControlPower(bool bEnabled);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Commissioning")
    bool SetCellCommissioned(bool bCommissioned);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Safety")
    bool SetSafetyInputs(bool bGatesAreClosed, bool bSafetyCircuitIsHealthy, bool bPersonnelAreClear);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Health")
    bool SetRobotHealthy(bool bHealthy);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Health")
    bool SetInspectionSystemsHealthy(bool bPackagingScannerIsHealthy, bool bInspectionSystemIsHealthy);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Waste")
    bool SetWasteStreamStatus(ELBPR004WasteStream Stream, const FLBPR004WasteStreamStatus& NewStatus);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Film Dewrap")
    bool SetFilmDewrapStatus(const FLBPR004FilmDewrapStatus& NewStatus);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Film Dewrap")
    bool RegisterUnrecoveredWrapFragment(FName FragmentId, bool bTrappedBeneathCoil);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Manual Recovery")
    bool BeginTrappedKeyManualRecovery(FName PermitId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Manual Recovery")
    bool ConfirmTrappedKeyIsolation(bool bZeroMotionVerified, bool bKeyRemovedAndRetained, FName EvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Manual Recovery")
    bool RecordRecoveredWrapFragment(FName FragmentId, FName EvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Manual Recovery")
    bool CompleteTrappedKeyManualRecovery(FName EvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Coil")
    bool LoadPackagedCoil(const FString& NewCoilId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Coil")
    bool LoadPackagedCoilWithTraceability(const FString& NewCoilId, const FString& NewHeatId,
        const FString& NewSupplierLotId, const FString& NewTraceabilityBarcode);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Coil")
    bool SelectDepackRecipe(FName NewRecipeId, const FString& NewExpectedCoilId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Cradle")
    bool SetCradleLocked(bool bLocked);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Crane")
    bool SetCHookWithdrawn(bool bWithdrawn);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Cycle")
    bool AuthoriseAutomaticCycle();

    /**
     * Player-facing simplified preparation action. The selected packaged coil
     * is atomically changed to the bare, handoff-ready state; presentation can
     * bind to OnStateChanged/IsCoilUnpackaged to swap the visible mesh.
     */
    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Interaction")
    bool UnpackageCoil(FName EvidenceId);

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-004|Interaction")
    bool CanUnpackageCoil(TArray<FText>& OutBlockingReasons) const;

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Cycle")
    bool SubmitPackagingScanReport(int64 RequestToken, const FLBPR004PackagingScanReport& Report);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Cycle")
    bool ConfirmCoilSecured(FName EvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Cycle")
    bool AcknowledgePackagingSubstage(int64 ActionToken, ELBPR004ActionSubstage Substage, FName EvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Inspection")
    bool SetCoilTailSecured(bool bSecured, FName EvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Inspection")
    bool SubmitInspectionReport(int64 RequestToken, const FLBPR004InspectionReport& Report);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Inspection")
    bool RequestReinspection(FName ReasonId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Quality")
    bool SetQualityDisposition(ELBPR004Disposition NewDisposition);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Handoff")
    bool RequestHandoff(FName TransactionId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Handoff")
    bool ConfirmHandoffComplete(FName TransactionId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Reject")
    bool RequestRejectedCoilRemoval(FName TransactionId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Reject")
    bool ConfirmRejectedCoilArchived(FName TransactionId, FName ArchiveRecordId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Fault")
    bool RaiseFault(ELBPR004Fault Fault);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Fault")
    bool ResetFault(FName RecoveryEvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Fault")
    bool ReconcilePowerLoss(ELBPR004MaterialOwner ConfirmedOwner, FName RecoveryEvidenceId);

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-004|State")
    ELBPR004State GetProcessState() const { return ProcessState; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-004|State")
    ELBPR004Fault GetActiveFault() const { return ActiveFault; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-004|State")
    ELBPR004Disposition GetDisposition() const { return Disposition; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-004|State")
    FString GetCurrentCoilId() const { return CoilId; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-004|State")
    FString GetCurrentHeatId() const { return HeatId; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-004|State")
    FString GetCurrentSupplierLotId() const { return SupplierLotId; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-004|State")
    FString GetCurrentTraceabilityBarcode() const { return TraceabilityBarcode; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-004|Presentation")
    FString GetWrappedCoilTraceLabelText() const;

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-004|State")
    FName GetActiveRecipeId() const { return ActiveRecipeId; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-004|State")
    FLBPR004ActiveAction GetActivePackagingAction() const { return ActiveAction; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-004|State")
    int64 GetActivePackagingScanRequestToken() const { return ActiveScanRequestToken; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-004|State")
    int64 GetActiveInspectionRequestToken() const { return ActiveInspectionRequestToken; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-004|State")
    float GetPhaseProgress() const;

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-004|State")
    bool IsCoilUnpackaged() const
    {
        return bCoilPresent && RemainingBandMask == 0 && RemainingProtectorMask == 0 && RemainingWrapMask == 0;
    }

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-004|Cycle")
    bool CanAuthoriseCycle(TArray<FText>& OutBlockingReasons) const;

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-004|Handoff")
    bool CanReleaseCoil(TArray<FText>& OutBlockingReasons) const;

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-004|Fault")
    bool CanResetFault(TArray<FText>& OutBlockingReasons) const;

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-004|Save")
    bool IsAtStableSaveBoundary() const;

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-004|Save")
    bool IsSaveStateCoherent(const FLBPR004SaveState& CandidateState, TArray<FText>& OutErrors) const;

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Save")
    bool GetStableSaveState(FLBPR004SaveState& OutState) const;

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|Save")
    bool RestoreSaveState(const FLBPR004SaveState& InState);

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|PR-004|Events")
    FLBPR004StateChanged OnStateChanged;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|PR-004|Events")
    FLBPR004FaultRaised OnFaultRaised;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|PR-004|Events")
    FLBPR004PackagingScanRequested OnPackagingScanRequested;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|PR-004|Events")
    FLBPR004PackagingScanAccepted OnPackagingScanAccepted;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|PR-004|Events")
    FLBPR004PackagingActionRequested OnPackagingActionRequested;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|PR-004|Events")
    FLBPR004PackagingActionAdvanced OnPackagingActionAdvanced;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|PR-004|Events")
    FLBPR004PackagingRemoved OnPackagingRemoved;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|PR-004|Events")
    FLBPR004WasteRecordAppended OnWasteRecordAppended;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|PR-004|Events")
    FLBPR004InspectionRequested OnInspectionRequested;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|PR-004|Events")
    FLBPR004InspectionAccepted OnInspectionAccepted;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|PR-004|Events")
    FLBPR004DispositionChanged OnDispositionChanged;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|PR-004|Events")
    FLBPR004TransferCommand OnHandoffCommandRequested;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|PR-004|Events")
    FLBPR004TransferCommand OnHandoffCompleted;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|PR-004|Events")
    FLBPR004TransferCommand OnRejectedCoilRemovalRequested;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|PR-004|Events")
    FLBPR004RejectArchived OnRejectedCoilArchived;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|PR-004|Events")
    FLBPR004FilmDriveCommand OnFilmDriveCommand;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|PR-004|Events")
    FLBPR004ManualRecoveryChanged OnManualRecoveryChanged;

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TObjectPtr<USceneComponent> StationRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TObjectPtr<USceneComponent> CradleMover;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TObjectPtr<USceneComponent> RobotRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TObjectPtr<USceneComponent> PersistentCoilRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-004|Presentation")
    TObjectPtr<UStaticMeshComponent> WrappedCoilVisual;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-004|Presentation")
    TObjectPtr<UStaticMeshComponent> WrappedCoilLabelVisual;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-004|Presentation")
    TObjectPtr<UTextRenderComponent> WrappedCoilLabelHeading;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-004|Presentation")
    TObjectPtr<UTextRenderComponent> WrappedCoilLabelDetail;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-004|Presentation")
    TObjectPtr<UStaticMeshComponent> WrappedCoilTraceLabelVisual;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-004|Presentation")
    TObjectPtr<UTextRenderComponent> WrappedCoilTraceText;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-004|Presentation")
    TObjectPtr<UTextRenderComponent> WrappedCoilBarcodeText;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-004|HMI")
    TObjectPtr<UWidgetComponent> OperatorHMI;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-004|HMI")
    TObjectPtr<UTextRenderComponent> HMIBrandText;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-004|HMI")
    TObjectPtr<UTextRenderComponent> HMIStationText;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-004|HMI")
    TObjectPtr<UTextRenderComponent> HMIStateText;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-004|HMI")
    TObjectPtr<UTextRenderComponent> HMICoilText;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-004|HMI")
    TObjectPtr<UTextRenderComponent> HMIRecipeText;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-004|HMI")
    TObjectPtr<UTextRenderComponent> HMIChecklistText;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-004|HMI")
    TObjectPtr<UTextRenderComponent> HMIActionText;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-004|Presentation")
    TObjectPtr<UStaticMeshComponent> BareCoilVisual;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TObjectPtr<USceneComponent> InspectionRoot;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Line Boss|Identity")
    FName StationId = TEXT("PR-004");

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Line Boss|Recipe")
    TArray<FName> ApprovedRecipeIds;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|State")
    ELBPR004State ProcessState = ELBPR004State::Unsurveyed;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|State")
    ELBPR004State StateBeforeFault = ELBPR004State::AwaitingAuthorisation;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|State")
    ELBPR004State StateBeforePowerLoss = ELBPR004State::AwaitingAuthorisation;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|State")
    ELBPR004Fault ActiveFault = ELBPR004Fault::None;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Quality")
    ELBPR004Disposition Disposition = ELBPR004Disposition::Unknown;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Coil")
    FString CoilId;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Coil")
    FString HeatId;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Coil")
    FString SupplierLotId;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Coil")
    FString TraceabilityBarcode;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Coil")
    FString ExpectedCoilId;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Coil")
    FName ActiveRecipeId = NAME_None;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Coil")
    int32 RemainingBandMask = 0;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Coil")
    int32 RemainingProtectorMask = 0;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Coil")
    int32 RemainingWrapMask = 0;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Coil")
    int32 AcceptedWrapMask = 0;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Action")
    FLBPR004ActiveAction ActiveAction;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Waste")
    TArray<FLBPR004WasteRecord> WasteLedger;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Reports")
    FLBPR004PackagingScanReport PackagingScanReport;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Reports")
    FLBPR004InspectionReport InspectionReport;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Waste")
    FLBPR004WasteStreamStatus BandStreamStatus;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Waste")
    FLBPR004WasteStreamStatus ProtectorStreamStatus;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Waste")
    FLBPR004WasteStreamStatus PlasticStreamStatus;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Film Dewrap")
    FLBPR004FilmDewrapStatus FilmDewrapStatus;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Waste")
    int32 CompactedBandCoilCount = 0;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Waste")
    int32 CompactedPlasticBaleCount = 0;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Manual Recovery")
    TArray<FName> UnrecoveredWrapFragmentIds;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Manual Recovery")
    TArray<FName> RecoveredWrapFragmentIds;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Manual Recovery")
    bool bManualWrapRecoveryRequired = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Manual Recovery")
    bool bManualWrapRecoveryInProgress = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Manual Recovery")
    bool bRecoveryZeroMotionVerified = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Manual Recovery")
    ELBPR004TrappedKeyState TrappedKeyState = ELBPR004TrappedKeyState::Installed;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Manual Recovery")
    FName ManualRecoveryPermitId = NAME_None;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Manual Recovery")
    FName LastManualRecoveryEvidenceId = NAME_None;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Line Boss|Film Dewrap")
    bool bCradleIndexDriveEnabled = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Line Boss|Film Dewrap")
    bool bFilmSpindleDriveEnabled = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|State")
    bool bControlPowerOn = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|State")
    bool bCellCommissioned = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Coil")
    bool bCoilPresent = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Coil")
    bool bIdentityVerified = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Reports")
    bool bPackagingScanAccepted = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Reports")
    bool bInspectionReportAccepted = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Coil")
    bool bCoilTailSecured = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Coil")
    FName CoilTailEvidenceId = NAME_None;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Interlocks")
    bool bCradleLocked = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Interlocks")
    bool bCHookWithdrawn = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Interlocks")
    bool bGatesClosed = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Interlocks")
    bool bSafetyCircuitHealthy = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Interlocks")
    bool bPersonnelClear = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Interlocks")
    bool bRobotHealthy = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Interlocks")
    bool bPackagingScannerHealthy = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Interlocks")
    bool bInspectionSystemHealthy = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Recovery")
    bool bPowerLossReconciliationRequired = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Transactions")
    FName ActiveHandoffTransactionId = NAME_None;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Transactions")
    FName LastCompletedHandoffTransactionId = NAME_None;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Transactions")
    FName ActiveRejectRemovalTransactionId = NAME_None;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Transactions")
    FName LastCompletedRejectRemovalTransactionId = NAME_None;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Transactions")
    FName LastRejectArchiveRecordId = NAME_None;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Transactions")
    FString LastCompletedCoilId;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Transactions")
    int64 LastCompletedCycleSerial = 0;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Line Boss|Tuning", meta = (ClampMin = "0.1", ClampMax = "10.0"))
    float CycleSpeedMultiplier = 1.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Line Boss|Tuning", meta = (ClampMin = "1.0", ClampMax = "120.0"))
    float PackagingActionTimeoutSeconds = 30.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Line Boss|Tuning", meta = (ClampMin = "1.0", ClampMax = "120.0"))
    float ReportTimeoutSeconds = 30.0f;

private:
    static constexpr int32 FullBandMask = 0x0F;
    static constexpr int32 FullProtectorMask = 0xFF;
    static constexpr int32 FullWrapMask = 0xFFFF;
    static constexpr int32 CurrentSaveVersion = 4;

    int64 ActiveCycleSerial = 0;
    int64 NextCycleSerial = 1;
    int64 NextActionToken = 1;
    int64 NextReportRequestToken = 1;
    int64 ActiveScanRequestToken = 0;
    int64 ActiveInspectionRequestToken = 0;
    float PhaseElapsedSeconds = 0.0f;
    float ItemElapsedSeconds = 0.0f;
    float HMIRefreshAccumulator = 0.0f;
    bool bMutationInProgress = false;
    bool bDispatchingEvents = false;

    bool CanBeginExternalMutation() const;
    void SetProcessStateInternal(ELBPR004State NewState, bool bIssueCommands);
    void RaiseFaultInternal(ELBPR004Fault Fault);
    void AdvanceAutomaticSequence(float DeltaSeconds);
    void TryResumeAfterCraneClearance();
    void CreateNextPackagingAction(bool bBroadcastCommand);
    void BroadcastActiveActionRequest();
    void CreateInspectionRequest(bool bBroadcastCommand);
    bool FinalizeActiveAction(FName EvidenceId);
    bool AppendWasteRecordIfAbsent(const FLBPR004WasteRecord& Record, bool& bOutWasAppended);
    void ClearActiveAction();
    void ResetActiveCycleAfterTransfer();
    void ResumeAfterPowerLossWithoutCommand();
    void StopFilmDrives();
    void StartFilmDrives();
    void UpdateCoilPresentation();
    void UpdateTraceabilityPresentation();
    void UpdateHMITextPresentation();

    bool IsPackagingRemovalState(ELBPR004State State) const;
    bool IsHazardousMotionState(ELBPR004State State) const;
    bool SafetyEnvelopeHealthy() const;
    bool StateSpecificMotionInterlocksHealthy() const;
    bool IsWasteStreamReady(ELBPR004WasteStream Stream, bool bRequireEject, ELBPR004Fault& OutFault) const;
    bool IsApprovedRecipe(FName RecipeId) const;
    bool ValidateReleaseInvariants(TArray<FText>& OutBlockingReasons, bool bRequireReadyDisposition) const;
    bool FaultRecoverySatisfied(FName RecoveryEvidenceId, TArray<FText>& OutBlockingReasons) const;
    bool ValidateActiveActionCoherence(const FLBPR004SaveState& CandidateState, TArray<FText>& OutErrors) const;
    bool ValidateWasteLedgerCoherence(const FLBPR004SaveState& CandidateState, TArray<FText>& OutErrors) const;
    int32 CountWasteRecordsForCycle(int64 CycleSerial, ELBPR004WasteStream Stream, FName WasteType) const;
    float GetCurrentPhaseDuration() const;
    ELBPR004Fault TimeoutFaultForActiveAction() const;
    ELBPR004ActionSubstage ExpectedNextSubstage() const;
    static int32 FindFirstSetBit(int32 Mask, int32 MaximumItems);
    static int32 CountSetBits(int32 Mask);
    static bool IsStableStateValue(ELBPR004State State);
    static ELBPR004MaterialOwner OwnerForSubstage(ELBPR004ActionSubstage Substage);
};
