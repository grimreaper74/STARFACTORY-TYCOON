#include "LBMobileRoutePlanner.h"

#include "LBFactoryBuildMachine.h"
#include "LBPressShopStorageZone.h"

#include "Engine/World.h"
#include "EngineUtils.h"

namespace
{
    constexpr float CornerNodeOffsetCm = 2.0f;
    constexpr float IntersectionInsetCm = 0.5f;
    constexpr float DuplicatePointToleranceCm = 1.0f;

    struct FRouteObstacle2D
    {
        FVector2D Centre = FVector2D::ZeroVector;
        FVector2D AxisX = FVector2D(1.0f, 0.0f);
        FVector2D AxisY = FVector2D(0.0f, 1.0f);
        FVector2D HalfExtent = FVector2D::ZeroVector;

        FVector2D ToLocal(const FVector2D& Point) const
        {
            const FVector2D Offset = Point - Centre;
            return FVector2D(FVector2D::DotProduct(Offset, AxisX), FVector2D::DotProduct(Offset, AxisY));
        }

        FVector2D ToWorld(const FVector2D& Point) const
        {
            return Centre + AxisX * Point.X + AxisY * Point.Y;
        }
    };

    FVector2D NormalizedPlanarAxis(const FVector& Axis, const FVector2D& Fallback)
    {
        FVector2D Result(Axis.X, Axis.Y);
        return Result.Normalize() ? Result : Fallback;
    }

    FRouteObstacle2D MakeObstacle(const FTransform& Transform, const FVector& RelativeCentre,
        const FVector& UnscaledHalfExtent, const float ExpansionCm)
    {
        FRouteObstacle2D Result;
        const FVector WorldCentre = Transform.TransformPosition(RelativeCentre);
        Result.Centre = FVector2D(WorldCentre.X, WorldCentre.Y);
        Result.AxisX = NormalizedPlanarAxis(Transform.TransformVectorNoScale(FVector::ForwardVector), FVector2D(1.0f, 0.0f));
        Result.AxisY = NormalizedPlanarAxis(Transform.TransformVectorNoScale(FVector::RightVector), FVector2D(0.0f, 1.0f));
        const FVector Scale = Transform.GetScale3D().GetAbs();
        Result.HalfExtent = FVector2D(
            UnscaledHalfExtent.X * Scale.X + ExpansionCm,
            UnscaledHalfExtent.Y * Scale.Y + ExpansionCm);
        return Result;
    }

    void GatherObstacles(const UWorld* World, const float ExpansionCm, TArray<FRouteObstacle2D>& OutObstacles)
    {
        OutObstacles.Reset();
        if (!World)
        {
            return;
        }

        for (TActorIterator<ALBFactoryBuildMachine> It(World); It; ++It)
        {
            const ALBFactoryBuildMachine* Machine = *It;
            if (!IsValid(Machine) || Machine->GetMachineId().IsNone())
            {
                continue;
            }
            OutObstacles.Add(MakeObstacle(
                Machine->GetActorTransform(),
                Machine->GetProtectedEnvelopeRelativeCentre(),
                Machine->GetProtectedEnvelopeHalfExtent(),
                ExpansionCm));
        }

        for (TActorIterator<ALBPressShopStorageZone> It(World); It; ++It)
        {
            const ALBPressShopStorageZone* Storage = *It;
            if (!IsValid(Storage) || Storage->GetZoneId().IsNone())
            {
                continue;
            }
            OutObstacles.Add(MakeObstacle(
                Storage->GetActorTransform(), FVector::ZeroVector,
                Storage->GetZoneHalfExtent(), ExpansionCm));
        }
    }

