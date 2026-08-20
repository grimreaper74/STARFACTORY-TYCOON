#include "LBOneFactoryScanBeamActor.h"

#include "Components/StaticMeshComponent.h"

ALBOneFactoryScanBeamActor::ALBOneFactoryScanBeamActor()
{
    PrimaryActorTick.bCanEverTick = true;
    // The sweep is scenery motion; it can start a frame late and skip
    // ticks under load without anyone noticing.
    PrimaryActorTick.TickInterval = 0.0f;
    RootComponent = CreateDefaultSubobject<USceneComponent>(
        TEXT("ScanRoot"));
    BeamMesh = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("ScanBeam"));
    BeamMesh->SetupAttachment(RootComponent);
    BeamMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    BeamMesh->SetCastShadow(false);
}

void ALBOneFactoryScanBeamActor::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    const float Pass = FMath::Max(0.25f, SecondsPerPass);
    const float Dwell = FMath::Max(0.0f, DwellSeconds);
    const float Cycle = (Pass + Dwell) * 2.0f;
    CycleSeconds = FMath::Fmod(CycleSeconds + DeltaSeconds, Cycle);

    // Forward pass, dwell, return pass, dwell.
    float Alpha;
    if (CycleSeconds < Pass)
    {
        Alpha = CycleSeconds / Pass;
    }
    else if (CycleSeconds < Pass + Dwell)
    {
        Alpha = 1.0f;
    }
    else if (CycleSeconds < Pass * 2.0f + Dwell)
    {
        Alpha = 1.0f - (CycleSeconds - Pass - Dwell) / Pass;
    }
    else
    {
        Alpha = 0.0f;
    }
    // Ease the turnarounds so the carriage reads as driven, not bounced.
    const float Eased = FMath::InterpSinInOut(-1.0f, 1.0f, Alpha);
    if (BeamMesh)
    {
        BeamMesh->SetRelativeLocation(
            FVector(Eased * SweepHalfRangeCm, 0.0f, 0.0f));
    }
}
