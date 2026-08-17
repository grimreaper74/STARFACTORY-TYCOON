#include "LBOneFactoryBodyWeldStarterLayout.h"

namespace LBOneFactoryBodyWeldStarterPrivate
{
    constexpr float TransformTolerance = 0.001f;
    constexpr float LayoutToleranceCm = 0.1f;
    constexpr float MaximumRouteLengthCm = 6200.0f;

    struct FStationContract
    {
        int32 LinePosition;
        ELBOneFactoryBodyWeldProgramme InitialProgramme;
        TArray<ELBOneFactoryBodyWeldCapability> Capabilities;
        TArray<ELBOneFactoryBodyWeldRobotRole> SupportedRobotRoles;
        ELBOneFactoryBodyWeldRobotRole LeftRobotRole;
        ELBOneFactoryBodyWeldRobotRole RightRobotRole;
        float NominalCycleSeconds;
    };

    const TArray<FStationContract>& Contracts()
    {
        using C = ELBOneFactoryBodyWeldCapability;
        using P = ELBOneFactoryBodyWeldProgramme;
        using R = ELBOneFactoryBodyWeldRobotRole;
        static const TArray<FStationContract> Result =
        {
            {1, P::PressedPanelReceive,
                {C::PanelLogistics, C::MaterialHandling},
                {R::PanelHandling, R::TransferHandling},
                R::PanelHandling, R::PanelHandling, 32.0f},
            {2, P::FrontUnderbodyGeometry,
                {C::UnderbodyGeometry, C::SpotJoining},
                {R::GeometryClamp, R::SpotWelding},
                R::GeometryClamp, R::SpotWelding, 52.0f},
            {3, P::RearUnderbodyGeometry,
                {C::UnderbodyGeometry, C::SpotJoining},
                {R::GeometryClamp, R::SpotWelding},
                R::SpotWelding, R::GeometryClamp, 52.0f},
            {4, P::UnderbodyFramingAndRespot,
                {C::UnderbodyGeometry, C::SpotJoining},
                {R::GeometryClamp, R::SpotWelding},
                R::SpotWelding, R::SpotWelding, 56.0f},
            {5, P::LeftBodysideLoad,
                {C::PanelLogistics, C::FramingGeometry},
                {R::PanelHandling, R::GeometryClamp},
                R::PanelHandling, R::PanelHandling, 48.0f},
            {6, P::RightBodysideLoad,
                {C::PanelLogistics, C::FramingGeometry},
                {R::PanelHandling, R::GeometryClamp},
                R::PanelHandling, R::PanelHandling, 48.0f},
            {7, P::BodyFramingAndMarriage,
                {C::FramingGeometry, C::SpotJoining},
                {R::GeometryClamp, R::SpotWelding},
                R::GeometryClamp, R::SpotWelding, 60.0f},
            {8, P::RoofAndCrossmemberFit,
                {C::RoofInstall, C::SpotJoining},
                {R::RoofHandling, R::SpotWelding},
                R::RoofHandling, R::SpotWelding, 54.0f},
            {9, P::MainBodySpotWeld,
                {C::SpotJoining, C::FramingGeometry},
                {R::SpotWelding, R::GeometryClamp},
                R::SpotWelding, R::SpotWelding, 62.0f},
            {10, P::AdhesiveAndBrazedSeams,
                {C::AdhesiveJoining, C::SpotJoining},
                {R::AdhesiveSealing, R::SpotWelding},
                R::AdhesiveSealing, R::SpotWelding, 56.0f},
            {11, P::ClosurePreparation,
                {C::ClosureFit, C::PanelLogistics},
                {R::ClosureHandling, R::PanelHandling},
                R::ClosureHandling, R::ClosureHandling, 46.0f},
            {12, P::ClosureFitAndHingeSet,
                {C::ClosureFit, C::SpotJoining},
                {R::ClosureHandling, R::SpotWelding},
                R::ClosureHandling, R::SpotWelding, 58.0f},
            {13, P::DimensionalGeometryScan,
                {C::Metrology, C::Quality},
                {R::VisionInspection, R::GeometryClamp},
                R::VisionInspection, R::VisionInspection, 42.0f},
            {14, P::RespotAndFinishWeld,
                {C::SpotJoining, C::Rework},
                {R::SpotWelding, R::ReworkWelding},
                R::SpotWelding, R::SpotWelding, 60.0f},
            {15, P::StudMountAndBracketWeld,
                {C::StudMount, C::SpotJoining},
                {R::StudWelding, R::SpotWelding},
                R::StudWelding, R::SpotWelding, 52.0f},
            {16, P::WeldQualityInspection,
                {C::Quality, C::Rework},
                {R::VisionInspection, R::ReworkWelding},
                R::VisionInspection, R::ReworkWelding, 46.0f},
            {17, P::BIWReworkAndBuffer,
                {C::Rework, C::Handoff},
                {R::ReworkWelding, R::TransferHandling},
                R::ReworkWelding, R::TransferHandling, 58.0f},
            {18, P::BIWHandoff,
                {C::Handoff, C::MaterialHandling},
                {R::TransferHandling, R::PanelHandling},
                R::TransferHandling, R::TransferHandling, 28.0f}
        };
        return Result;
    }