    bool SegmentIntersectsObstacleInterior(const FVector2D& Start, const FVector2D& End,
        const FRouteObstacle2D& Obstacle)
    {
        const FVector2D LocalStart = Obstacle.ToLocal(Start);
        const FVector2D LocalEnd = Obstacle.ToLocal(End);
        const FVector2D Delta = LocalEnd - LocalStart;
        const FVector2D InnerHalf(
            FMath::Max(0.0f, Obstacle.HalfExtent.X - IntersectionInsetCm),
            FMath::Max(0.0f, Obstacle.HalfExtent.Y - IntersectionInsetCm));

        float MinimumT = 0.0f;
        float MaximumT = 1.0f;
        const auto ClipAxis = [&MinimumT, &MaximumT](const float Origin, const float Direction, const float HalfExtent)
        {
            if (FMath::Abs(Direction) <= UE_KINDA_SMALL_NUMBER)
            {
                return Origin > -HalfExtent && Origin < HalfExtent;
            }
            float Enter = (-HalfExtent - Origin) / Direction;
            float Exit = (HalfExtent - Origin) / Direction;
            if (Enter > Exit)
            {
                Swap(Enter, Exit);
            }
            MinimumT = FMath::Max(MinimumT, Enter);
            MaximumT = FMath::Min(MaximumT, Exit);
            return MinimumT <= MaximumT;
        };

        return ClipAxis(LocalStart.X, Delta.X, InnerHalf.X)
            && ClipAxis(LocalStart.Y, Delta.Y, InnerHalf.Y)
            && MaximumT >= 0.0f && MinimumT <= 1.0f;
    }

    bool IsSegmentClear(const FVector2D& Start, const FVector2D& End,
        const TArray<FRouteObstacle2D>& Obstacles)
    {
        for (const FRouteObstacle2D& Obstacle : Obstacles)
        {
            if (SegmentIntersectsObstacleInterior(Start, End, Obstacle))
            {
                return false;
            }
        }
        return true;
    }

    bool IsPointClear(const FVector2D& Point, const TArray<FRouteObstacle2D>& Obstacles)
    {
        for (const FRouteObstacle2D& Obstacle : Obstacles)
        {
            const FVector2D Local = Obstacle.ToLocal(Point);
            if (FMath::Abs(Local.X) < Obstacle.HalfExtent.X - IntersectionInsetCm
                && FMath::Abs(Local.Y) < Obstacle.HalfExtent.Y - IntersectionInsetCm)
            {
                return false;
            }
        }
        return true;
    }

    void AddUniquePoint(TArray<FVector>& Points, const FVector& Point)
    {
        if (Points.IsEmpty() || FVector::Dist2D(Points.Last(), Point) > DuplicatePointToleranceCm)
        {
            Points.Add(Point);
        }
    }

