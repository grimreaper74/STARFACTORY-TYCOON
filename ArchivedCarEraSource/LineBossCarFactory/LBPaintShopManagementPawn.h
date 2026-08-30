#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "LBPaintShopManagementPawn.generated.h"

class ALBPaintShopPrototypeWorldBootstrap;
class ALBPaintShopPrototypeGameMode;
class UCameraComponent;
class UFloatingPawnMovement;
class USceneComponent;
class USpringArmComponent;

/** Deterministic framing for the approved 1,800 x 1,000 cm ED-coat cell. */
struct LINEBOSSCARFACTORY_API FLBPaintShopCameraFocusContract
{
    FVector Target = FVector(0.0f, 0.0f, 426.5f);
    float ZoomDistanceCm = 2700.0f;
    FRotator Rotation = FRotator(-32.0f, 45.0f, 0.0f);
    float FieldOfViewDegrees = 55.0f;
    FVector CellDimensionsCm = FVector(1800.0f, 1000.0f, 853.0f);
};

/**
 * Paint-only management camera for the isolated ED-coat prototype. It consumes
 * the existing generic camera mappings and delegates deterministic operator keys
 * to the GameMode; it owns no process, save, lineage or build authority.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBPaintShopManagementPawn : public APawn
{
    GENERATED_BODY()

public:
    ALBPaintShopManagementPawn();

    virtual void BeginPlay() override;
    virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;

    /** Focuses only a coherent, Ready bootstrap-owned ED-coat cell. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Prototype|Camera")
    bool FocusEDCoatCell(ALBPaintShopPrototypeWorldBootstrap* Bootstrap);

    /** Requires exactly one live Paint prototype bootstrap in this world. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Prototype|Camera")
    bool FocusEDCoatCellFromWorld();

    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Prototype|Camera")
    void SetPrototypeZoomInput(float Value);

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Prototype|Camera")
    float GetPrototypeZoomDistance() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Prototype|Camera")
    FString GetCameraStatus() const { return CameraStatus; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Prototype|Camera")
    bool IsBoundToPrototypeBootstrap(
        ALBPaintShopPrototypeWorldBootstrap* InBootstrap) const;

    static float ClampPrototypeZoomDistance(float InDistanceCm);
    static FLBPaintShopCameraFocusContract BuildEDCoatFocusContract(
        const FTransform& CellWorldTransform);

private:
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Paint Shop|Prototype|Camera")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Paint Shop|Prototype|Camera")
    TObjectPtr<USpringArmComponent> CameraBoom;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Paint Shop|Prototype|Camera")
    TObjectPtr<UCameraComponent> Camera;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Paint Shop|Prototype|Camera")
    TObjectPtr<UFloatingPawnMovement> CameraMovement;

    UPROPERTY(Transient)
    TWeakObjectPtr<ALBPaintShopPrototypeWorldBootstrap> PrototypeBootstrap;

    FString CameraStatus = TEXT("WAITING FOR READY ED-COAT CELL");

    void PanForward(float Value);
    void PanRight(float Value);
    void OrbitYaw(float Value);
    void OrbitPitch(float Value);
    void HandleCameraReset();
    void HandleStartCanonicalWeldHandoff();
    void HandleToggleProcessPause();
    void HandleToggleOutputBlock();
    void HandleReleasePaintOutput();
    void HandleSavePaintState();
    void HandleLoadPaintState();
    ALBPaintShopPrototypeGameMode* ResolveOperatorGameMode() const;
    void ApplyFocusContract(const FLBPaintShopCameraFocusContract& Contract);
};