    const FStationContract* FindContract(const int32 LinePosition)
    {
        return Contracts().FindByPredicate([LinePosition](
            const FStationContract& Contract)
        {
            return Contract.LinePosition == LinePosition;
        });
    }

    FBox BodyBayBounds()
    {
        const FLBOneFactoryLayoutDefinition Layout =
            ULBOneFactoryLayoutLibrary::MakeMoorcrossWorksShellLayout();
        const FLBOneFactoryDepartmentBay* Bay =
            Layout.DepartmentBays.FindByPredicate([](
                const FLBOneFactoryDepartmentBay& Candidate)
            {
                return Candidate.BayId == LBOneFactoryIds::BodyBay()
                    && Candidate.Department ==
                        ELBOneFactoryDepartment::Body;
            });
        return Bay ? Bay->GetWorldBounds() : FBox(ForceInit);
    }

    FBox StationBounds(const FLBOneFactoryBodyWeldStationState& Station)
    {
        const FVector Half(Station.FootprintSizeCm.X * 0.5f,
            Station.FootprintSizeCm.Y * 0.5f, 0.0f);
        return FBox(FVector(-Half.X, -Half.Y, 0.0f),
            FVector(Half.X, Half.Y, Station.FootprintSizeCm.Z))
            .TransformBy(Station.WorldTransform);
    }

    bool IsTransformUsable(const FTransform& Transform)
    {
        const FRotator Rotation = Transform.Rotator();
        return Transform.IsValid() && !Transform.ContainsNaN()
            && Transform.GetScale3D().Equals(FVector::OneVector,
                TransformTolerance)
            && FMath::IsNearlyZero(Transform.GetLocation().Z,
                LayoutToleranceCm)
            && FMath::IsNearlyZero(Rotation.Roll, TransformTolerance)
            && FMath::IsNearlyZero(Rotation.Pitch, TransformTolerance);
    }

    bool IsFinitePositiveVector(const FVector& Value)
    {
        return FMath::IsFinite(Value.X) && FMath::IsFinite(Value.Y)
            && FMath::IsFinite(Value.Z) && Value.X > 0.0f
            && Value.Y > 0.0f && Value.Z > 0.0f;
    }

    FLBOneFactoryBodyWeldStationState* FindStation(
        FLBOneFactoryBodyWeldLayoutState& State, const FName StationId)
    {
        return State.Stations.FindByPredicate([StationId](
            const FLBOneFactoryBodyWeldStationState& Station)
        {
            return Station.StationId == StationId;
        });
    }

    const FLBOneFactoryBodyWeldStationState* FindStation(
        const FLBOneFactoryBodyWeldLayoutState& State,
        const FName StationId)
    {
        return State.Stations.FindByPredicate([StationId](
            const FLBOneFactoryBodyWeldStationState& Station)
        {
            return Station.StationId == StationId;
        });
    }

    bool HasUniqueCapabilities(
        const TArray<ELBOneFactoryBodyWeldCapability>& Capabilities)
    {
        TSet<ELBOneFactoryBodyWeldCapability> Seen;
        for (const ELBOneFactoryBodyWeldCapability Capability : Capabilities)
        {
            if (static_cast<uint8>(Capability)
                    > static_cast<uint8>(
                        ELBOneFactoryBodyWeldCapability::Handoff)
                || Seen.Contains(Capability))
            {
                return false;
            }
            Seen.Add(Capability);
        }
        return !Capabilities.IsEmpty();
    }

    bool HasUniqueRobotRoles(
        const TArray<ELBOneFactoryBodyWeldRobotRole>& RobotRoles)
    {
        TSet<ELBOneFactoryBodyWeldRobotRole> Seen;
        for (const ELBOneFactoryBodyWeldRobotRole RobotRole : RobotRoles)
        {
            if (RobotRole == ELBOneFactoryBodyWeldRobotRole::None
                || static_cast<uint8>(RobotRole)
                    > static_cast<uint8>(
                        ELBOneFactoryBodyWeldRobotRole::ReworkWelding)
                || Seen.Contains(RobotRole))
            {
                return false;
            }
            Seen.Add(RobotRole);
        }
        return !RobotRoles.IsEmpty();
    }

    bool AssignedProgrammesHaveRequiredRobotRoles(
        const FLBOneFactoryBodyWeldStationState& Station)
    {
        for (const ELBOneFactoryBodyWeldProgramme Programme :
            Station.AssignedProgrammes)
        {
            const ELBOneFactoryBodyWeldRobotRole Required =
                ULBOneFactoryBodyWeldStarterLayoutLibrary::
                    GetRequiredRobotRole(Programme);
            if (Station.LeftRobotRole != Required
                && Station.RightRobotRole != Required)
            {
                return false;
            }
        }
        return true;
    }