    bool PlanLeg(const FVector& Start, const FVector& End,
        const TArray<FRouteObstacle2D>& Obstacles, TArray<FVector>& OutPoints)
    {
        OutPoints.Reset();
        const FVector2D Start2D(Start.X, Start.Y);
        const FVector2D End2D(End.X, End.Y);
        if (!IsPointClear(Start2D, Obstacles) || !IsPointClear(End2D, Obstacles))
        {
            return false;
        }
        if (IsSegmentClear(Start2D, End2D, Obstacles))
        {
            OutPoints.Add(End);
            return true;
        }

        TArray<FVector2D> Nodes;
        Nodes.Reserve(2 + Obstacles.Num() * 4);
        Nodes.Add(Start2D);
        Nodes.Add(End2D);
        for (const FRouteObstacle2D& Obstacle : Obstacles)
        {
            const FVector2D CornerHalf = Obstacle.HalfExtent + FVector2D(CornerNodeOffsetCm);
            for (const float XSign : {-1.0f, 1.0f})
            {
                for (const float YSign : {-1.0f, 1.0f})
                {
                    const FVector2D Candidate = Obstacle.ToWorld(FVector2D(XSign * CornerHalf.X, YSign * CornerHalf.Y));
                    if (IsPointClear(Candidate, Obstacles))
                    {
                        Nodes.Add(Candidate);
                    }
                }
            }
        }

        TArray<float> BestDistance;
        TArray<int32> Previous;
        TArray<bool> Visited;
        BestDistance.Init(TNumericLimits<float>::Max(), Nodes.Num());
        Previous.Init(INDEX_NONE, Nodes.Num());
        Visited.Init(false, Nodes.Num());
        BestDistance[0] = 0.0f;

        for (int32 Iteration = 0; Iteration < Nodes.Num(); ++Iteration)
        {
            int32 Current = INDEX_NONE;
            float CurrentDistance = TNumericLimits<float>::Max();
            for (int32 NodeIndex = 0; NodeIndex < Nodes.Num(); ++NodeIndex)
            {
                if (!Visited[NodeIndex] && BestDistance[NodeIndex] < CurrentDistance)
                {
                    CurrentDistance = BestDistance[NodeIndex];
                    Current = NodeIndex;
                }
            }
            if (Current == INDEX_NONE || Current == 1)
            {
                break;
            }

            Visited[Current] = true;
            for (int32 Candidate = 0; Candidate < Nodes.Num(); ++Candidate)
            {
                if (Candidate == Current || Visited[Candidate]
                    || !IsSegmentClear(Nodes[Current], Nodes[Candidate], Obstacles))
                {
                    continue;
                }
                const float CandidateDistance = CurrentDistance + FVector2D::Distance(Nodes[Current], Nodes[Candidate]);
                if (CandidateDistance < BestDistance[Candidate])
                {
                    BestDistance[Candidate] = CandidateDistance;
                    Previous[Candidate] = Current;
                }
            }
        }

        if (Previous[1] == INDEX_NONE)
        {
            return false;
        }

        TArray<int32> ReversePath;
        for (int32 Node = 1; Node != 0 && Node != INDEX_NONE; Node = Previous[Node])
        {
            ReversePath.Add(Node);
        }
        if (ReversePath.IsEmpty() || Previous[ReversePath.Last()] != 0)
        {
            return false;
        }

        for (int32 PathIndex = ReversePath.Num() - 1; PathIndex >= 0; --PathIndex)
        {
            const FVector2D Point = Nodes[ReversePath[PathIndex]];
            OutPoints.Add(FVector(Point.X, Point.Y, End.Z));
        }
        return true;
    }

    void RoundPolyline(const FVector& Start, const TArray<FVector>& Polyline,
        const float CornerRadiusCm, const float MaximumCurveStepDegrees, TArray<FVector>& OutRounded)
    {
        OutRounded.Reset();
        if (Polyline.IsEmpty())
        {
            return;
        }

        TArray<FVector> FullPath;
        FullPath.Reserve(Polyline.Num() + 1);
        FullPath.Add(Start);
        FullPath.Append(Polyline);
        if (FullPath.Num() <= 2 || CornerRadiusCm <= KINDA_SMALL_NUMBER)
        {
            OutRounded = Polyline;
            return;
        }

        for (int32 CornerIndex = 1; CornerIndex < FullPath.Num() - 1; ++CornerIndex)
        {
            const FVector Corner = FullPath[CornerIndex];
            const FVector IncomingVector = Corner - FullPath[CornerIndex - 1];
            const FVector OutgoingVector = FullPath[CornerIndex + 1] - Corner;
            const float IncomingLength = IncomingVector.Size2D();
            const float OutgoingLength = OutgoingVector.Size2D();
            const FVector IncomingDirection = IncomingVector.GetSafeNormal2D();
            const FVector OutgoingDirection = OutgoingVector.GetSafeNormal2D();
            const float DirectionDot = FVector::DotProduct(IncomingDirection, OutgoingDirection);
            if (IncomingLength <= 2.0f || OutgoingLength <= 2.0f || DirectionDot > 0.999f || DirectionDot < -0.98f)
            {
                AddUniquePoint(OutRounded, Corner);
                continue;
            }

            const float TangentDistance = FMath::Min3(CornerRadiusCm, IncomingLength * 0.34f, OutgoingLength * 0.34f);
            const FVector TangentStart = Corner - IncomingDirection * TangentDistance;
            const FVector TangentEnd = Corner + OutgoingDirection * TangentDistance;
            AddUniquePoint(OutRounded, TangentStart);

            const float TurnDegrees = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(DirectionDot, -1.0f, 1.0f)));
            const int32 SampleCount = FMath::Clamp(
                FMath::CeilToInt(TurnDegrees / FMath::Max(5.0f, MaximumCurveStepDegrees)), 2, 12);
            for (int32 SampleIndex = 1; SampleIndex <= SampleCount; ++SampleIndex)
            {
                const float Alpha = static_cast<float>(SampleIndex) / static_cast<float>(SampleCount);
                const float OneMinusAlpha = 1.0f - Alpha;
                const FVector CurvePoint = OneMinusAlpha * OneMinusAlpha * TangentStart
                    + 2.0f * OneMinusAlpha * Alpha * Corner
                    + Alpha * Alpha * TangentEnd;
                AddUniquePoint(OutRounded, CurvePoint);
            }
        }
        AddUniquePoint(OutRounded, FullPath.Last());
    }

    bool PathIsClear(const FVector& Start, const TArray<FVector>& Path,
        const TArray<FRouteObstacle2D>& Obstacles)
    {
        FVector Previous = Start;
        for (const FVector& Point : Path)
        {
            if (!IsSegmentClear(FVector2D(Previous.X, Previous.Y), FVector2D(Point.X, Point.Y), Obstacles))
            {
                return false;
            }
            Previous = Point;
        }
        return true;
    }
}

