#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBSupportRobotServiceDock.generated.h"

class ALBSupportRobot;
class UBoxComponent;
class UStaticMesh;
class UStaticMeshComponent;

UENUM(BlueprintType)
enum class ELBServiceDockVariant : uint8
{
    CR01_Cleaning,
    MR01_Maintenance
};

UENUM(BlueprintType)
enum class ELBServiceDockState : uint8
{
    SafeClosed,
    ProvingRobot,
    Opening,
    ServiceReady,
    Closing,
    SafetyStop,
    Fault
};

USTRUCT(BlueprintType)
struct FLBServiceDockSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Version = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName DockId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBServiceDockVariant Variant = ELBServiceDockVariant::CR01_Cleaning;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 CompletedServiceCycles = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bInspectionDue = false;
};

/**
 * Physical authority for one CR01 or MR01 berth.
 *
 * Mechanisms only open for the correctly docked, stationary robot after the
 * safety zone and operator permit are proved. Save restore is intentionally
 * fail-safe: powered movement is never resumed and every mover returns closed.
 */
UCLASS(BlueprintType, Blueprintable)
class LINEBOSSCARFACTORY_API ALBSupportRobotServiceDock : public AActor
{
    GENERATED_BODY()

public:
    ALBSupportRobotServiceDock();

    virtual void OnConstruction(const FTransform& Transform) override;
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Line Boss|Service Dock|Configuration")
    bool ConfigureDock(FName NewDockId, ELBServiceDockVariant NewVariant);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Service Dock|Safety")
    void SetServicePermissives(bool bSafetyZoneClear, bool bOperatorPermitGranted, bool bIsolationHealthy);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Service Dock|Service")
    bool BeginServiceSequence();

    UFUNCTION(BlueprintCallable, Category="Line Boss|Service Dock|Service")
    bool CompleteServiceSequence();

    UFUNCTION(BlueprintCallable, Category="Line Boss|Service Dock|Safety")
    void ForceSafeClose(const FString& Reason);

    UFUNCTION(BlueprintPure, Category="Line Boss|Service Dock|State")
    ELBServiceDockState GetDockState() const { return DockState; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Service Dock|State")
    bool IsServiceReady() const { return DockState == ELBServiceDockState::ServiceReady; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Service Dock|Identity")
    FName GetDockId() const { return DockId; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Service Dock|Save")
    FLBServiceDockSaveState CaptureSaveState() const;

    UFUNCTION(BlueprintCallable, Category="Line Boss|Service Dock|Save")
    bool RestoreSaveState(const FLBServiceDockSaveState& SavedState);

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Line Boss|Service Dock|Components")
    TObjectPtr<UBoxComponent> BlockingEnvelope;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Line Boss|Service Dock|Components")
    TObjectPtr<UBoxComponent> StructuralLeft;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Line Boss|Service Dock|Components")
    TObjectPtr<UBoxComponent> StructuralRight;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Line Boss|Service Dock|Components")
    TObjectPtr<UBoxComponent> StructuralHeader;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Line Boss|Service Dock|Components")
    TObjectPtr<UStaticMeshComponent> StaticBody;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Line Boss|Service Dock|Components")
    TObjectPtr<UStaticMeshComponent> CalibrationProbe;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Line Boss|Service Dock|Components")
    TObjectPtr<UStaticMeshComponent> ToolRackDoor;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Line Boss|Service Dock|Components")
    TObjectPtr<UStaticMeshComponent> WasteDrawer;

    UPROPERTY(EditInstanceOnly, BlueprintReadOnly, SaveGame, Category="Line Boss|Service Dock|Identity")
    FName DockId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Service Dock|Identity")
    ELBServiceDockVariant Variant = ELBServiceDockVariant::MR01_Maintenance;

private:
    UPROPERTY(Transient)
    TObjectPtr<UStaticMesh> MR01StaticMesh;

    UPROPERTY(Transient)
    TObjectPtr<UStaticMesh> CR01StaticMesh;

    UPROPERTY(Transient)
    TObjectPtr<UStaticMesh> MR01ResolvedMaterialSource;

    UPROPERTY(Transient)
    TObjectPtr<UStaticMesh> CR01ResolvedMaterialSource;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category="Line Boss|Service Dock|State")
    ELBServiceDockState DockState = ELBServiceDockState::SafeClosed;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category="Line Boss|Service Dock|State")
    int32 CompletedServiceCycles = 0;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category="Line Boss|Service Dock|State")
    bool bInspectionDue = false;

    bool bSafetyZoneClear = false;
    bool bOperatorPermitGranted = false;
    bool bIsolationHealthy = false;
    float MechanismAlpha = 0.0f;
    FString LastSafeStopReason;

    static constexpr float MechanismTravelSeconds = 2.0f;

    void ApplyVariantPresentation();
    void ApplyResolvedMaterialOverrides(UStaticMeshComponent* TargetComponent, UStaticMesh* MaterialSource);
    void ApplyMechanismPose();
    ALBSupportRobot* FindCompatibleDockedRobot() const;
    bool HasServicePermissives() const;
};
