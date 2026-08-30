#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBBridgeCraneController.generated.h"

class ALBPR004Station;

UENUM(BlueprintType)
enum class ELBBridgeCranePhase : uint8
{
    Idle,
    BridgeToPickup,
    TrolleyToPickup,
    LoweringToPickup,
    SecuringLoad,
    RaisingLoad,
    BridgeToDrop,
    TrolleyToDrop,
    LoweringToDrop,
    Depositing,
    WithdrawingHook,
    Complete,
    Fault
};

UENUM(BlueprintType)
enum class ELBBridgeCraneFault : uint8
{
    None,
    BindingIncomplete,
    ControlPowerLost,
    RouteOrPersonnelUnsafe,
    SourceCoilUnavailable,
    PR004RejectedDeposit
};

USTRUCT(BlueprintType)
struct FLBBridgeCraneSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 SaveVersion = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBBridgeCranePhase Phase = ELBBridgeCranePhase::Idle;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBBridgeCranePhase PhaseBeforeFault = ELBBridgeCranePhase::Idle;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBBridgeCraneFault Fault = ELBBridgeCraneFault::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FString CoilId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float BridgeX = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float TrolleyY = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float HookZ = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float PhaseElapsedSeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bCarryingCoil = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bSourceCoilConsumed = false;
};

/**
 * Reusable authority for a tagged modular overhead crane. It drives the
 * existing bridge/trolley/hoist/C-hook actors as one mechanism and transfers
 * a real packaged-coil actor into PR-004 without visual teleporting.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBBridgeCraneController : public AActor
{
    GENERATED_BODY()

public:
    ALBBridgeCraneController();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Crane|Binding")
    bool DiscoverAndBind();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Crane|Transfer")
    bool StartConfiguredTransfer();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Crane|Transfer")
    bool StartTransfer(const FString& CoilId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Crane|Safety")
    bool SetSafetyInputs(bool bRouteIsClear, bool bPersonnelAreClear, bool bTransferGateIsClosed);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Crane|Safety")
    bool SetControlPower(bool bEnabled);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Crane|Fault")
    bool ResetFault(FName RecoveryEvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Crane|Save")
    bool GetSaveState(FLBBridgeCraneSaveState& OutState) const;

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Crane|Save")
    bool RestoreSaveState(const FLBBridgeCraneSaveState& InState);

    UFUNCTION(BlueprintPure, Category = "Line Boss|Crane|State")
    ELBBridgeCranePhase GetPhase() const { return Phase; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Crane|State")
    ELBBridgeCraneFault GetFault() const { return ActiveFault; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Crane|State")
    bool IsCarryingCoil() const { return bCarryingCoil; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Crane|State")
    bool IsTransferComplete() const { return Phase == ELBBridgeCranePhase::Complete; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Crane|State")
    float GetBridgeX() const { return BridgeX; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Crane|State")
    float GetTrolleyY() const { return TrolleyY; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Crane|State")
    float GetHookZ() const { return HookZ; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Crane|State")
    float GetLoadCentreBelowHookCm() const { return PickupHookZOffset; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Crane|State")
    float GetMaxLoadFollowErrorCm() const { return MaxLoadFollowErrorCm; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Crane|State")
    float GetMaxAttachmentFollowErrorCm() const { return MaxAttachmentFollowErrorCm; }

protected:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Crane|Binding")
    FName CraneTag = TEXT("LB.Crane.40T");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Crane|Binding")
    FName SourceCoilTag = TEXT("LB.CoilSlot.CS-10");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Crane|Binding")
    FName SourceAttachmentTag = TEXT("LB.CoilSlot.CS-10.Attachment");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Crane|Transfer")
    FString ConfiguredCoilId = TEXT("MCX-U-CS10-0001");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Crane|Transfer")
    FString ConfiguredHeatId = TEXT("HT-CW26-08417");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Crane|Transfer")
    FString ConfiguredSupplierLotId = TEXT("LOT-MCXU-260804-A");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Crane|Transfer")
    FString ConfiguredTraceabilityBarcode = TEXT("503184064100010");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Crane|Motion", meta = (ClampMin = "1.0"))
    float BridgeSpeedCmPerSecond = 260.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Crane|Motion", meta = (ClampMin = "1.0"))
    float TrolleySpeedCmPerSecond = 180.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Crane|Motion", meta = (ClampMin = "1.0"))
    float HoistSpeedCmPerSecond = 150.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Crane|Motion")
    float SafeHookZ = 820.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Crane|Motion")
    // The authored C-hook's padded lower bore arm is 59 cm below its actor
    // datum.  The carried coil centre must stay on that arm, not float at the
    // hook datum.
    float PickupHookZOffset = 59.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Crane|Motion")
    float DropHookZOffset = 59.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Crane|Motion", meta = (ClampMin = "0.0"))
    float SecureDelaySeconds = 0.75f;

private:
    struct FBoundCraneActor
    {
        TWeakObjectPtr<AActor> Actor;
        FVector InitialLocation = FVector::ZeroVector;
        FVector InitialScale = FVector::OneVector;
        bool bReeving = false;
    };

    UPROPERTY(Transient)
    TObjectPtr<ALBPR004Station> PR004Station;

    UPROPERTY(Transient)
    TObjectPtr<AActor> SourceCoilActor;

    TArray<FBoundCraneActor> BridgeActors;
    TArray<FBoundCraneActor> TrolleyActors;
    TArray<FBoundCraneActor> HoistActors;
    TArray<FBoundCraneActor> HookActors;
    TArray<FBoundCraneActor> SourceAttachmentActors;

    ELBBridgeCranePhase Phase = ELBBridgeCranePhase::Idle;
    ELBBridgeCranePhase PhaseBeforeFault = ELBBridgeCranePhase::Idle;
    ELBBridgeCraneFault ActiveFault = ELBBridgeCraneFault::None;
    FString ActiveCoilId;
    float BridgeX = 0.0f;
    float TrolleyY = 0.0f;
    float HookZ = 0.0f;
    float InitialBridgeX = 0.0f;
    float InitialTrolleyY = 0.0f;
    float InitialHookZ = 0.0f;
    float PickupX = 0.0f;
    float PickupY = 0.0f;
    float PickupZ = 0.0f;
    float DropX = 0.0f;
    float DropY = 0.0f;
    float DropZ = 0.0f;
    float PhaseElapsedSeconds = 0.0f;
    bool bControlPowerOn = true;
    bool bRouteClear = true;
    bool bPersonnelClear = true;
    bool bTransferGateClosed = true;
    bool bCarryingCoil = false;
    bool bSourceCoilConsumed = false;
    bool bBound = false;
    float MaxLoadFollowErrorCm = 0.0f;
    float MaxAttachmentFollowErrorCm = 0.0f;

    bool SafetyHealthy() const;
    bool IsMotionPhase(ELBBridgeCranePhase Candidate) const;
    void EnterPhase(ELBBridgeCranePhase NewPhase);
    void LatchFault(ELBBridgeCraneFault Fault);
    bool MoveAxis(float& Value, float Target, float Speed, float DeltaSeconds);
    void ApplyPose();
    void BindActor(AActor* Actor, TArray<FBoundCraneActor>& Group, bool bReeving = false);
    void SetSourcePresentation(bool bVisible, bool bCollisionEnabled);
};
