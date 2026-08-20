#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBOneFactoryScanBeamActor.generated.h"

class UStaticMeshComponent;

/**
 * The inspection laser: a thin emissive bar that sweeps back and forth
 * along the line through an inspection station, the way a car-wash
 * gantry passes over a car. Placed at EOL arches, vision gates and the
 * quality light tunnel; the beam mesh is authored art (ScanKit), the
 * sweep is a triangle wave with a short dwell at each end of travel.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBOneFactoryScanBeamActor : public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryScanBeamActor();
    virtual void Tick(float DeltaSeconds) override;

    UStaticMeshComponent* GetBeamComponent() const { return BeamMesh; }

    /** Half the sweep travel along local X, in centimetres. */
    UPROPERTY(EditAnywhere, Category="Line Boss|Scan")
    float SweepHalfRangeCm = 210.0f;

    /** Seconds for one end-to-end pass (excluding dwell). */
    UPROPERTY(EditAnywhere, Category="Line Boss|Scan")
    float SecondsPerPass = 3.2f;

    /** Dwell at each end of travel before the return pass. */
    UPROPERTY(EditAnywhere, Category="Line Boss|Scan")
    float DwellSeconds = 0.5f;

private:
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Scan")
    TObjectPtr<UStaticMeshComponent> BeamMesh;

    float CycleSeconds = 0.0f;
};
