#pragma once

#include "CoreMinimal.h"

class UWorld;

/**
 * Runtime-only path planning shared by Line Boss mobile plant equipment.
 *
 * Certified/save-game routes remain the authoritative mission contract. This
 * planner derives a disposable, clearance-aware path from that contract each
 * time a vehicle starts moving, so old saves and authored route revisions stay
 * compatible when the player changes the factory layout.
 */
namespace LBMobileRoutePlanner
{
    struct FSettings
    {
        /** Half size of the moving authority's collision footprint. */
        FVector2D VehicleHalfExtentCm = FVector2D(75.0f, 50.0f);

        /** Air gap retained outside both the vehicle and protected asset envelope. */
        float EnvelopeClearanceCm = 35.0f;

        /** Preferred centre-line radius used to round polyline corners. */
        float CornerRadiusCm = 140.0f;

        /** Maximum heading change between generated curve samples. */
        float MaximumCurveStepDegrees = 15.0f;
    };

    /**
     * Builds a world-space route around player-built machine and storage
     * envelopes. OutPath excludes Start and includes every final destination.
     */
    LINEBOSSCARFACTORY_API bool BuildClearanceAwarePath(
        const UWorld* World,
        const FVector& Start,
        const TArray<FVector>& CertifiedWaypoints,
        const FSettings& Settings,
        TArray<FVector>& OutPath);
}