    /**
     * The 18 positions on a serpentine that opens EAST.
     *
     * The previous grid ran at 2000 cm pitch with rows at Y -11300 and -5700, and
     * run B travelling east-to-west - which put panel receipt (position 1) in the
     * south-west corner and the BIW handoff (position 18) at the north-WEST wall,
     * about 170 m of backhaul from paint, whose west wall is at X -1000. It also
     * spent 88 of the bay's 100 m of depth on two rows plus an aisle, leaving 6 m at
     * each wall: no receiving lane, no service corridor and no subassembly space.
     * That, not the station count, is why the shop read sparse.
     *
     * Both heads now sit at the east end, nearest the press exit and the paint
     * entry, as a real two-bay body shop is fed.
     *
     * The pitch stays at 2000, NOT the 1800 the layout study proposed. 1800 clears
     * the 1700 footprint on paper, but the player can nudge a station a metre east
     * (ExecuteUMGAction 4), which consumes all 100 cm of that slack and makes
     * neighbours touch - the validator then refuses the move and
     * BodyWeldLifecycleRobotProgrammeRollbackMoveWIPAndRemoval fails. 2000 leaves
     * 300 cm, so a one-metre nudge in either direction still clears. The depth
     * saving that mattered comes from the row change, not the pitch.
     *
     * Arithmetic: 9 positions at 2000 span 16000, plus the 1700 footprint gives
     * 17700 inside the bay's 18000, so the run starts at -3050 to keep the west end
     * at -19900 rather than 50 cm outside BodyBayBounds(). Row separation 4200
     * exceeds the 3200 footprint in Y; the 9-to-10 link is 4200 cm and every other
     * 2000 cm, all under the frozen MaximumRouteLengthCm of 6200.
     */
    FVector CanonicalLocation(const int32 LinePosition)
    {
        if (LinePosition <= 9)
        {
            return FVector(-3050.0f - (LinePosition - 1) * 2000.0f,
                -7000.0f, 0.0f);
        }
        return FVector(-19050.0f + (LinePosition - 10) * 2000.0f,
            -11200.0f, 0.0f);
    }

    FRotator CanonicalRotation(const int32 LinePosition)
    {
        // Run A travels east to west, run B west to east: each station faces the
        // direction the body is moving, which is inverted from the old grid.
        return FRotator(0.0f, LinePosition <= 9 ? 180.0f : 0.0f, 0.0f);
    }
}

FName LBOneFactoryBodyWeldStarterIds::Layout()
{
    static const FName Id(TEXT("MOORCROSS_BODY_WELD_STARTER_NATIVE_V001"));
    return Id;
}

FName LBOneFactoryBodyWeldStarterIds::VehicleModel()
{
    static const FName Id(TEXT("CAIRNWELL_2040"));
    return Id;
}

FName LBOneFactoryBodyWeldStarterIds::Station(const int32 LinePosition)
{
    return LinePosition >= 1
            && LinePosition <=
                ULBOneFactoryBodyWeldStarterLayoutLibrary::RequiredStationCount
        ? FName(*FString::Printf(TEXT("OF_BODY_WELD_POS_%02d"),
            LinePosition))
        : NAME_None;
}

FName LBOneFactoryBodyWeldStarterIds::Connection(
    const int32 SourceLinePosition)
{
    return SourceLinePosition >= 1
            && SourceLinePosition <=
                ULBOneFactoryBodyWeldStarterLayoutLibrary::
                    RequiredConnectionCount
        ? FName(*FString::Printf(TEXT("OF_BODY_WELD_ROUTE_%02d_%02d"),
            SourceLinePosition, SourceLinePosition + 1))
        : NAME_None;
}

ELBOneFactoryBodyWeldCapability
ULBOneFactoryBodyWeldStarterLayoutLibrary::GetRequiredCapability(
    const ELBOneFactoryBodyWeldProgramme InProgramme)
{
    using C = ELBOneFactoryBodyWeldCapability;
    using P = ELBOneFactoryBodyWeldProgramme;
    switch (InProgramme)
    {
    case P::PressedPanelReceive: return C::PanelLogistics;
    case P::FrontUnderbodyGeometry: return C::UnderbodyGeometry;
    case P::RearUnderbodyGeometry: return C::UnderbodyGeometry;
    case P::UnderbodyFramingAndRespot: return C::SpotJoining;
    case P::LeftBodysideLoad: return C::PanelLogistics;
    case P::RightBodysideLoad: return C::PanelLogistics;
    case P::BodyFramingAndMarriage: return C::FramingGeometry;
    case P::RoofAndCrossmemberFit: return C::RoofInstall;
    case P::MainBodySpotWeld: return C::SpotJoining;
    case P::AdhesiveAndBrazedSeams: return C::AdhesiveJoining;
    case P::ClosurePreparation: return C::ClosureFit;
    case P::ClosureFitAndHingeSet: return C::ClosureFit;
    case P::DimensionalGeometryScan: return C::Metrology;
    case P::RespotAndFinishWeld: return C::SpotJoining;
    case P::StudMountAndBracketWeld: return C::StudMount;
    case P::WeldQualityInspection: return C::Quality;
    case P::BIWReworkAndBuffer: return C::Rework;
    case P::BIWHandoff: return C::Handoff;
    default: return C::PanelLogistics;
    }
}