bool LBMobileRoutePlanner::BuildClearanceAwarePath(
    const UWorld* World,
    const FVector& Start,
    const TArray<FVector>& CertifiedWaypoints,
    const FSettings& Settings,
    TArray<FVector>& OutPath)
{
    OutPath.Reset();
    if (CertifiedWaypoints.IsEmpty() || Settings.VehicleHalfExtentCm.X <= 0.0f
        || Settings.VehicleHalfExtentCm.Y <= 0.0f || Settings.EnvelopeClearanceCm < 0.0f
        || Settings.CornerRadiusCm < 0.0f)
    {
        return false;
    }

    const float VehicleRadiusCm = Settings.VehicleHalfExtentCm.Size();
    const float RequiredExpansionCm = VehicleRadiusCm + Settings.EnvelopeClearanceCm;
    // A quadratic corner can bow toward a visibility-graph corner. Plan against
    // a wider disposable envelope, then validate the curve against the required
    // vehicle clearance before accepting it.
    const float PlanningExpansionCm = RequiredExpansionCm + Settings.CornerRadiusCm * 0.5f;
    TArray<FRouteObstacle2D> PlanningObstacles;
    TArray<FRouteObstacle2D> RequiredClearanceObstacles;
    GatherObstacles(World, PlanningExpansionCm, PlanningObstacles);
    GatherObstacles(World, RequiredExpansionCm, RequiredClearanceObstacles);

    TArray<FVector> Polyline;
    FVector LegStart = Start;
    for (const FVector& Destination : CertifiedWaypoints)
    {
        TArray<FVector> Leg;
        if (!PlanLeg(LegStart, Destination, PlanningObstacles, Leg))
        {
            OutPath.Reset();
            return false;
        }
        for (const FVector& Point : Leg)
        {
            AddUniquePoint(Polyline, Point);
        }
        LegStart = Destination;
    }

    for (const float RadiusScale : {1.0f, 0.65f, 0.35f})
    {
        TArray<FVector> Rounded;
        RoundPolyline(Start, Polyline, Settings.CornerRadiusCm * RadiusScale,
            Settings.MaximumCurveStepDegrees, Rounded);
        if (PathIsClear(Start, Rounded, RequiredClearanceObstacles))
        {
            OutPath = MoveTemp(Rounded);
            return !OutPath.IsEmpty();
        }
    }

    if (!PathIsClear(Start, Polyline, RequiredClearanceObstacles))
    {
        return false;
    }
    OutPath = MoveTemp(Polyline);
    return !OutPath.IsEmpty();
}

