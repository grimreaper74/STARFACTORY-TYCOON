#include "LBFreeRoamPawn.h"

#include "Components/SphereComponent.h"
#include "GameFramework/SpectatorPawnMovement.h"

ALBFreeRoamPawn::ALBFreeRoamPawn()
{
    SpawnCollisionHandlingMethod = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    if (USphereComponent* Sphere = GetCollisionComponent())
    {
        Sphere->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Sphere->SetGenerateOverlapEvents(false);
    }
    if (USpectatorPawnMovement* SpectatorMovement = Cast<USpectatorPawnMovement>(GetMovementComponent()))
    {
        SpectatorMovement->MaxSpeed = 6000.0f;
        SpectatorMovement->Acceleration = 12000.0f;
        SpectatorMovement->Deceleration = 16000.0f;
    }
}

void ALBFreeRoamPawn::BeginPlay()
{
    Super::BeginPlay();
    FVector SafeStart = GetActorLocation();
    SafeStart.Z = FMath::Max(SafeStart.Z, MinimumInitialHeightCm);
    SetActorLocation(SafeStart, false, nullptr, ETeleportType::TeleportPhysics);
    UE_LOG(LogTemp, Display, TEXT("FreeRoam spectator start=%s collision=NoCollision"), *SafeStart.ToString());
}