ELBOneFactoryBodyWeldRobotRole
ULBOneFactoryBodyWeldStarterLayoutLibrary::GetRequiredRobotRole(
    const ELBOneFactoryBodyWeldProgramme InProgramme)
{
    using P = ELBOneFactoryBodyWeldProgramme;
    using R = ELBOneFactoryBodyWeldRobotRole;
    switch (InProgramme)
    {
    case P::PressedPanelReceive: return R::PanelHandling;
    case P::FrontUnderbodyGeometry: return R::GeometryClamp;
    case P::RearUnderbodyGeometry: return R::GeometryClamp;
    case P::UnderbodyFramingAndRespot: return R::SpotWelding;
    case P::LeftBodysideLoad: return R::PanelHandling;
    case P::RightBodysideLoad: return R::PanelHandling;
    case P::BodyFramingAndMarriage: return R::GeometryClamp;
    case P::RoofAndCrossmemberFit: return R::RoofHandling;
    case P::MainBodySpotWeld: return R::SpotWelding;
    case P::AdhesiveAndBrazedSeams: return R::AdhesiveSealing;
    case P::ClosurePreparation: return R::ClosureHandling;
    case P::ClosureFitAndHingeSet: return R::ClosureHandling;
    case P::DimensionalGeometryScan: return R::VisionInspection;
    case P::RespotAndFinishWeld: return R::SpotWelding;
    case P::StudMountAndBracketWeld: return R::StudWelding;
    case P::WeldQualityInspection: return R::VisionInspection;
    case P::BIWReworkAndBuffer: return R::ReworkWelding;
    case P::BIWHandoff: return R::TransferHandling;
    default: return R::None;
    }
}

FString ULBOneFactoryBodyWeldStarterLayoutLibrary::GetProgrammeDisplayName(
    const ELBOneFactoryBodyWeldProgramme InProgramme)
{
    using P = ELBOneFactoryBodyWeldProgramme;
    switch (InProgramme)
    {
    case P::PressedPanelReceive: return TEXT("Pressed-panel receive and sort");
    case P::FrontUnderbodyGeometry: return TEXT("Front underbody geometry");
    case P::RearUnderbodyGeometry: return TEXT("Rear underbody geometry");
    case P::UnderbodyFramingAndRespot: return TEXT("Underbody framing and respot");
    case P::LeftBodysideLoad: return TEXT("Left bodyside load");
    case P::RightBodysideLoad: return TEXT("Right bodyside load");
    case P::BodyFramingAndMarriage: return TEXT("Body framing and marriage");
    case P::RoofAndCrossmemberFit: return TEXT("Roof and crossmember fit");
    case P::MainBodySpotWeld: return TEXT("Main-body spot weld");
    case P::AdhesiveAndBrazedSeams: return TEXT("Adhesive and brazed seams");
    case P::ClosurePreparation: return TEXT("Closure preparation");
    case P::ClosureFitAndHingeSet: return TEXT("Closure fit and hinge set");
    case P::DimensionalGeometryScan: return TEXT("Dimensional geometry scan");
    case P::RespotAndFinishWeld: return TEXT("Respot and finish weld");
    case P::StudMountAndBracketWeld: return TEXT("Stud, mount and bracket weld");
    case P::WeldQualityInspection: return TEXT("Weld quality inspection");
    case P::BIWReworkAndBuffer: return TEXT("BIW rework and buffer");
    case P::BIWHandoff: return TEXT("Body-in-white handoff");
    default: return TEXT("Unknown Body/Weld programme");
    }
}

FString ULBOneFactoryBodyWeldStarterLayoutLibrary::GetRobotRoleDisplayName(
    const ELBOneFactoryBodyWeldRobotRole InRobotRole)
{
    using R = ELBOneFactoryBodyWeldRobotRole;
    switch (InRobotRole)
    {
    case R::PanelHandling: return TEXT("Panel handling");
    case R::TransferHandling: return TEXT("Transfer handling");
    case R::GeometryClamp: return TEXT("Geometry clamp tending");
    case R::SpotWelding: return TEXT("Spot welding");
    case R::AdhesiveSealing: return TEXT("Adhesive sealing");
    case R::RoofHandling: return TEXT("Roof handling");
    case R::ClosureHandling: return TEXT("Closure handling");
    case R::StudWelding: return TEXT("Stud welding");
    case R::VisionInspection: return TEXT("Vision inspection");
    case R::ReworkWelding: return TEXT("Rework welding");
    default: return TEXT("No robot duty");
    }
}

bool ULBOneFactoryBodyWeldStarterLayoutLibrary::StationSupportsProgramme(
    const FLBOneFactoryBodyWeldStationState& Station,
    const ELBOneFactoryBodyWeldProgramme InProgramme)
{
    return Station.Capabilities.Contains(GetRequiredCapability(InProgramme));
}

bool ULBOneFactoryBodyWeldStarterLayoutLibrary::StationSupportsRobotRole(
    const FLBOneFactoryBodyWeldStationState& Station,
    const ELBOneFactoryBodyWeldRobotRole InRobotRole)
{
    return InRobotRole != ELBOneFactoryBodyWeldRobotRole::None
        && Station.SupportedRobotRoles.Contains(InRobotRole);
}

