#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBSupportCraneController.generated.h"

UENUM(BlueprintType)
enum class ELBSupportCranePhase : uint8
{
    Parked,
    DispatchingBridge,
    DispatchingTrolley,
    LoweringForSupport,
    OnStation,
    RaisingToTravel,
    ReturningTrolley,
    ReturningBridge,
    Complete,
    Fault
};

UENUM(BlueprintType)
enum class ELBSupportCraneFault : uint8
{
    None,
    BindingIncomplete,
    ControlPowerLost,
    RouteOrPersonnelUnsafe,
    MaintenancePermitMissing,
    SupportZoneNotReserved,
    PrimaryCraneConflict,
    RestoreInterlockStop
};

USTRUCT(BlueprintType)
struct FLBSupportCraneSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 SaveVersion = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBSupportCranePhase Phase = ELBSupportCranePhase::Parked;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBSupportCranePhase PhaseBeforeFault = ELBSupportCranePhase::Parked;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBSupportCraneFault Fault = ELBSupportCraneFault::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName ServicePointId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float BridgeX = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float TrolleyY = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float HookZ = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bStableState = true;
};

/**
 * Authority for the front-end 30 t support/maintenance crane. This controller
 * deliberately has no coil source, PR-004 deposit or material-ownership API;
 * the 40 t bridge crane remains the sole master-coil transfer authority.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBSupportCraneController : public AActor
{
    GENERATED_BODY()

public:
    ALBSupportCraneController();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Crane|Binding")
    bool DiscoverAndBind();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Crane|Support")
    bool DispatchToConfiguredServicePoint();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Crane|Support")
    bool ReturnToPark();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Crane|Safety")
    bool SetSafetyInputs(bool bRouteIsClear, bool bPersonnelAreClear,
        bool bMaintenancePermitIsActive, bool bSupportZoneIsReserved);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Crane|Safety")
    bool SetPrimaryCraneClear(bool bIsClear);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Crane|Safety")
    bool SetControlPower(bool bEnabled);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Crane|Fault")
    bool ResetFault(FName RecoveryEvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Crane|Save")
    bool GetSaveState(FLBSupportCraneSaveState& OutState) const;

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Crane|Save")
    bool RestoreSaveState(const FLBSupportCraneSaveState& InState);

    UFUNCTION(BlueprintPure, Category = "Line Boss|Crane|State")
    ELBSupportCranePhase GetPhase() const { return Phase; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Crane|State")
    ELBSupportCraneFault GetFault() const { return ActiveFault; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Crane|State")
    bool CanHandleMasterCoils() const { return false; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Crane|State")
    bool IsAtServicePoint() const { return Phase == ELBSupportCranePhase::OnStation; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Crane|State")
    bool IsParked() const { return Phase == ELBSupportCranePhase::Parked; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Crane|State")
    float GetBridgeX() const { return BridgeX; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Crane|State")
    float GetTrolleyY() const { return TrolleyY; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Crane|State")
    float GetHookZ() const { return HookZ; }

protected:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Crane|Binding")
    FName CraneTag = TEXT("LB.Crane.30T");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Crane|Binding")
    FName ConfiguredServicePointTag = TEXT("LB.Crane.SupportPoint.FrontEndMaintenance");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Crane|Motion", meta = (ClampMin = "1.0"))
    float BridgeSpeedCmPerSecond = 220.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Crane|Motion", meta = (ClampMin = "1.0"))
    float TrolleySpeedCmPerSecond = 160.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Crane|Motion", meta = (ClampMin = "1.0"))
    float HoistSpeedCmPerSecond = 120.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Crane|Motion", meta = (ClampMin = "0.0"))
    float CompleteHoldSeconds = 0.5f;

private:
    struct FBoundCraneActor
    {
        TWeakObjectPtr<AActor> Actor;
        FVector InitialLocation = FVector::ZeroVector;
        FVector InitialScale = FVector::OneVector;
        bool bReeving = false;
    };

    UPROPERTY(Transient)
    TObjectPtr<AActor> ServicePointActor;

    TArray<FBoundCraneActor> BridgeActors;
    TArray<FBoundCraneActor> TrolleyActors;
    TArray<FBoundCraneActor> HoistActors;
    TArray<FBoundCraneActor> HookActors;

    ELBSupportCranePhase Phase = ELBSupportCranePhase::Parked;
    ELBSupportCranePhase PhaseBeforeFault = ELBSupportCranePhase::Parked;
    ELBSupportCraneFault ActiveFault = ELBSupportCraneFault::None;
    float BridgeX = 0.0f;
    float TrolleyY = 0.0f;
    float HookZ = 0.0f;
    float HomeBridgeX = 0.0f;
    float HomeTrolleyY = 0.0f;
    float HomeHookZ = 0.0f;
    float ServiceBridgeX = 0.0f;
    float ServiceTrolleyY = 0.0f;
    float ServiceHookZ = 0.0f;
    float PhaseElapsedSeconds = 0.0f;
    bool bControlPowerOn = true;
    bool bRouteClear = true;
    bool bPersonnelClear = true;
    bool bMaintenancePermitActive = false;
    bool bSupportZoneReserved = false;
    bool bPrimaryCraneClear = true;
    bool bBound = false;

    bool DispatchSafetyHealthy() const;
    bool IsMotionPhase(ELBSupportCranePhase Candidate) const;
    bool IsStablePhase(ELBSupportCranePhase Candidate) const;
    ELBSupportCraneFault CurrentSafetyFault() const;
    void EnterPhase(ELBSupportCranePhase NewPhase);
    void LatchFault(ELBSupportCraneFault Fault);
    bool MoveAxis(float& Value, float Target, float Speed, float DeltaSeconds);
    void ApplyPose();
    void BindActor(AActor* Actor, TArray<FBoundCraneActor>& Group, bool bReeving = false);
};
