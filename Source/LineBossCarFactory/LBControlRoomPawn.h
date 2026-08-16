#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "LBControlRoomPawn.generated.h"

class UCameraComponent;
class UCapsuleComponent;
class UFloatingPawnMovement;
class USceneComponent;
class UWidgetInteractionComponent;

/**
 * Standing-first operator for the Moorcross Works main control room.
 *
 * The player can walk between consoles immediately. Sitting at the authored
 * operator chair remains optional, and the player must return to the chair
 * before entering its locked overview view.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBControlRoomPawn : public APawn
{
    GENERATED_BODY()

public:
    ALBControlRoomPawn();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;

    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Control Room|Interaction")
    bool InteractWithActor(AActor* TargetActor);

    /** Controller-friendly interaction trace through the centre of the operator view. */
    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Control Room|Interaction")
    void InteractAtViewCentre();

    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Control Room|View")
    bool FocusOnActor(AActor* TargetActor);

    UFUNCTION(Exec, BlueprintCallable, Category = "Cairnwell|Control Room|View")
    void FocusSelectedCCTV();

    UFUNCTION(Exec, Category = "Cairnwell|Control Room|Validation")
    void CaptureOperatorEvidence();

    UFUNCTION(BlueprintPure, Category = "Cairnwell|Control Room|View")
    FVector GetLockedSeatLocation() const { return LockedSeatLocation; }

    UFUNCTION(BlueprintPure, Category = "Cairnwell|Control Room|View")
    float GetCurrentFieldOfView() const;

    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Control Room|Operator")
    void ToggleSeatState();

    UFUNCTION(BlueprintPure, Category = "Cairnwell|Control Room|Operator")
    bool IsStanding() const { return bStanding; }

    UFUNCTION(BlueprintPure, Category = "Cairnwell|Control Room|Operator")
    bool CanSitAtChair() const;

    /** Switches from the standing control room to the overhead factory management camera. */
    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Control Room|Management")
    bool EnterManagementView();

private:
    UPROPERTY(VisibleAnywhere, Category = "Cairnwell|Control Room")
    TObjectPtr<UCapsuleComponent> OperatorCollision;

    UPROPERTY(VisibleAnywhere, Category = "Cairnwell|Control Room")
    TObjectPtr<USceneComponent> SeatRoot;

    UPROPERTY(VisibleAnywhere, Category = "Cairnwell|Control Room")
    TObjectPtr<UCameraComponent> Camera;

    UPROPERTY(VisibleAnywhere, Category = "Cairnwell|Control Room")
    TObjectPtr<UWidgetInteractionComponent> WidgetInteraction;

    UPROPERTY(VisibleAnywhere, Category = "Cairnwell|Control Room")
    TObjectPtr<UFloatingPawnMovement> WalkingMovement;

    UPROPERTY(EditDefaultsOnly, Category = "Cairnwell|Control Room|View", meta = (ClampMin = "10.0", ClampMax = "120.0"))
    float MaximumYawOffsetDegrees = 70.0f;

    UPROPERTY(EditDefaultsOnly, Category = "Cairnwell|Control Room|View", meta = (ClampMin = "5.0", ClampMax = "80.0"))
    float MaximumPitchOffsetDegrees = 35.0f;

    UPROPERTY(EditDefaultsOnly, Category = "Cairnwell|Control Room|View", meta = (ClampMin = "25.0", ClampMax = "112.0"))
    float MinimumFieldOfView = 36.0f;

    UPROPERTY(EditDefaultsOnly, Category = "Cairnwell|Control Room|View", meta = (ClampMin = "52.0", ClampMax = "120.0"))
    float MaximumFieldOfView = 112.0f;

    UPROPERTY(EditDefaultsOnly, Category = "Cairnwell|Control Room|View", meta = (ClampMin = "25.0", ClampMax = "70.0"))
    float FocusedScreenFieldOfView = 38.0f;

    UPROPERTY(EditDefaultsOnly, Category = "Cairnwell|Control Room|Operator")
    float SeatedCameraHeightCm = 42.0f;

    UPROPERTY(EditDefaultsOnly, Category = "Cairnwell|Control Room|Operator")
    float SeatedCameraForwardOffsetCm = 30.0f;

    UPROPERTY(EditDefaultsOnly, Category = "Cairnwell|Control Room|Operator")
    float StandingCameraHeightCm = 80.0f;

    UPROPERTY(EditDefaultsOnly, Category = "Cairnwell|Control Room|Operator")
    float ChairSitRadiusCm = 140.0f;

    UPROPERTY(EditDefaultsOnly, Category = "Cairnwell|Control Room|Operator")
    FVector2D StandingRoomHalfExtentCm = FVector2D(550.0f, 310.0f);

    FVector LockedSeatLocation = FVector::ZeroVector;
    FRotator InitialControlRotation = FRotator::ZeroRotator;
    float PendingYawInput = 0.0f;
    float PendingPitchInput = 0.0f;
    float PendingZoomInput = 0.0f;
    bool bStanding = true;

    void MoveForward(float Value);
    void MoveRight(float Value);
    void LookYaw(float Value);
    void LookPitch(float Value);
    void Zoom(float Value);
    void ResetView();
    void InteractUnderCursor();
    void EndPointerInteraction();
    void ToggleManagement();
    void ManagementNextPage();
    void ManagementPreviousPage();
    void ManagementNextAction();
    void ManagementPreviousAction();
    void ManagementConfirm();
    bool IsManagementOpen() const;
};