FLBOneFactoryBodyWeldLayoutState
ULBOneFactoryBodyWeldStarterLayoutLibrary::MakeCanonicalStarterLayout()
{
    FLBOneFactoryBodyWeldLayoutState State;
    State.LayoutId = LBOneFactoryBodyWeldStarterIds::Layout();
    State.VehicleModelId = LBOneFactoryBodyWeldStarterIds::VehicleModel();
    State.InputState = ELBOneFactoryBodyWeldMaterialState::PressedPanelSet;
    State.OutputState = ELBOneFactoryBodyWeldMaterialState::BodyInWhite;
    for (const LBOneFactoryBodyWeldStarterPrivate::FStationContract& Contract :
        LBOneFactoryBodyWeldStarterPrivate::Contracts())
    {
        FLBOneFactoryBodyWeldStationState& Station =
            State.Stations.AddDefaulted_GetRef();
        Station.StationId =
            LBOneFactoryBodyWeldStarterIds::Station(Contract.LinePosition);
        Station.LinePosition = Contract.LinePosition;
        Station.WorldTransform = FTransform(
            LBOneFactoryBodyWeldStarterPrivate::CanonicalRotation(
                Contract.LinePosition),
            LBOneFactoryBodyWeldStarterPrivate::CanonicalLocation(
                Contract.LinePosition), FVector::OneVector);
        Station.FootprintSizeCm = FVector(1700.0f, 3200.0f, 650.0f);
        Station.Capabilities = Contract.Capabilities;
        Station.AssignedProgrammes = {Contract.InitialProgramme};
        Station.SupportedRobotRoles = Contract.SupportedRobotRoles;
        Station.LeftRobotRole = Contract.LeftRobotRole;
        Station.RightRobotRole = Contract.RightRobotRole;
        Station.bMirroredLargeSixAxisPair = true;
        Station.NominalCycleSeconds = Contract.NominalCycleSeconds;
    }
    for (int32 Position = 1; Position <= RequiredConnectionCount; ++Position)
    {
        FLBOneFactoryBodyWeldConnectionState& Connection =
            State.Connections.AddDefaulted_GetRef();
        Connection.ConnectionId =
            LBOneFactoryBodyWeldStarterIds::Connection(Position);
        Connection.SourceStationId =
            LBOneFactoryBodyWeldStarterIds::Station(Position);
        Connection.TargetStationId =
            LBOneFactoryBodyWeldStarterIds::Station(Position + 1);
        Connection.MaximumRouteLengthCm =
            LBOneFactoryBodyWeldStarterPrivate::MaximumRouteLengthCm;
    }
    return State;
}

