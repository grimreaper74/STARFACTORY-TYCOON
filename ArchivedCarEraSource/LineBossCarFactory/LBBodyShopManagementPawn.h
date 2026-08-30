#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "LBBodyShopManagementPawn.generated.h"

class UCameraComponent;
class UFloatingPawnMovement;
class USceneComponent;
class USpringArmComponent;
class ALBBodyShopPrototypeRuntime;
class ALBBodyShopPrototypeWorldBootstrap;

/** Pure result used to frame either the live process footprint or its safe fallback. */
struct LINEBOSSCARFACTORY_API FLBBodyShopCameraFocusContract
{
    FVector Target = FVector::ZeroVector;
    float ZoomDistanceCm = 3400.0f;
    FRotator Rotation = FRotator(-30.0f, 55.0f, 0.0f);
    float FieldOfViewDegrees = 60.0f;
    bool bUsedProcessBounds = false;
};

/**
 * Small, map-isolated management camera for the Body Shop prototype.
 * It is intentionally a camera/placement shell: it does not inherit any legacy
 * Press Shop input, campaign, UI or actor-selection authority.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBBodyShopManagementPawn : public APawn
{
    GENERATED_BODY()

public:
    ALBBodyShopManagementPawn();

    virtual void BeginPlay() override;
    virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;

    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Prototype|Camera")
    bool FocusPrototypeBuildOrigin();

    /**
     * Frames commissioned cells owned by the prototype build authority. When no
     * commissioned cells exist it frames any valid placed cells, then falls back
     * to the map bootstrap origin while the isolated slice is still being built.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Prototype|Camera")
    bool FocusPrototypeProcess();

    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Prototype|Camera")
    void SetPrototypeZoomInput(float Value);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Prototype|Configuration")
    void SetRobotSlotOverlayRequested(bool bVisible);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Prototype|Configuration")
    void ToggleRobotSlotOverlay();

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|Configuration")
    bool IsRobotSlotOverlayRequested() const { return bRobotSlotOverlayRequested; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|Camera")
    float GetPrototypeZoomDistance() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|Camera")
    FVector GetPrototypeBuildOrigin() const { return PrototypeBuildOrigin; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|Controls")
    FString GetLastPrototypeActionStatus() const { return LastPrototypeActionStatus; }

    static float ClampPrototypeZoomDistance(float InDistanceCm);

    /** Pure deterministic release-comparison framing contract used by automation. */
    static FLBBodyShopCameraFocusContract BuildFocusContract(
        const FBox& ProcessBounds, const FVector& FallbackBuildOrigin);

private:
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Body Shop|Prototype")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Body Shop|Prototype")
    TObjectPtr<USpringArmComponent> CameraBoom;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Body Shop|Prototype")
    TObjectPtr<UCameraComponent> Camera;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Body Shop|Prototype")
    TObjectPtr<UFloatingPawnMovement> CameraMovement;

    UPROPERTY(EditDefaultsOnly, Category="Line Boss|Body Shop|Prototype|Camera",
        meta=(ClampMin="1000.0", ClampMax="25000.0"))
    float InitialZoomDistanceCm = 3400.0f;

    bool bRobotSlotOverlayRequested = false;
    FString LastPrototypeActionStatus = TEXT("Ready for operator input");
    FVector PrototypeBuildOrigin = FVector::ZeroVector;
    TWeakObjectPtr<ALBBodyShopPrototypeWorldBootstrap> PrototypeBootstrap;

    void MoveForward(float Value);
    void MoveRight(float Value);
    void LookYaw(float Value);
    void LookPitch(float Value);
    void HandleCameraReset();
    void HandlePrototypeStartPause();
    void HandlePrototypeSave();
    void HandlePrototypeLoad();
    void HandlePrototypeClearHeld();
    void ApplyFocusContract(const FLBBodyShopCameraFocusContract& Contract);
    ALBBodyShopPrototypeWorldBootstrap* FindPrototypeBootstrap() const;
    ALBBodyShopPrototypeRuntime* FindPrototypeRuntime() const;
};
