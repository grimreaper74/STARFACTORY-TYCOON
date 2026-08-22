#include "LBOneFactoryScanBeamActor.h"

#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "UObject/ConstructorHelpers.h"

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
    ScanLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("ScanGlow"));
    ScanLight->SetupAttachment(BeamMesh);
    ScanLight->SetLightColor(FLinearColor(0.03f, 0.85f, 1.0f));
    ScanLight->SetIntensity(2400.0f);
    ScanLight->SetAttenuationRadius(420.0f);
    ScanLight->SetCastShadows(false);
    ScanLight->SetVolumetricScatteringIntensity(0.35f);
    // The actor owns its authored beam rather than relying on an editor-only
    // per-instance override.  That keeps the scanner visible after a save,
    // reload and cook, wherever the three inspection actors are placed.
    static ConstructorHelpers::FObjectFinder<UStaticMesh> ScanBeamAsset(
        TEXT("/Game/LineBoss/ScanKit_v001/Meshes/SM_LB_Inspect_ScanBeam_v001.SM_LB_Inspect_ScanBeam_v001"));
    if (ScanBeamAsset.Succeeded())
    {
        BeamMesh->SetStaticMesh(ScanBeamAsset.Object);
    }
    BeamMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    BeamMesh->SetCastShadow(false);
    BeamMesh->SetGenerateOverlapEvents(false);
    BeamMesh->SetCanEverAffectNavigation(false);
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