bool ULBOneFactoryBodyWeldStarterLayoutLibrary::ValidateStarterLayout(
    const FLBOneFactoryBodyWeldLayoutState& State, FString& OutReason)
{
    if (State.Version != 1
        || State.LayoutId != LBOneFactoryBodyWeldStarterIds::Layout()
        || State.VehicleModelId !=
            LBOneFactoryBodyWeldStarterIds::VehicleModel()
        || State.Revision < 0
        || State.InputState !=
            ELBOneFactoryBodyWeldMaterialState::PressedPanelSet
        || State.OutputState !=
            ELBOneFactoryBodyWeldMaterialState::BodyInWhite
        || State.Stations.Num() != RequiredStationCount
        || State.Connections.Num() != RequiredConnectionCount)
    {
        OutReason = TEXT(
            "BODY/WELD LAYOUT IDENTITY, VERSION OR CARDINALITY IS INVALID");
        return false;
    }

    const FBox Bay = LBOneFactoryBodyWeldStarterPrivate::BodyBayBounds();
    if (!Bay.IsValid)
    {
        OutReason = TEXT("BODY/WELD BAY CONTRACT IS UNAVAILABLE");
        return false;
    }

    TSet<FName> StationIds;
    TSet<int32> Positions;
    TSet<FName> UnitIds;
    TMap<ELBOneFactoryBodyWeldProgramme, int32> ProgrammePositions;
    TArray<FBox> Envelopes;
    for (const FLBOneFactoryBodyWeldStationState& Station : State.Stations)
    {
        const LBOneFactoryBodyWeldStarterPrivate::FStationContract* Contract =
            LBOneFactoryBodyWeldStarterPrivate::FindContract(
                Station.LinePosition);
        if (Station.Version != 1 || !Contract
            || Station.StationId !=
                LBOneFactoryBodyWeldStarterIds::Station(Station.LinePosition)
            || StationIds.Contains(Station.StationId)
            || Positions.Contains(Station.LinePosition)
            || !LBOneFactoryBodyWeldStarterPrivate::IsTransformUsable(
                Station.WorldTransform)
            || !LBOneFactoryBodyWeldStarterPrivate::IsFinitePositiveVector(
                Station.FootprintSizeCm)
            || !FMath::IsFinite(Station.NominalCycleSeconds)
            || Station.NominalCycleSeconds <= 0.0f
            || Station.Capabilities != Contract->Capabilities
            || Station.SupportedRobotRoles != Contract->SupportedRobotRoles
            || !LBOneFactoryBodyWeldStarterPrivate::HasUniqueCapabilities(
                Station.Capabilities)
            || !LBOneFactoryBodyWeldStarterPrivate::HasUniqueRobotRoles(
                Station.SupportedRobotRoles)
            || !Station.bMirroredLargeSixAxisPair
            || !StationSupportsRobotRole(Station, Station.LeftRobotRole)
            || !StationSupportsRobotRole(Station, Station.RightRobotRole))
        {
            OutReason = FString::Printf(
                TEXT("BODY/WELD STATION CONTRACT FAILED AT POSITION %d"),
                Station.LinePosition);
            return false;
        }
        StationIds.Add(Station.StationId);
        Positions.Add(Station.LinePosition);

        const FBox Envelope =
            LBOneFactoryBodyWeldStarterPrivate::StationBounds(Station);
        if (!Bay.IsInsideOrOn(Envelope.Min) || !Bay.IsInsideOrOn(Envelope.Max))
        {
            OutReason = FString::Printf(
                TEXT("BODY/WELD STATION %s LEFT ITS BAY"),
                *Station.StationId.ToString());
            return false;
        }
        for (const FBox& Existing : Envelopes)
        {
            if (Envelope.Intersect(Existing))
            {
                OutReason = FString::Printf(
                    TEXT("BODY/WELD STATION %s OVERLAPS ANOTHER POSITION"),
                    *Station.StationId.ToString());
                return false;
            }
        }
        Envelopes.Add(Envelope);

        for (const FName UnitId : Station.ActiveOrReservedUnitIds)
        {
            if (UnitId.IsNone() || UnitIds.Contains(UnitId))
            {
                OutReason = TEXT(
                    "BODY/WELD ACTIVE OR RESERVED UNIT IDS ARE INVALID OR DUPLICATED");
                return false;
            }
            UnitIds.Add(UnitId);
        }

        TSet<ELBOneFactoryBodyWeldProgramme> LocalProgrammes;
        for (const ELBOneFactoryBodyWeldProgramme Programme :
            Station.AssignedProgrammes)
        {
            if (static_cast<uint8>(Programme)
                    >= static_cast<uint8>(RequiredProgrammeCount)
                || LocalProgrammes.Contains(Programme)
                || ProgrammePositions.Contains(Programme)
                || !StationSupportsProgramme(Station, Programme))
            {
                OutReason = FString::Printf(
                    TEXT("BODY/WELD PROGRAMME ASSIGNMENT IS INVALID AT %s"),
                    *Station.StationId.ToString());
                return false;
            }
            LocalProgrammes.Add(Programme);
            ProgrammePositions.Add(Programme, Station.LinePosition);
        }
        if (!LBOneFactoryBodyWeldStarterPrivate::
            AssignedProgrammesHaveRequiredRobotRoles(Station))
        {
            OutReason = FString::Printf(
                TEXT("BODY/WELD ROBOT PAIR CANNOT EXECUTE THE PROGRAMME AT %s"),
                *Station.StationId.ToString());
            return false;
        }
    }

    if (ProgrammePositions.Num() != RequiredProgrammeCount)
    {
        OutReason = TEXT(
            "BODY/WELD BILL OF PROCESS MUST CONTAIN ALL 18 PROGRAMMES EXACTLY ONCE");
        return false;
    }
    int32 PreviousPosition = 0;
    for (int32 Index = 0; Index < RequiredProgrammeCount; ++Index)
    {
        const ELBOneFactoryBodyWeldProgramme Programme =
            static_cast<ELBOneFactoryBodyWeldProgramme>(Index);
        const int32* Position = ProgrammePositions.Find(Programme);
        if (!Position || *Position < PreviousPosition)
        {
            OutReason = TEXT(
                "BODY/WELD PROGRAMME ORDER WOULD BYPASS A REQUIRED PROCESS");
            return false;
        }
        PreviousPosition = *Position;
    }

    TSet<FName> ConnectionIds;
    for (int32 Index = 0; Index < State.Connections.Num(); ++Index)
    {
        const int32 SourcePosition = Index + 1;
        const FLBOneFactoryBodyWeldConnectionState& Connection =
            State.Connections[Index];
        const FLBOneFactoryBodyWeldStationState* Source =
            LBOneFactoryBodyWeldStarterPrivate::FindStation(
                State, Connection.SourceStationId);
        const FLBOneFactoryBodyWeldStationState* Target =
            LBOneFactoryBodyWeldStarterPrivate::FindStation(
                State, Connection.TargetStationId);
        if (Connection.Version != 1
            || Connection.ConnectionId !=
                LBOneFactoryBodyWeldStarterIds::Connection(SourcePosition)
            || Connection.SourceStationId !=
                LBOneFactoryBodyWeldStarterIds::Station(SourcePosition)
            || Connection.TargetStationId !=
                LBOneFactoryBodyWeldStarterIds::Station(SourcePosition + 1)
            || ConnectionIds.Contains(Connection.ConnectionId)
            || !Source || !Target
            || !FMath::IsNearlyEqual(Connection.MaximumRouteLengthCm,
                LBOneFactoryBodyWeldStarterPrivate::MaximumRouteLengthCm,
                LBOneFactoryBodyWeldStarterPrivate::LayoutToleranceCm)
            || FVector::Dist2D(Source->WorldTransform.GetLocation(),
                Target->WorldTransform.GetLocation())
                > Connection.MaximumRouteLengthCm
                    + LBOneFactoryBodyWeldStarterPrivate::LayoutToleranceCm)
        {
            OutReason = FString::Printf(
                TEXT("BODY/WELD ROUTE CONTRACT FAILED AT LINK %d"),
                SourcePosition);
            return false;
        }
        ConnectionIds.Add(Connection.ConnectionId);
    }

    OutReason = State.bCommissioned
        ? TEXT("CONFIGURABLE 18-POSITION BODY/WELD LINE IS COMMISSIONED")
        : TEXT(
            "CONFIGURABLE 18-POSITION BODY/WELD LINE IS VALID AND UNCOMMISSIONED");
    return true;
}

