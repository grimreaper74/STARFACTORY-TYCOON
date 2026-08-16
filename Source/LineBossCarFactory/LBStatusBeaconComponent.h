#pragma once

#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "LBStatusBeaconComponent.generated.h"

class UMaterialInstanceDynamic;
class UMaterialInterface;
class UPointLightComponent;
class UStaticMesh;
class UStaticMeshComponent;

/**
 * Plant-wide status language shared by machines, support robots and AGVs.
 *
 * Green is ready/running, amber is idle/waiting, a flashing amber beacon means
 * mobile equipment is moving, and red is stopped/faulted. Emergency is a
 * flashing red beacon.  The component owns both emissive lamp heads and small
 * real point lights, so a replacement Meshy body does not need special material
 * slots before its runtime safety state is readable.
 */
UENUM(BlueprintType)
enum class ELBStatusBeaconState : uint8
{
    Off,
    Ready,
    Running,
    Idle,
    Waiting,
    Moving,
    Stopped,
    Fault,
    Emergency
};

UCLASS(ClassGroup=(LineBoss), meta=(BlueprintSpawnableComponent))
class LINEBOSSCARFACTORY_API ULBStatusBeaconComponent : public USceneComponent
{
    GENERATED_BODY()

public:
    ULBStatusBeaconComponent();

    virtual void OnRegister() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType,
        FActorComponentTickFunction* ThisTickFunction) override;

    UFUNCTION(BlueprintCallable, Category="Line Boss|Status Beacon")
    void SetStatus(ELBStatusBeaconState NewStatus);

    UFUNCTION(BlueprintPure, Category="Line Boss|Status Beacon")
    ELBStatusBeaconState GetStatus() const { return Status; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Status Beacon")
    bool IsGreenLampLit() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Status Beacon")
    bool IsAmberLampLit() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Status Beacon")
    bool IsRedLampLit() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Status Beacon")
    bool IsFlashing() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Status Beacon")
    bool IsFlashOn() const { return bFlashOn; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Status Beacon")
    UPointLightComponent* GetGreenLight() const { return GreenLight; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Status Beacon")
    UPointLightComponent* GetAmberLight() const { return AmberLight; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Status Beacon")
    UPointLightComponent* GetRedLight() const { return RedLight; }

    /** Keeps real lights active while allowing an approved body to supply its own lamp-head geometry. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Status Beacon")
    void SetGeneratedLampHeadsVisible(bool bShowLampHeads);

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Line Boss|Status Beacon|Visual")
    TObjectPtr<UStaticMeshComponent> Mast;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Line Boss|Status Beacon|Visual")
    TObjectPtr<UStaticMeshComponent> GreenLens;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Line Boss|Status Beacon|Visual")
    TObjectPtr<UStaticMeshComponent> AmberLens;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Line Boss|Status Beacon|Visual")
    TObjectPtr<UStaticMeshComponent> RedLens;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Line Boss|Status Beacon|Light")
    TObjectPtr<UPointLightComponent> GreenLight;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Line Boss|Status Beacon|Light")
    TObjectPtr<UPointLightComponent> AmberLight;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Line Boss|Status Beacon|Light")
    TObjectPtr<UPointLightComponent> RedLight;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Status Beacon|Light", meta=(ClampMin="0.0"))
    float ActiveLightIntensity = 650.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Status Beacon|Light", meta=(ClampMin="1.0"))
    float AttenuationRadiusCm = 180.0f;

    /** Full on/off flash cycle, not the half-cycle. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Status Beacon|Timing", meta=(ClampMin="0.1"))
    float FlashPeriodSeconds = 0.8f;

private:
    UPROPERTY(Transient) TObjectPtr<UStaticMesh> CylinderMesh;
    UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MastMaterialParent;
    UPROPERTY(Transient) TObjectPtr<UMaterialInterface> LensMaterialParent;
    UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> GreenLensMaterial;
    UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> AmberLensMaterial;
    UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> RedLensMaterial;

    ELBStatusBeaconState Status = ELBStatusBeaconState::Off;
    float FlashElapsedSeconds = 0.0f;
    bool bFlashOn = true;
    bool bGeneratedLampHeadsVisible = true;

    void EnsureVisualComponents();
    void EnsureDynamicMaterials();
    void ApplyVisualState();
    void ApplyLamp(UStaticMeshComponent* Lens, UMaterialInstanceDynamic* Material,
        UPointLightComponent* Light, const FLinearColor& Colour, bool bLit);
};