ALBOneFactoryBodyWeldStarterLayoutAuthority::
    ALBOneFactoryBodyWeldStarterLayoutAuthority()
{
    PrimaryActorTick.bCanEverTick = false;
    SetReplicates(false);
    Tags.AddUnique(GetAuthorityTag());
    Tags.AddUnique(GetNativeOnlyTag());
    CurrentState =
        ULBOneFactoryBodyWeldStarterLayoutLibrary::MakeCanonicalStarterLayout();
}

FName ALBOneFactoryBodyWeldStarterLayoutAuthority::GetAuthorityTag()
{
    static const FName Tag(TEXT("LB.OneFactory.BodyWeldStarter.Authority"));
    return Tag;
}

FName ALBOneFactoryBodyWeldStarterLayoutAuthority::GetNativeOnlyTag()
{
    static const FName Tag(TEXT("LB.OneFactory.Provenance.NativeOnly"));
    return Tag;
}

bool ALBOneFactoryBodyWeldStarterLayoutAuthority::HasActiveOrReservedWIP(
    const FLBOneFactoryBodyWeldLayoutState& State)
{
    return State.Stations.ContainsByPredicate([](
        const FLBOneFactoryBodyWeldStationState& Station)
    {
        return !Station.ActiveOrReservedUnitIds.IsEmpty();
    });
}

bool ALBOneFactoryBodyWeldStarterLayoutAuthority::RestoreLayout(
    const FLBOneFactoryBodyWeldLayoutState& State, FString& OutReason)
{
    if (!ULBOneFactoryBodyWeldStarterLayoutLibrary::ValidateStarterLayout(
            State, OutReason))
    {
        return false;
    }
    CurrentState = State;
    OutReason = TEXT("BODY/WELD LAYOUT RESTORED AFTER COMPLETE PREFLIGHT");
    return true;
}

bool ALBOneFactoryBodyWeldStarterLayoutAuthority::AssignProgramme(
    const ELBOneFactoryBodyWeldProgramme InProgramme,
    const FName TargetStationId, FString& OutReason)
{
    if (HasActiveOrReservedWIP(CurrentState))
    {
        OutReason = TEXT(
            "BODY/WELD PROGRAMME ASSIGNMENT IS BLOCKED BY ACTIVE OR RESERVED WIP");
        return false;
    }
    FLBOneFactoryBodyWeldLayoutState Candidate = CurrentState;
    FLBOneFactoryBodyWeldStationState* Source = nullptr;
    FLBOneFactoryBodyWeldStationState* Target =
        LBOneFactoryBodyWeldStarterPrivate::FindStation(
            Candidate, TargetStationId);
    for (FLBOneFactoryBodyWeldStationState& Station : Candidate.Stations)
    {
        if (Station.AssignedProgrammes.Contains(InProgramme))
        {
            Source = &Station;
            break;
        }
    }
    const ELBOneFactoryBodyWeldRobotRole RequiredRobotRole =
        ULBOneFactoryBodyWeldStarterLayoutLibrary::
            GetRequiredRobotRole(InProgramme);
    if (!Source || !Target || Source == Target
        || !ULBOneFactoryBodyWeldStarterLayoutLibrary::
            StationSupportsProgramme(*Target, InProgramme)
        || (Target->LeftRobotRole != RequiredRobotRole
            && Target->RightRobotRole != RequiredRobotRole))
    {
        OutReason = TEXT(
            "BODY/WELD TARGET CANNOT ACCEPT THE REQUESTED PROGRAMME AND ROBOT DUTY");
        return false;
    }
    Source->AssignedProgrammes.RemoveSingle(InProgramme);
    Target->AssignedProgrammes.Add(InProgramme);
    Target->AssignedProgrammes.Sort([](
        const ELBOneFactoryBodyWeldProgramme Left,
        const ELBOneFactoryBodyWeldProgramme Right)
    {
        return static_cast<uint8>(Left) < static_cast<uint8>(Right);
    });
    Candidate.bCommissioned = false;
    ++Candidate.Revision;
    if (!ULBOneFactoryBodyWeldStarterLayoutLibrary::ValidateStarterLayout(
            Candidate, OutReason))
    {
        return false;
    }
    CurrentState = MoveTemp(Candidate);
    OutReason = TEXT(
        "BODY/WELD PROGRAMME REASSIGNED ATOMICALLY; RECOMMISSION REQUIRED");
    return true;
}

bool ALBOneFactoryBodyWeldStarterLayoutAuthority::AssignRobotPairRoles(
    const FName StationId,
    const ELBOneFactoryBodyWeldRobotRole InLeftRobotRole,
    const ELBOneFactoryBodyWeldRobotRole InRightRobotRole,
    FString& OutReason)
{
    if (HasActiveOrReservedWIP(CurrentState))
    {
        OutReason = TEXT(
            "BODY/WELD ROBOT ROLE ASSIGNMENT IS BLOCKED BY ACTIVE OR RESERVED WIP");
        return false;
    }
    FLBOneFactoryBodyWeldLayoutState Candidate = CurrentState;
    FLBOneFactoryBodyWeldStationState* Station =
        LBOneFactoryBodyWeldStarterPrivate::FindStation(Candidate, StationId);
    if (!Station
        || (Station->LeftRobotRole == InLeftRobotRole
            && Station->RightRobotRole == InRightRobotRole)
        || !ULBOneFactoryBodyWeldStarterLayoutLibrary::
            StationSupportsRobotRole(*Station, InLeftRobotRole)
        || !ULBOneFactoryBodyWeldStarterLayoutLibrary::
            StationSupportsRobotRole(*Station, InRightRobotRole))
    {
        OutReason = TEXT(
            "BODY/WELD ROBOT PAIR DUTIES ARE UNCHANGED OR INCOMPATIBLE");
        return false;
    }
    Station->LeftRobotRole = InLeftRobotRole;
    Station->RightRobotRole = InRightRobotRole;
    Candidate.bCommissioned = false;
    ++Candidate.Revision;
    if (!ULBOneFactoryBodyWeldStarterLayoutLibrary::ValidateStarterLayout(
            Candidate, OutReason))
    {
        return false;
    }
    CurrentState = MoveTemp(Candidate);
    OutReason = TEXT(
        "BODY/WELD MIRRORED ROBOT DUTIES REASSIGNED ATOMICALLY; RECOMMISSION REQUIRED");
    return true;
}

bool ALBOneFactoryBodyWeldStarterLayoutAuthority::MoveStation(
    const FName StationId, const FTransform& WorldTransform,
    FString& OutReason)
{
    if (HasActiveOrReservedWIP(CurrentState))
    {
        OutReason = TEXT(
            "BODY/WELD MOVEMENT IS BLOCKED BY ACTIVE OR RESERVED WIP");
        return false;
    }
    FLBOneFactoryBodyWeldLayoutState Candidate = CurrentState;
    FLBOneFactoryBodyWeldStationState* Station =
        LBOneFactoryBodyWeldStarterPrivate::FindStation(Candidate, StationId);
    if (!Station
        || !LBOneFactoryBodyWeldStarterPrivate::IsTransformUsable(
            WorldTransform)
        || Station->WorldTransform.Equals(WorldTransform,
            LBOneFactoryBodyWeldStarterPrivate::TransformTolerance))
    {
        OutReason = TEXT("BODY/WELD MOVE TARGET OR TRANSFORM IS INVALID");
        return false;
    }
    Station->WorldTransform = WorldTransform;
    Candidate.bCommissioned = false;
    ++Candidate.Revision;
    if (!ULBOneFactoryBodyWeldStarterLayoutLibrary::ValidateStarterLayout(
            Candidate, OutReason))
    {
        return false;
    }
    CurrentState = MoveTemp(Candidate);
    OutReason = TEXT(
        "BODY/WELD POSITION MOVED ATOMICALLY; RECOMMISSION REQUIRED");
    return true;
}

bool ALBOneFactoryBodyWeldStarterLayoutAuthority::Commission(
    FString& OutReason)
{
    if (CurrentState.bCommissioned)
    {
        OutReason = TEXT("BODY/WELD LINE IS ALREADY COMMISSIONED");
        return false;
    }
    if (HasActiveOrReservedWIP(CurrentState)
        || !ULBOneFactoryBodyWeldStarterLayoutLibrary::ValidateStarterLayout(
            CurrentState, OutReason))
    {
        if (HasActiveOrReservedWIP(CurrentState))
        {
            OutReason = TEXT(
                "BODY/WELD COMMISSION IS BLOCKED BY ACTIVE OR RESERVED WIP");
        }
        return false;
    }
    FLBOneFactoryBodyWeldLayoutState Candidate = CurrentState;
    Candidate.bCommissioned = true;
    ++Candidate.Revision;
    if (!ULBOneFactoryBodyWeldStarterLayoutLibrary::ValidateStarterLayout(
            Candidate, OutReason))
    {
        return false;
    }
    CurrentState = MoveTemp(Candidate);
    OutReason = TEXT(
        "CONFIGURABLE 18-POSITION BODY/WELD LINE COMMISSIONED");
    return true;
}
